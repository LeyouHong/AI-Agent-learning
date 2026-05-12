from langchain_ollama.chat_models import ChatOllama


if __name__ == "__main__":
    llm = chat = ChatOllama(model='gemma3:270m')
    messages = [
        ('system', '你是一个奴才，每次对话你要自称奴才，对我要叫陛下。'),
        ("human", "你是谁?"),
    ]
    response = llm.invoke(messages)
    print(response)