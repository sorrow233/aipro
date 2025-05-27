import asyncio
from config import WORKFLOW_STAGES
from modules.api_client import APIClient, ResearchAPIClient
from utils.file_utils import append_text
from utils.resource_tracker import update_resource_usage

class Researcher:
    def __init__(self, output_dir: str, max_concurrency: int = 6):
        self.output_dir = output_dir
        self.api_client = APIClient()  # 主账号
        self.research_api_client = ResearchAPIClient()  # 研究专用账号
        self.max_concurrency = max_concurrency  # 增加到 6，因为现在有两个账号

    async def process_question(self, question: dict, index: int, main_topic: str, all_branches: list, use_research_client: bool = False):
        """深入探讨某个具体问题
        
        Args:
            question: 当前要探讨的问题
            index: 问题索引
            main_topic: 主要话题
            all_branches: 所有分支的列表
            use_research_client: 是否使用备用账号
        """
        client = self.research_api_client if use_research_client else self.api_client
        print(f"开始探讨第 {index + 1} 个方面: {question['标题']}")
        
        # 构建更友好的对话提示
        prompt = f"""让我们一起来聊聊"{main_topic}"这个有趣的话题！

这个问题有不同的角度：
{', '.join([b['标题'] for b in all_branches])}

现在，我想请你重点集中谈"{question['标题']}"这个方面。

在分享你的想法时，请：
1. 请形象生动的告诉我
2. 始终围绕"{main_topic}"这个话题
3. 只围绕当前的"{question['标题']}"这个方面，其他角度我会单独研究

记住，我们是作为对这个话题感兴趣的爱好者在交流，希望你能像给好朋友解释一样，让我能轻松理解并产生自己的思考。
"""

        answer = await client.call_model(
            model=WORKFLOW_STAGES['research'],
            messages=[{"role": "user", "content": prompt}],
            temp=0.8  # 稍微提高温度，让回答更自然
        )
        update_resource_usage(call_count=1, word_count=len(answer))
        log_entry = f"Topic {index + 1}: {question['标题']}\nThoughts: {answer}\n{'-' * 40}"
        append_text("researcher_history.txt", log_entry, output_dir=self.output_dir)
        print(f"完成第 {index + 1} 个方面的探讨")
        return answer

    async def parallel_research(self, questions: list, main_topic: str) -> list:
        """并行处理所有研究问题
        
        Args:
            questions: 问题列表
            main_topic: 主要研究主题
        """
        tasks = []
        for i, question in enumerate(questions):
            # 交替使用两个账号以提高并行效率
            use_research_client = i % 2 == 1
            task = self.process_question(
                question=question,
                index=i,
                main_topic=main_topic,
                all_branches=questions,
                use_research_client=use_research_client
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)