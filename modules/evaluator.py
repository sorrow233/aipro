import json
import re
from config import WORKFLOW_STAGES
from modules.api_client import APIClient
from utils.file_utils import append_text, write_text
from utils.resource_tracker import update_resource_usage

class Evaluator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.api_client = APIClient()

    def clean_ai_response(self, text: str) -> str:
        """清理AI返回的文本，移除think标签及其内容"""
        # 移除 <think> 标签及其内容
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        # 移除 <think>\n嗯 格式
        text = re.sub(r'<think>\s*\n\s*嗯', '', text)
        # 清理可能残留的空行
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        return text.strip()

    async def evaluate_and_optimize(self, content: str, title: str = "") -> dict:
        """
        评估文章质量并给出优化建议
        """
        eval_prompt = f"""请阅读下面的文章内容，并完成以下任务：
1. 给出1-10分的质量评分
2. 提供具体的优化建议
3. 如果发现任何事实性或逻辑性错误，请指出并更正

请严格按照下面格式返回JSON：
{{
    "标题": "文章标题",
    "评分": 0,
    "评分理由": "为什么给出这个分数",
    "优化建议": [
        "建议1",
        "建议2",
        ...
    ],
    "事实更正": [
        "更正1",
        "更正2",
        ...
    ]
}}

文章内容如下：
{content[:3000]}
"""
        print(f"\n开始评估文章: {title if title else '最终报告'}")
        
        result = await self.api_client.call_model(
            model=WORKFLOW_STAGES['scoring'],
            messages=[{"role": "user", "content": eval_prompt}],
            temp=0.4
        )
        update_resource_usage(call_count=1, word_count=len(result))

        # 清理AI返回的文本
        result = self.clean_ai_response(result)
        
        # 记录原始返回结果
        append_text("evaluator_history.txt", result, output_dir=self.output_dir)

        # 提取JSON
        match = re.search(r'(\{.*\})', result, re.DOTALL)
        if not match:
            print("无法提取JSON，返回文本：", result)
            raise ValueError("无法提取JSON结构")
        
        json_str = match.group(1).strip()
        try:
            evaluation = json.loads(json_str)
            print(f"评分完成: {evaluation['评分']}分")
            
            # 确保评估结果中的文本也经过清理
            if "评分理由" in evaluation:
                evaluation["评分理由"] = self.clean_ai_response(evaluation["评分理由"])
            if "优化建议" in evaluation:
                evaluation["优化建议"] = [self.clean_ai_response(suggestion) for suggestion in evaluation["优化建议"]]
            if "事实更正" in evaluation:
                evaluation["事实更正"] = [self.clean_ai_response(correction) for correction in evaluation["事实更正"]]
            
            return evaluation
        except json.JSONDecodeError as e:
            print(f"JSON解析错误，提取后的JSON文本：{json_str}")
            raise e