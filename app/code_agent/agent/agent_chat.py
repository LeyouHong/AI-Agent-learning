from app.code_agent.model.chat_gpt_model import llm_gpt
from app.code_agent.tools.file_tools import file_toolskit
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.prebuilt import create_react_agent

def create_agent():
    config = RunnableConfig(configurable={"thread_id": 1})

    MONGO_URI = "mongodb://admin:password@localhost:27017/admin"
    MONGO_DB = "chat"

    with MongoDBSaver.from_conn_string(MONGO_URI, MONGO_DB) as memory:
        agent = create_react_agent(
            model=llm_gpt, 
            tools=file_toolskit, 
            checkpointer=memory,
        )

        res = agent.invoke(input={"messages": [
            ("user", "Hi, I'm Leo.")
        ]}, config=config)

        print(res["messages"][-1].content)

        memory.close()


if __name__ == "__main__":
    create_agent()