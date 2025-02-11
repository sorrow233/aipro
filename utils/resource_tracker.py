import json
import os

SUMMARY_FILE = "api_usage_summary.json"
SUMMARY_DOC = "api_usage_summary.txt"

def get_resource_summary():
    if os.path.exists(SUMMARY_FILE):
        try:
            with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {"api_calls": 0, "total_words": 0}
    else:
        data = {"api_calls": 0, "total_words": 0}
    return data

def update_resource_usage(call_count: int = 1, word_count: int = 0):
    data = get_resource_summary()
    data["api_calls"] += call_count
    data["total_words"] += word_count
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_resource_summary_text() -> str:
    data = get_resource_summary()
    return f"AI调用次数: {data['api_calls']} 次\nAI返回字数: {data['total_words']} 字"

def write_summary_doc():
    summary_text = get_resource_summary_text()
    with open(SUMMARY_DOC, "w", encoding="utf-8") as f:
        f.write(summary_text) 