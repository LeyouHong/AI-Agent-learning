from langchain_community.agent_toolkits.file_management import FileManagementToolkit

from app.common import ROOT_DIR

file_toolskit = FileManagementToolkit(root_dir=ROOT_DIR).get_tools()