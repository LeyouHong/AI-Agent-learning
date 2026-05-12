from langchain_core.prompts import ChatPromptTemplate, ChatMessagePromptTemplate
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key = os.environ["OPENAI_API_KEY"],
    streaming=True
)

system_message_template = ChatMessagePromptTemplate.from_template(
    template = "你是一个{role}专家，擅长回答{domain}的问题",
    role="system",
)

human_message_template = ChatMessagePromptTemplate.from_template(
    template = "用户问题：{question}",
    role="user",
)

chat_prompt_template = ChatPromptTemplate.from_messages([
    system_message_template,
    human_message_template
])

class AddInputArgs(BaseModel):
    x: int = Field(description="The first number to add")
    y: int = Field(description="The second number to add")


# =========================
# 2. Tool 定义
# =========================
@tool(
    description="Add two numbers",
    args_schema=AddInputArgs,
    return_direct=False
)
def add(x: int, y: int) -> int:
    """Add two numbers"""
    return x + y

def create_calc_tools():
    return [add]

calc_tools = create_calc_tools()

FILE_DIR = "/Users/leyouhong/workspace/ai-projects/ai-agent-test/app/temp"

file_toolkit = FileManagementToolkit(root_dir=FILE_DIR)
file_tools = file_toolkit.get_tools()