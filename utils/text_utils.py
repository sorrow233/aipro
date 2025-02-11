import re

def extract_json(text: str) -> str:
    """
    从文本中提取出第一个 JSON 片段。
    优先通过 ```json ... ``` 标记提取，如果没有再尝试抓取从 { 到 } 的部分。
    """
    # 优先提取 markdown 格式里的 JSON
    pattern = r"```json\s*(\{[\s\S]*?\})\s*```"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    # 如果没有 markdown 包裹，则查找第一组 { ... } 文本
    pattern = r"(\{[\s\S]*\})"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return "" 