from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from app.common import llm
# from langgraph.prebuilt import create_react_agent
from langchain.agents import create_agent

import asyncio

# 获取 MCP Tools

async def create_mcp_playwright_client():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@executeautomation/playwright-mcp-server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)

            agent =agent = create_agent(
                model=llm,
                tools=tools
            )

            question = question = """
                Open https://duckduckgo.com
                Search hamster
                Return top 3 results
            """

            # MCP tool 只支持 ainvoke：
            resp = await agent.ainvoke(input={
                "messages": [
                    ("user", question)
                ]
            })

            for m in resp["messages"]:
                print("====")
                print(type(m).__name__)
                print(m)

asyncio.run(create_mcp_playwright_client())