import asyncio

from langchain_core.messages import convert_to_messages
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent
from langgraph_supervisor import create_supervisor
from app.code_agent.model.chat_gpt_model import llm_gpt
from app.code_agent.tools.file_tools import file_toolskit

from app.code_agent.tools.shell_tools import get_stdio_shell_tools
from app.code_agent.tools.terminal_tools import get_stdio_terminal_tools


def pretty_print_messages(update, last_message=False):
    # for node_name, node_update in update.items():
    #     update_label = f"Update from node {node_name}:"
    #     print(update_label)

    # messages = convert_to_messages(node_update['messages'])
    messages = convert_to_messages(update['messages'])
    if last_message:
        messages = messages[-1:]

    for message in messages:
        pretty_message = message.pretty_repr(html=True)
        print(pretty_message)

    print("\n\n")


async def run_agent():
    memory = MemorySaver()

    shell_tools = await get_stdio_shell_tools()

    research_agent = create_agent(
        model=llm_gpt,
        tools=shell_tools + file_toolskit,
        name="research_expert",
        system_prompt="你是一个技术主管，负责设计技术方案，请不要直接写代码，请指导 code_agent 进行工作",
    )

    code_agent = create_agent(
        model=llm_gpt,
        tools=shell_tools + file_toolskit,
        name="code_expert",
        system_prompt="你是一个编程专家，请根据 research_expert 设计的技术方案来实现代码或进行代码文件相关的操作",
    )

    supervisor_agent = create_supervisor(
        agents=[research_agent, code_agent],
        model=llm_gpt,
        system_prompt=(
            "You are a team supervisor managing a research expert and a code expert."
            "For task planning and task researching, use research_agent."
            "For code problems, use code_agent."
        )
    )

    app = supervisor_agent.compile(checkpointer=memory)

    while True:
        user_input = input("用户：")

        if user_input.lower() == "exit":
            break

        config = RunnableConfig(configurable={"thread_id": 1}, recursion_limit=100)

        # async for chunk in app.astream(input={"messages": user_input}, config=config):
        #     pretty_print_messages(chunk, last_message=True)

        result = await app.ainvoke(input={"messages": user_input}, config=config)
        pretty_print_messages(result)

asyncio.run(run_agent())