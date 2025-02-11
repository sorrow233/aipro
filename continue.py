import asyncio
from workflow import AutoQASystem

async def continue_from_step3():
    # 使用之前的会话目录
    session_folder = "output/日本可能遇到的困难_20250210_212431"  # 修改为实际目录
    system = AutoQASystem(output_dir=session_folder)
    
    # 从步骤3继续执行
    print("\n从步骤3继续：开始评估和优化...")
    result = await system.execute_workflow_from_step3()
    
    # 读取生成的markdown文件
    try:
        with open(f"{session_folder}/final_report.md", "r", encoding='utf-8') as f:
            print("\n最终报告已生成，请查看：", f"{session_folder}/final_report.md")
    except Exception as e:
        print("无法读取最终报告文件：", str(e))

if __name__ == "__main__":
    asyncio.run(continue_from_step3()) 