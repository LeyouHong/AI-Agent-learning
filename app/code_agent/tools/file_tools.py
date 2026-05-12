from langchain_community.agent_toolkits.file_management import FileManagementToolkit

from app.common import FILE_DIR

file_toolskit = FileManagementToolkit(root_dir=FILE_DIR).get_tools()