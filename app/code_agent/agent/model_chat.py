import uuid

from langchain_community.chat_message_histories import FileChatMessageHistory

from app.code_agent.model.chat_gpt_model import llm_gpt
from app.code_agent.prompt.multi_chat_prompt import multi_chat_prompt
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.agent_toolkits.file_management import FileManagementToolkit

from app.common import FILE_DIR

def get_session_history(session_id: str):
    return FileChatMessageHistory(f"{session_id}.json")

file_toolkit = FileManagementToolkit(root_dir=FILE_DIR)
file_tools = file_toolkit.get_tools()

chain = multi_chat_prompt | llm_gpt | StrOutputParser()

chain_with_history = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_session_history,
    input_messages_key="question",
    history_messages_key="chat_history"
)

chat_session_id = uuid.uuid4()

while True:
    user_input = input("User: ")
    if user_input.lower() == "exit" or user_input.lower() == "quit":
        break
    response = chain_with_history.stream(
        {"question": user_input},
        config={"configurable": {"session_id": chat_session_id}},
    )

    for chunk in response:
        print(chunk, end="")
        
    print("\n")