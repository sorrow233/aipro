import asyncio
import datetime
import re
import json
from modules.decomposer import Decomposer
from modules.researcher import Researcher
from modules.synthesizer import Synthesizer
from modules.evaluator import Evaluator
from utils.file_utils import write_json, write_text
from config import OUTPUT_DIR, WORKFLOW_STAGES
from utils.resource_tracker import write_summary_doc

class AutoQASystem:
    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = output_dir
        self.decomposer = Decomposer(output_dir)
        self.researcher = Researcher(output_dir)
        self.synthesizer = Synthesizer(output_dir)
        self.evaluator = Evaluator(output_dir)

    def clean_think_tags(self, text: str) -> str:
        """清理think标签及其内容，包括处理嵌套标签的情况"""
        # 使用循环来处理嵌套的标签，直到没有更多匹配
        while True:
            # 保存处理前的文本
            old_text = text
            # 匹配最内层的 <think>...</think> 对
            text = re.sub(r'<think>([^<>]*?)</think>', '', text, flags=re.DOTALL)
            # 如果文本没有变化，说明没有找到更多匹配，退出循环
            if text == old_text:
                break
        
        # 清理多余的空行，但保留段落格式
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        return text.strip()

    async def execute_workflow(self, question: str, cognitive: str, goal: str, custom_branch: str = "") -> dict:
        """执行完整的工作流程"""
        print(f"步骤1：问题分解中...")
        decomposition = await self.decomposer.decompose_question(question, cognitive, goal, custom_branch)
        print(f"步骤1完成：问题分解结果已保存至 {self.output_dir}/分解结构.json")

        print("\n步骤2：并行研究子问题中...")
        sub_answers = await self.researcher.parallel_research(
            questions=decomposition["子问题"],
            main_topic=question  # 传入主要研究主题
        )
        print("步骤2完成：并行研究结果已全部返回.")

        print("\n步骤3：开始评估和优化...")
        # 将研究结果整合成一个完整的报告
        report_content = ""
        for q, a in zip(decomposition["子问题"], sub_answers):
            report_content += f"## {q['标题']}\n\n{a}\n\n"

        # 使用新的评估和优化方法
        evaluation = await self.evaluator.evaluate_and_optimize(report_content)
        
        # 在生成最终markdown之前，清理所有内容中的think标签
        report_content = self.clean_think_tags(report_content)
        if evaluation.get('评分理由'):
            evaluation['评分理由'] = self.clean_think_tags(evaluation['评分理由'])
        if evaluation.get('优化建议'):
            evaluation['优化建议'] = [self.clean_think_tags(suggestion) for suggestion in evaluation['优化建议']]
        if evaluation.get('事实更正'):
            evaluation['事实更正'] = [self.clean_think_tags(correction) for correction in evaluation['事实更正']]

        # 生成最终的markdown文件
        final_md_content = f"""# {evaluation['标题']}

{report_content}

## 质量评估

- 评分：{evaluation['评分']}/10
- 评分理由：{evaluation['评分理由']}

## 优化建议

{''.join([f'- {suggestion}\n' for suggestion in evaluation['优化建议']])}

## 事实更正

{''.join([f'- {correction}\n' for correction in evaluation['事实更正']])}
"""

        write_text("final_report.md", final_md_content, output_dir=self.output_dir)
        print(f"\n最终报告已保存至: {self.output_dir}/final_report.md")

        return {
            "报告内容": report_content,
            "质量评估": evaluation
        }

    async def execute_workflow_from_step3(self):
        """从步骤3继续执行工作流"""
        print("步骤3：开始整合研究结果并生成报告...")

        # 读取分解结构获取标题
        with open(f"{self.output_dir}/分解结构.json", "r", encoding="utf-8") as f:
            decomposition = json.load(f)

        # 读取之前的研究结果（从 researcher_history.txt 提取答案）
        sub_answers = []
        with open(f"{self.output_dir}/researcher_history.txt", "r", encoding="utf-8") as f:
            content = f.read()
            # 这里正则表达式提取每个答案中的内容
            answers = re.findall(r"Answer: (.*?)-{40}", content, re.DOTALL)
            sub_answers = [answer.strip() for answer in answers]

        # 对应分解后的子问题标题
        titles = [q["标题"] for q in decomposition["子问题"]]

        # 这里不再调用事实核查，因为我们已把核查功能合并到 evaluator 中
        # 将各分支研究结果统一包装成合成报告需要的格式
        final_report = await self.synthesizer.synthesize_report({
            "子问题": titles,
            "研究结果": [{"修正内容": ans} for ans in sub_answers]
        })

        print("步骤4：评估报告质量并给出优化建议...")
        evaluation = await self.evaluator.evaluate_and_optimize(final_report)

        # 在生成最终markdown之前，清理所有内容中的think标签
        final_report = self.clean_think_tags(final_report)
        if evaluation.get('评分理由'):
            evaluation['评分理由'] = self.clean_think_tags(evaluation['评分理由'])
        if evaluation.get('优化建议'):
            evaluation['优化建议'] = [self.clean_think_tags(suggestion) for suggestion in evaluation['优化建议']]
        if evaluation.get('事实更正'):
            evaluation['事实更正'] = [self.clean_think_tags(correction) for correction in evaluation['事实更正']]

        # 生成最终的 markdown 文件
        final_md_content = f"""# {evaluation['标题']}

{final_report}

## 质量评估

- 评分：{evaluation['评分']}/10  
- 评分理由：{evaluation['评分理由']}

## 优化建议

{''.join([f'- {suggestion}\n' for suggestion in evaluation['优化建议']])}

## 事实更正

{''.join([f'- {correction}\n' for correction in evaluation['事实更正']])}
"""
        write_text("final_report.md", final_md_content, output_dir=self.output_dir)
        print(f"最终报告已保存至: {self.output_dir}/final_report.md")

        return {"报告内容": final_report, "质量评估": evaluation}

if __name__ == "__main__":
    import asyncio
    output_path = "output/会话目录示例"  # 请修改为实际的输出目录
    system = AutoQASystem(output_path)
    asyncio.run(system.execute_workflow_from_step3())