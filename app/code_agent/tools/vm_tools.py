from pathlib import Path
from app.code_agent.utils.mcp import create_mcp_stdio_client


async def get_stdio_vm_tools():
    current_dir = Path(__file__).resolve().parent

    project_root = current_dir.parents[2]

    script_path = project_root / "app/code_agent/mcp/vm.py"

    params = {
        "command": "python",
        "args": [str(script_path)]
    }

    client, tools = await create_mcp_stdio_client("vm_tools", params)

    return tools