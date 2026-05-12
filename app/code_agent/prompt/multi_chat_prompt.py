from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

multi_chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a good developer, who is good at frontend and backend coding."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])