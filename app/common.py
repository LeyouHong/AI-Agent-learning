from langchain_community.agent_toolkits import FileManagementToolkit
from dotenv import load_dotenv

load_dotenv()

# =========================
# 2. Tool 定义
# =========================

ROOT_DIR = "/Users/leyouhong/workspace/ai-projects/ai-agent-test"

file_toolkit = FileManagementToolkit()
file_tools = file_toolkit.get_tools()