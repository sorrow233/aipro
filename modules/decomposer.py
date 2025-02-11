import json
import re
from config import WORKFLOW_STAGES
from modules.api_client import APIClient
from utils.file_utils import append_text
from utils.text_utils import extract_json
from utils.resource_tracker import update_resource_usage

def fix_invalid_json(json_str: str) -> str:
    """
    尝试修正 JSON 字符串中字段值缺少引号的问题。
    例如：将 "理由": 需平衡算法精度与医患信任建立机制 转换为 "理由": "需平衡算法精度与医患信任建立机制"
    """
    # 此处仅针对 "理由" 字段做处理，可以按需扩展其他字段
    pattern = re.compile(r'("理由":\s*)([^\s"][^,\}\]]*)([,\}\]])', re.UNICODE)
    def replacer(match):
        fixed_value = match.group(2).strip()
        return f'{match.group(1)}"{fixed_value}"{match.group(3)}'
    return pattern.sub(replacer, json_str)

class Decomposer:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.api_client = APIClient()

    async def decompose_question(self, question: str, cognitive: str, goal: str, custom_branch: str = "") -> dict:
        """
        根据用户信息生成文章分支（子问题）。
        
        输出固定的 JSON 格式，示例如下：
        {
          "子问题": [
            {"标题": "分支1", "理由": "理由1"},
            {"标题": "分支2", "理由": "理由2"}
          ]
        }
        
        说明：
          - AI 可自主决定输出多少个分支，但数量不应超过 15 个；
          - 分支需要按照从最简单开始逐步深入到更复杂的顺序排列；
          - 每个分支必须附带一个简短的理由，解释为什么选择该分支；
          - 输出格式必须严格为 JSON 数据，不允许附加任何其它内容。
        """
        decomposition_prompt = f"""请依据以下信息生成文章分支，每个分支代表一个独立的讨论角度或方向。要求：
1. 从最简单的角度开始，然后逐步深入到更复杂的方向；
2. 每个分支必须附带一个简短的理由，解释为什么选择该分支；
3. 输出格式必须严格遵守如下 JSON 格式，不要附加任何其他文字：
{{
  "子问题": [
    {{"标题": "分支1", "理由": "理由1"}},
    {{"标题": "分支2", "理由": "理由2"}}
  ]
}}
注意：你可以自主决定输出多少个分支，但数量不得超过 10 个。
用户当前知识水平：{cognitive}
用户目标：{goal}
自定义额外分支：{custom_branch if custom_branch else "无"}
原始问题：{question}
"""
        result = await self.api_client.call_model(
            model=WORKFLOW_STAGES['decomposition'],
            messages=[{"role": "user", "content": decomposition_prompt}],
            temp=0.9
        )
        # 累加统计：本次调用1次，返回字数按结果长度计算
        update_resource_usage(call_count=1, word_count=len(result))
        
        prefix = "<think>\n嗯"
        if result.startswith(prefix):
            result = result[len(prefix):].strip()
        
        # 将日志写入当前会话的目录
        append_text("decomposer_history.txt", result, output_dir=self.output_dir)
        
        json_str = extract_json(result)
        if not json_str:
            print("无法提取JSON，返回原始结果：", result)
            raise ValueError("无法提取JSON结构，请检查提示词设计。")
        
        # 新增清洗逻辑：确保提取的JSON字符串以 { 开始、} 结束
        match = re.search(r'(\{.*\})', json_str, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
        else:
            print("正则匹配未找到有效 JSON，从返回文本：", json_str)
            raise ValueError("提取JSON失败，请检查返回格式。")
        
        # 这里尝试修正类似缺少引号的格式问题
        json_str = fix_invalid_json(json_str)
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print("JSON解析错误，提取后的JSON文本：", json_str)
            raise e