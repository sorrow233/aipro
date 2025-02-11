import json
from pathlib import Path
from config import OUTPUT_DIR  # 关键词: 配置导入, 输出目录
import os

def write_json(filename: str, data, output_dir: str = OUTPUT_DIR) -> None:
    # 关键词: 文件I/O, JSON写入, 数据持久化
    path = Path(output_dir)
    path.mkdir(exist_ok=True, parents=True)
    with open(path / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)  # 关键词: 序列化输出, 美化格式

def write_text(filename: str, text: str, output_dir: str = OUTPUT_DIR) -> None:
    # 关键词: 文件I/O, 文本写入, 数据持久化
    path = Path(output_dir)
    path.mkdir(exist_ok=True, parents=True)
    with open(path / filename, "w", encoding="utf-8") as f:
        f.write(text)  # 关键词: 写入文本, 文件保存

def append_text(filename: str, content: str, output_dir: str = "."):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(content + "\n")