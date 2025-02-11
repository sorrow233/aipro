import asyncio
from modules.api_client import APIClient
from config import WORKFLOW_STAGES

async def test_api_connectivity():
    print("发送 '你好' 到 API，等待回复...")

    # 使用 APIClient 调用，内部会自动加入系统指令要求回复以 "<think>\n嗯" 开头
    api_client = APIClient()
    result = await api_client.call_model(
        model=WORKFLOW_STAGES['research'],
        messages=[{"role": "user", "content": "你好"}],
        temp=0.6,
        max_tokens=4096
    )
    
    print("收到回复：")
    print(result)
    
    # 检查回复是否以 "<think>\n嗯" 开始
    if result.startswith("<think>\n嗯"):
        print("验证通过：回复以 '<think>\\n嗯' 开始")
    else:
        print("警告：回复没有按照要求开始，请检查系统指令是否生效")

if __name__ == "__main__":
    asyncio.run(test_api_connectivity()) 