import asyncio
import json
import re
from typing import List, Dict, Any
from config import WORKFLOW_STAGES
from modules.api_client import APIClient
from utils.file_utils import append_text
from utils.text_utils import extract_json
from utils.resource_tracker import update_resource_usage

# 尝试修复 JSON 字符串中字段值缺少引号的问题的函数可以保留，以备最终输出时使用
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

    async def _call_ai_for_json_list(self, prompt: str, attempt_msg: str) -> List[str]:
        """调用AI并期望返回一个JSON字符串列表"""
        print(attempt_msg)
        result = await self.api_client.call_model(
            model=WORKFLOW_STAGES['decomposition'], # 可以考虑为不同阶段设置不同模型或参数
            messages=[{"role": "user", "content": prompt}],
            temp=0.7 # 对于生成和选择阶段，可以适当调整温度
        )
        update_resource_usage(call_count=1, word_count=len(result))
        append_text("decomposer_history.txt", f"--- Attempt: {attempt_msg} ---\n{result}\n--- End Attempt ---", output_dir=self.output_dir)

        # 尝试提取JSON数组
        # AI可能返回 ```json ... ``` 或直接返回 [...]
        json_str_match = re.search(r'```json\s*(\[.*?\])\s*```', result, re.DOTALL)
        if not json_str_match:
            json_str_match = re.search(r'(\[.*?\])', result, re.DOTALL)

        if json_str_match:
            json_str = json_str_match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print(f"警告：AI返回的JSON列表解析失败，尝试作为纯文本处理。内容: {json_str}")
                # 如果解析失败，尝试基于换行符分割，并去除空行和多余引号
                # 这是一个简化的回退逻辑，可能需要根据实际AI输出调整
                return [line.strip().strip('"').strip("'") for line in json_str.split('\n') if line.strip()]
        else:
            # 如果无法提取JSON数组，则按行分割返回的文本作为最后的尝试
            print(f"警告：AI未返回预期的JSON列表格式。尝试按行解析。内容: {result}")
            return [line.strip() for line in result.split('\n') if line.strip()]

    async def _generate_initial_titles(self, question: str, cognitive: str, goal: str, generator_id: int) -> List[str]:
        """第一阶段：单个AI生成约20个标题"""
        prompt = f"""作为问题分解的第 {generator_id+1} 号AI助手，请针对以下信息，生成大约20个相关的、有启发性的问题分支或子主题标题。
这些标题应尽可能多样化，并覆盖不同方面。请确保标题简洁明了。

原始问题："{question}"
用户当前知识水平："{cognitive}"
用户目标："{goal}"

请严格以JSON字符串列表的格式返回，例如：
["标题1", "标题2", "标题3", ...]
不要包含任何其他解释性文字或标记。
"""
        return await self._call_ai_for_json_list(prompt, f"生成初始标题 (生成器 {generator_id+1})")

    async def _score_and_select_titles(self, titles_to_score: List[str], question: str, cognitive: str, goal: str, scorer_id: int) -> List[str]:
        """第二阶段：单个AI从给定列表中评分并选出10个标题"""
        titles_str = "\n".join([f"- \"{t}\"" for t in titles_to_score])
        prompt = f"""作为问题分解的第 {scorer_id+1} 号AI评分员，请从以下候选标题列表中，选出最多10个与主要问题、用户知识和目标最相关、最有价值且不重复的标题。
请仔细评估每个标题的质量和相关性。

原始问题："{question}"
用户当前知识水平："{cognitive}"
用户目标："{goal}"

候选标题列表：
{titles_str}

请严格以JSON字符串列表的格式返回你选出的10个标题，例如：
["选中的标题A", "选中的标题B", ...]
不要包含任何其他解释性文字或标记。
"""
        return await self._call_ai_for_json_list(prompt, f"评分和选择标题 (评分器 {scorer_id+1})")

    async def _finalize_selection_and_add_reasons(self, final_candidate_titles: List[str], question: str, cognitive: str, goal: str, custom_branch: str) -> Dict[str, List[Dict[str, str]]]:
        """第三阶段：最后一个AI从30个标题中提取最多10个，并添加理由，形成最终JSON"""
        titles_str = "\n".join([f"- \"{t}\"" for t in final_candidate_titles])
        custom_branch_info = f'请额外考虑并优先纳入这个自定义分支（如果它尚未在列表中且有意义）："{custom_branch}"' if custom_branch else "没有自定义分支。"

        prompt = f"""作为问题分解的最终决策AI，请从以下大约30个精选候选标题中，选出最终的、不超过10个子问题。
这些子问题应能全面且有逻辑地覆盖原始问题，并考虑用户的知识水平和学习目标。
请确保选出的子问题是从最简单或最基础的开始，逐步深入到更复杂的方面。
为每个选定的子问题提供一个简短的理由，解释为什么选择该分支。
{custom_branch_info}

原始问题："{question}"
用户当前知识水平："{cognitive}"
用户目标："{goal}"

候选标题列表（请从中选择）：
{titles_str}

请严格按照以下JSON格式返回结果，不要附加任何其他文字：
{{
  "子问题": [
    {{"标题": "最终选择的标题1", "理由": "选择此标题的理由1..."}},
    {{"标题": "最终选择的标题2", "理由": "选择此标题的理由2..."}}
  ]
}}
"""
        print("进行最终选择并添加理由")
        result_str = await self.api_client.call_model(
            model=WORKFLOW_STAGES['decomposition'], # 可以考虑为最终阶段设置不同模型或参数
            messages=[{"role": "user", "content": prompt}],
            temp=0.5 # 最终阶段温度可以低一些，确保输出稳定
        )
        update_resource_usage(call_count=1, word_count=len(result_str))
        append_text("decomposer_history.txt", f"--- Attempt: Final Selection and Reasons ---\n{result_str}\n--- End Attempt ---", output_dir=self.output_dir)

        # 提取最终的JSON对象
        json_output_str = extract_json(result_str)
        if not json_output_str:
            print("错误：最终选择AI未能返回有效的JSON结构。原始返回：", result_str)
            # 尝试构建一个空的有效结构，避免整个流程崩溃
            return {"子问题": []}

        # 尝试修正类似缺少引号的格式问题
        json_output_str = fix_invalid_json(json_output_str)

        # 新增：尝试修正 "理由" 字段值末尾多余的引号，例如 "理由": "some reason""}
        # 正则表达式匹配一个标准的JSON字符串值 ("(?:\\.|[^"\\])*")，后面跟一个多余的引号(")，然后是逗号或结束括号([,\}\s])
        json_output_str = re.sub(r'("理由":\s*"(?:\\.|[^"\\])*")(")([,\}\s])', r'\1\3', json_output_str)

        try:
            final_decomposition = json.loads(json_output_str)
            if "子问题" not in final_decomposition or not isinstance(final_decomposition["子问题"], list):
                print(f"错误：最终JSON结构不符合预期（缺少'子问题'列表）。内容: {json_output_str}")
                return {"子问题": []}
            return final_decomposition
        except json.JSONDecodeError as e:
            print(f"错误：最终JSON解析失败。修复尝试后的JSON文本：{json_output_str}。错误：{e}")
            return {"子问题": []} # 返回一个空的有效结构

    async def decompose_question(self, question: str, cognitive: str, goal: str, custom_branch: str = "") -> dict:
        """
        根据用户信息生成文章分支（子问题），采用多阶段AI协作机制。
        阶段1: 3个AI分别生成约20个标题。
        阶段2: 3个AI分别从上述生成的标题中挑选10个。
        阶段3: 1个AI从阶段2选出的30个标题中最终选择不超过10个，并添加理由。
        """
        print("开始多阶段问题分解...")

        # 阶段1: 并行生成初始标题
        print("\n阶段1：生成初始候选标题...")
        generation_tasks = [
            self._generate_initial_titles(question, cognitive, goal, i) for i in range(3)
        ]
        results_stage1 = await asyncio.gather(*generation_tasks)
        
        all_initial_titles = []
        for title_list in results_stage1:
            if isinstance(title_list, list):
                all_initial_titles.extend(title_list)
            else:
                print(f"警告：生成器返回了非列表类型: {type(title_list)}")
        
        # 去重，保持一定的顺序性（基于首次出现）
        seen_titles = set()
        unique_initial_titles = []
        for title in all_initial_titles:
            if isinstance(title, str) and title.strip() and title not in seen_titles:
                unique_initial_titles.append(title)
                seen_titles.add(title)
        
        if not unique_initial_titles:
            print("错误：阶段1未能生成任何有效标题。返回空分解。")
            return {"子问题": []}
        print(f"阶段1完成：共生成 {len(unique_initial_titles)} 个不重复的初始标题。")
        append_text("decomposer_history.txt", f"--- 阶段1 不重复初始标题 ---\n{json.dumps(unique_initial_titles, ensure_ascii=False, indent=2)}\n--- End ---", output_dir=self.output_dir)


        # 阶段2: 并行评分和选择标题
        # 将标题大致均分给3个评分AI
        print("\n阶段2：评分和筛选候选标题...")
        num_scorers = 3
        chunk_size = (len(unique_initial_titles) + num_scorers - 1) // num_scorers # 确保能分完
        
        scoring_tasks = []
        for i in range(num_scorers):
            start_index = i * chunk_size
            end_index = min((i + 1) * chunk_size, len(unique_initial_titles))
            if start_index < end_index: # 确保块内有内容
                titles_chunk = unique_initial_titles[start_index:end_index]
                scoring_tasks.append(
                    self._score_and_select_titles(titles_chunk, question, cognitive, goal, i)
                )
        
        results_stage2 = await asyncio.gather(*scoring_tasks)
        
        all_selected_titles_stage2 = []
        for title_list in results_stage2:
            if isinstance(title_list, list):
                all_selected_titles_stage2.extend(title_list)
            else:
                print(f"警告：评分器返回了非列表类型: {type(title_list)}")

        seen_titles_stage2 = set()
        unique_selected_titles_stage2 = []
        for title in all_selected_titles_stage2:
             if isinstance(title, str) and title.strip() and title not in seen_titles_stage2:
                unique_selected_titles_stage2.append(title)
                seen_titles_stage2.add(title)

        if not unique_selected_titles_stage2:
            print("错误：阶段2未能筛选出任何有效标题。将尝试使用阶段1的全部标题进行最终选择。")
            # 如果阶段2没有选出任何标题，作为回退，直接用阶段1的全部不重复标题给最终选择AI
            # 但这可能会超出最终选择AI的处理能力或提示长度限制，需要注意
            if not unique_initial_titles: # 再次检查，如果连初始标题都没有，就真没办法了
                 print("错误：阶段1和阶段2均无有效标题。返回空分解。")
                 return {"子问题": []}
            unique_selected_titles_stage2 = unique_initial_titles[:100] # 限制数量，避免过长
            print(f"警告：阶段2无输出，回退到使用阶段1的前{len(unique_selected_titles_stage2)}个标题进行最终选择。")

        print(f"阶段2完成：共选出 {len(unique_selected_titles_stage2)} 个不重复的候选标题。")
        append_text("decomposer_history.txt", f"--- 阶段2 不重复候选标题 ---\n{json.dumps(unique_selected_titles_stage2, ensure_ascii=False, indent=2)}\n--- End ---", output_dir=self.output_dir)

        # 阶段3: 最终选择并添加理由
        print("\n阶段3：最终选择并添加理由...")
        final_decomposition_result = await self._finalize_selection_and_add_reasons(
            unique_selected_titles_stage2, question, cognitive, goal, custom_branch
        )
        
        print("问题分解流程完成。")
        # 将最终结果写入 decomposer_history.txt 和 分解结构.json
        # 这个写入分解结构.json的逻辑可以移到 workflow.py 中，或者在这里也保留一份详细日志
        append_text("decomposer_final_structure.json.log", json.dumps(final_decomposition_result, ensure_ascii=False, indent=2), output_dir=self.output_dir)

        return final_decomposition_result

if __name__ == "__main__":
    # 这是一个用于本地测试 decomposer.py 的示例
    async def main_test():
        output_path = "output/decomposer_test_session"
        # 确保测试输出目录存在
        import os
        os.makedirs(output_path, exist_ok=True)

        decomposer_instance = Decomposer(output_path)
        test_question = "详细解释一下什么是人工智能以及它的未来发展趋势。"
        test_cognitive = "我对人工智能有一些基本了解，比如知道机器学习、深度学习等名词，但具体原理和应用不太清楚。"
        test_goal = "希望能够系统地了解人工智能的核心概念、主要技术、当前应用以及未来可能对社会产生的影响。"
        test_custom_branch = "人工智能伦理问题" # 可选

        print(f"测试问题: {test_question}")
        print(f"测试自定义分支: {test_custom_branch if test_custom_branch else '无'}")

        decomposition = await decomposer_instance.decompose_question(
            test_question, 
            test_cognitive, 
            test_goal, 
            test_custom_branch
        )
        
        print("\n最终分解结果:")
        print(json.dumps(decomposition, ensure_ascii=False, indent=2))

    asyncio.run(main_test())