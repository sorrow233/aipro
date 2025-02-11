import asyncio
import datetime
import re
from workflow import AutoQASystem

async def main():
    question = input("想讨论什么问题呢：")
    cognitive = input("当前对这问题有着什么样的认识：")
    goal = input("通过阅读你想达到什么样的目的：")
    custom_option = input("是否需要自定义分支让AI进行额外研究？(y/n):")
    custom_branch = ""
    if custom_option.strip().lower() in ["y", "yes"]:
        custom_branch = input("请输入自定义分支：")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = re.sub(r"\W+", "_", question).strip("_")
    session_folder = f"output/{safe_title}_{timestamp}"
    print("历史记录将存储在：", session_folder)
    
    system = AutoQASystem(output_dir=session_folder)
    result = await system.execute_workflow(question, cognitive, goal, custom_branch)
    
    print("\n最终报告：\n", result.get("报告内容", ""))
    print("\n质量评估：\n", result.get("质量评估", ""))

if __name__ == "__main__":
    asyncio.run(main())