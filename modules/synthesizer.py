import json
from utils.file_utils import append_text

class Synthesizer:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        # 不再需要API客户端，直接进行文本拼接即可
        pass

    async def synthesize_report(self, components: dict) -> str:
        """
        根据组件中的内容生成最终报告。
        
        组件格式：
            {
                "子问题": ["分支标题1", "分支标题2", ...],
                "研究结果": [{"修正内容": "分支1内容"}, {"修正内容": "分支2内容"}, ...]
            }
        """
        branch_titles = components.get("子问题", [])
        branch_contents = [item["修正内容"] for item in components.get("研究结果", [])]
        
        if len(branch_titles) != len(branch_contents):
            raise ValueError(f"子问题标题与研究结果数量不匹配！标题数：{len(branch_titles)}，内容数：{len(branch_contents)}")
        
        # 拼接所有分支内容
        final_lines = []
        for title, content in zip(branch_titles, branch_contents):
            final_lines.append(f"# {title}")  # 大标题
            final_lines.append("")            # 空行
            final_lines.append(content)       # 分支研究结果内容
            final_lines.append("")            # 分隔空行
        
        final_report = "\n".join(final_lines)
        
        # 写入日志
        append_text("synthesizer_history.txt", final_report, output_dir=self.output_dir)
        return final_report