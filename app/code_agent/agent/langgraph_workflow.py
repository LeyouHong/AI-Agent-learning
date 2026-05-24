import os

from langchain.messages import AIMessage
from langgraph.graph import END, START, StateGraph, MessagesState
from langchain_core.prompt_values import StringPromptValue
from app.code_agent.model.chat_gpt_model import llm_gpt
from app.code_agent.mcp.browser_tools import search_in_duckduckgo

def output_graph_image(graph, filename):
    try:
        png_data = graph.get_graph().draw_mermaid_png()
        output_file_dir = os.path.dirname(__file__)
        output_file_path = os.path.join(output_file_dir, filename + '.png')

        with open(output_file_path, 'wb') as f:
            f.write(png_data)
            print(f"write file successfully: {output_file_path}")
    except Exception as e:
        return str(e)

class SearchMessagesState(MessagesState):
    search_question: str
    search_keyword: str
    search_results: str

key_extract_query_keyword = "key_extract_query_keyword"
key_search_web = "key_search_web"
key_reply_user = "key_reply_user"


def node_extract_query_keyword(state: SearchMessagesState):
    last_message = state['messages'][-1]
    question = last_message.content
    state['search_question'] = question
    print(question)
    prompt = StringPromptValue(text=f"find keyword in question and return result directly: {question}")
    print(prompt)
    message = llm_gpt.invoke(input=prompt)
    state['messages'].append(message)
    state['search_keyword'] = message.content
    return state


def node_search_web(state: SearchMessagesState):
    keyword = state['search_keyword']

    search_result = search_in_duckduckgo(keyword, 1)

    summary = llm_gpt.invoke(input=f"""
You are a data compression system.

Extract only the useful information for answering questions.

# Raw Search Result
{search_result}

Return a short structured summary.
""")

    state['search_results'] = summary.content

    state['messages'].append(AIMessage(content=summary.content))

    return state


def node_reply_user(state: SearchMessagesState):

    result = llm_gpt.invoke(input=f"""
You are a helpful assistant.

Answer the question based only on the search summary.
Use 1-2 sentences to answer the question.

# Question
{state['search_question']}

# Summary
{state['search_results']}
""")

    state['messages'].append(result)

    return state

state_graph = StateGraph(SearchMessagesState)
state_graph.add_node(key_extract_query_keyword, node_extract_query_keyword)
state_graph.add_node(key_search_web, node_search_web)
state_graph.add_node(key_reply_user, node_reply_user)


state_graph.add_edge(START, key_extract_query_keyword)
state_graph.add_edge(key_extract_query_keyword, key_search_web)
state_graph.add_edge(key_search_web, key_reply_user)
state_graph.add_edge(key_reply_user, END)

compiled_graph = state_graph.compile()
# output_graph_image(compiled_graph, "graph")

results = compiled_graph.stream({
    "messages": [
        ("user", "How is the weather today in San Francisco?")
    ]
})

print(results)

for s in results:
    print(s)
    key = list(s)[0]
    print(s[key]["messages"][-1].content)
    print("-"*60)