# 关键词: 配置, API设置, 输出目录, 工作流阶段

# 主账号配置
API_BASE_URL = "https://integrate.api.nvidia.com/v1"  # 关键词: 基础URL, API端点
API_KEY = "your_api_key_here"  # 关键词: API密钥, 安全认证

# 第二个账号配置（用于并行研究）
RESEARCH_API_BASE_URL = "https://integrate.api.nvidia.com/v1"  # 替换为第二个账号的 URL
RESEARCH_API_KEY = "your_research_api_key_here"  # 替换为第二个账号的 API KEY

# 更新所有模型为 deepseek-ai/deepseek-r1
WORKFLOW_STAGES = {
    'decomposition': "deepseek-ai/deepseek-r1",  # 使用 deepseek-ai/deepseek-r1
    'research': "deepseek-ai/deepseek-r1",       # 使用 deepseek-ai/deepseek-r1
    'verification': "deepseek-ai/deepseek-r1",     # 使用 deepseek-ai/deepseek-r1
    'scoring': "deepseek-ai/deepseek-r1"           # 使用 deepseek-ai/deepseek-r1
}
OUTPUT_DIR = "./output"  # 关键词: 文件输出, 目录路径