from langchain_mcp_adapters.client import MultiServerMCPClient
from app.common import llm
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
import asyncio

async def create_mcp_sse_client():
    client = MultiServerMCPClient({
        "math-tools": {
            "url": "http://localhost:8000/mcp",
            "transport": "streamable_http",
        }
    })

    tools = await client.get_tools()

    agent = create_react_agent(llm, tools)

    question = "100+100*100 = ?"

    # MCP tool 只支持 ainvoke：
    resp = await agent.ainvoke({
        "messages": [
            HumanMessage(content=question)
        ]
    })

    print(resp["messages"][-1].content)

asyncio.run(create_mcp_sse_client())