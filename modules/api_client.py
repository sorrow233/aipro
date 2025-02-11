import asyncio
from openai import AsyncOpenAI  # 关键词: OpenAI, 异步API, SDK
from config import API_BASE_URL, API_KEY, RESEARCH_API_BASE_URL, RESEARCH_API_KEY  # 关键词: 配置导入, API设置

class APIClient:
    total_api_calls = 0  # 类变量用于记录整个过程中的API调用次数
    # 设置全局并发限制：所有API调用全局最多同时进行3个请求
    global_semaphore = asyncio.Semaphore(3)
    
    def __init__(self, base_url=API_BASE_URL, api_key=API_KEY):
        # 关键词: 初始化, API客户端设置, 配置读取
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key
        )
    
    async def call_model(self, model: str, messages: list, temp: float = 0.7, max_tokens: int = 4096) -> str:
        """封装模型调用，包含重试机制
           在首个消息中添加指令，要求模型在回答前加入思考流程
           关键词: API调用, 重试逻辑, 异步方法, 聊天完成, 系统指令
        """
        # 添加系统消息，要求模型输出必须以 "<think>\n嗯" 开始
        system_message = {
            "role": "system",
            "content": "Initiate your response with \"<think>\\n嗯\" at the beginning of every output."
        }
        # 将系统消息放在消息列表最前面
        messages_with_instruction = [system_message] + messages

        max_retries = 3  # 关键词: 最大重试次数, 计数器
        for attempt in range(max_retries):
            try:
                async with APIClient.global_semaphore:
                    # 每次实际调用API时，计数器加1，并输出调用信息
                    APIClient.total_api_calls += 1
                    print(f"[API调用] 第 {APIClient.total_api_calls} 次调用. 模型: {model}, 尝试次数: {attempt + 1}")
                    
                    # 关键词: 模型请求, 响应解析, 实现chat完成逻辑
                    response = await self.client.chat.completions.create(
                        model=model,
                        messages=messages_with_instruction,
                        temperature=temp,
                        top_p=0.8,       # 关键词: top_p, 采样参数
                        max_tokens=max_tokens
                    )
                    # 关键词: 成功返回, 解析响应内容
                    return response.choices[0].message.content
            except Exception as e:
                # 关键词: 异常处理, 错误, 指数退避
                if attempt == max_retries - 1:
                    raise  # 关键词: 最终失败, 程序终止
                await asyncio.sleep(2**attempt)  # 关键词: 重试延时, 指数增长
        return ""  # 关键词: 默认返回, 空字符串

class ResearchAPIClient(APIClient):
    """专门用于研究阶段的 API 客户端，在初始化时使用研究专用的 API 配置"""
    def __init__(self):
        super().__init__(RESEARCH_API_BASE_URL, RESEARCH_API_KEY)