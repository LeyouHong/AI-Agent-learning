import asyncio
import sys
import time
from pathlib import Path

# Allow running this file directly: python app/code_agent/agent/code_agent.py
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

from langchain.messages import AIMessage, ToolMessage

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig

from app.code_agent.tools.rag_tools import get_stdio_rag_tools
from app.code_agent.tools.file_saver import FileSaver
from app.code_agent.model.chat_gpt_model import llm_gpt
from app.code_agent.tools.file_tools import file_toolskit
from app.code_agent.tools.terminal_tools import get_stdio_terminal_tools
from app.code_agent.tools.browser_tools import get_stdio_browser_tools
from app.code_agent.tools.vm_tools import get_stdio_vm_tools
from app.code_agent.tools.mysql_tools import get_stdio_mysql_tools
from app.code_agent.prompt.system_prompt import build_system_prompt

from langsmith import traceable

load_dotenv()

def format_debug_output(step_name: str, content: str, is_tool_call = False) -> None:
    if is_tool_call:
        print(f"🔄 [Tool Call: {step_name}]")
        print ("-" * 40)
        print(content.strip())
        print ("-" * 40)
    else:
        print(f"💭 [{step_name}]")
        print ("-" * 40)
        print(content.strip())
        print ("-" * 40)

@traceable(name="Code Agent")
async def run_agent():
    saver = FileSaver()

    terminal_tools = await get_stdio_terminal_tools()
    rag_tools = await get_stdio_rag_tools()
    browser_tools = await get_stdio_browser_tools()
    vm_tools = await get_stdio_vm_tools()
    mysql_tools = await get_stdio_mysql_tools()
    tools = file_toolskit + terminal_tools + rag_tools + browser_tools + vm_tools + mysql_tools

    config = RunnableConfig(configurable={"thread_id": 5}, recursion_limit=100)

    agent = create_agent(
        model=llm_gpt, 
        tools=tools, 
        checkpointer=saver,
        system_prompt=build_system_prompt(),)
    

    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit" or user_input.lower() == "quit":
            break

        print("\n🤖 AI is thinking...\n")
        print("=" * 60)

        iteration_count = 0
        start_time = time.time()
        last_tool_time = start_time


        # Read data from RAG, and add it to the prompt

        async for chunk in agent.astream(input={"messages": [
            ("user", user_input), ("system", """
Before the tasks, use query_rag to get knowledge from database, base on knowledge to do the tasks.
            """)
        ]}, config=config):
            iteration_count += 1

            print(f"\n📊 This is {iteration_count} step: ")
            print("-" * 30)
            
            items = chunk.items()
            for node_name, node_output in items:
                if "messages" in node_output:
                    for msg in node_output["messages"]:
                        if isinstance(msg, AIMessage):
                            if msg.content:
                                format_debug_output("AI thinking", msg.content)
                            else:
                                for tool in msg.tool_calls:
                                    format_debug_output(f"Tool Call", f"{tool['name']}: {tool['args']}")
                        elif isinstance(msg, ToolMessage):
                            tool_name = getattr(msg, "name", "Unknown Tool")
                            tool_content = msg.content

                            current_time = time.time()
                            tool_duration = current_time - last_tool_time
                            last_tool_time = current_time

                            tool_result = f"""
                            🔧 Tool: {tool_name}
🤖 Result: {tool_content}
✅ Status: Completed, start next task
🕒 Duration: {tool_duration:.2f} seconds
"""

                            format_debug_output(f"Tool Output", tool_result, is_tool_call=True)
                        else:
                            format_debug_output("Not Implemented", f"Not implemented {chunk}.")

        print()
    
asyncio.run(run_agent())