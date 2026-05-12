from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from app.common import llm
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

import asyncio
import sys

async def create_mcp_stdio_client():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["/Users/leyouhong/workspace/ai-projects/ai-agent-test/app/mcp/stdio/mcp_stdio_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)

            agent = create_react_agent(llm, tools)

            question = "100+100*100 = ?"

            # MCP tool 只支持 ainvoke：
            resp = await agent.ainvoke({
                "messages": [
                    HumanMessage(content=question)
                ]
            })

            print(resp["messages"][-1].content)

asyncio.run(create_mcp_stdio_client())