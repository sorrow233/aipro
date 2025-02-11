询问一个问题，AI自动分解为多个方面，并行处理，生成最终的综合报告


## 特点

- 智能话题分解：从多个角度分析话题，确保全面理解
- 并行处理：同时处理多个子话题，提高效率
- 资源追踪：记录 API 使用情况
- 自动保存：所有对话历史自动保存

## 安装要求

```bash
pip install -r requirements.txt
```


## 配置

1. 在 `config.py` 中配置你的 API 密钥，要删除config.example.py的.example：
```python
API_BASE_URL = "你的API基础URL"
API_KEY = "你的API密钥"
```

2. 可选：配置第二个 API 账号以提高并行效率：
```python
RESEARCH_API_BASE_URL = "第二个API基础URL"
RESEARCH_API_KEY = "第二个API密钥"
```

3. 模型配置
在 `config.py` 中可以配置不同阶段使用的模型：
```python
WORKFLOW_STAGES = {
    'decomposition': "deepseek-ai/deepseek-r1",  # 话题分解阶段
    'research': "deepseek-ai/deepseek-r1",       # 内容探讨阶段
    'verification': "deepseek-ai/deepseek-r1",   # 验证阶段
    'scoring': "deepseek-ai/deepseek-r1"         # 评分阶段
}
```


## 使用方法

1. 启动新对话：
```python
python main.py
```

2. 输入你感兴趣的话题，例如：
```
请输入你想了解的话题：详细的为我介绍虚拟货币
你目前对这个话题的了解程度：只知道狗狗币是meme币，比特币被称为现代黄金，但不知道为什么
你想达到的学习目标：能够在买入前知晓买的是什么，以及什么影响他们的涨跌
```

3. 系统会自动：
   - 分解话题为多个子方面
   - 并行处理每个方面
   - 生成最终的综合报告

4. 输出文件：
   - `output/[时间戳]/final_report.md`：最终报告
   - `output/[时间戳]/分解结构.json`：话题分解结构
   - `output/[时间戳]/*.txt`：详细处理日志

最终结果展示：https://sorrow233.notion.site/197c238567d3809abd1eca3d5eeb98ac

## 目录结构

```
.
├── main.py              # 主程序入口
├── config.py            # 配置文件
├── modules/             # 核心模块
│   ├── decomposer.py   # 话题分解器
│   ├── researcher.py   # 内容探索器
│   ├── evaluator.py    # 质量评估器
│   └── api_client.py   # API 客户端
├── utils/              # 工具函数
│   ├── file_utils.py   # 文件操作
│   └── resource_tracker.py  # 资源追踪
└── output/             # 输出目录
```


## 高级功能

1. 继续之前的会话（从分支研究完成之后继续）：
```python
python continue.py
```

2. 追踪 API 使用情况：
```
查看 API_usage_summary.txt 获取累计使用统计
```

3. 自定义分支：
可在话题分解时添加自定义关注点


## 注意事项

- 确保 API 密钥配置正确，config.example.py只是示例，要删除.example
- 建议定期备份 output 目录


## 常见问题

Q: 如何修改并行处理的数量？
A: 在 config.py 中调整 MAX_CONCURRENT_TASKS 参数
