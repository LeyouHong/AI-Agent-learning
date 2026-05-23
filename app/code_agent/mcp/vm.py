import os
import shlex
import subprocess
import tempfile
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP()


def run_limavm_shell_command(command):
    try:
        wrapper_command = "limactl shell lima-test " + command
        shell_command = shlex.split(wrapper_command)

        res = subprocess.run(shell_command, shell=False, capture_output=True, text=True)

        if res.returncode != 0:
            return res.stderr
        return res.stdout

    except Exception as e:
        return str(e)


def run_limavm_command(command):
    try:
        wrapper_command = "limactl " + command
        shell_command = shlex.split(wrapper_command)

        print("shell_command", shell_command)

        res = subprocess.run(shell_command, shell=False, capture_output=True, text=True)

        if res.returncode != 0:
            return res.stderr
        return res.stdout

    except Exception as e:
        return str(e)


@mcp.tool(
    name="make_dir_in_vm",
    description="Create a directory in the VM (equivalent to mkdir -p)."
)
def make_dir_in_vm(
    dir_path: Annotated[
        str,
        Field(description="Directory path to create")
    ]
):
    """Create a directory inside the virtual machine."""
    print("dir_path", dir_path)
    return run_limavm_shell_command("mkdir -p " + dir_path)


@mcp.tool(
    name="list_files_in_vm",
    description="List files in a VM directory (equivalent to ls -al)."
)
def list_files_in_vm(
    dir_path: Annotated[
        str,
        Field(description="Directory path to list")
    ]
):
    """List files in a VM directory."""
    print("dir_path", dir_path)
    return run_limavm_shell_command("ls -al " + dir_path)


@mcp.tool(
    name="write_file_to_vm",
    description="Write a file into the VM."
)
def write_file_to_vm(
    file_path: Annotated[
        str,
        Field(description="Target file path in VM")
    ],
    content: Annotated[
        str,
        Field(description="File content to write")
    ]
):
    """Write content to a file in the VM."""
    with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    print("Temp file created:", tmp_file_path)

    run_limavm_command(f"copy {tmp_file_path} lima-test:{file_path}")
    change_file_permission_in_vm(file_path, "755")


def change_file_permission_in_vm(file_path, mode):
    return run_limavm_shell_command(f"chmod {mode} {file_path}")


@mcp.tool(
    name="upload_directory_to_vm",
    description="Upload a local directory to the VM."
)
def upload_directory_to_vm(
    local_dir: Annotated[
        str,
        Field(description="Local directory path")
    ],
    vm_dest_dir: Annotated[
        str,
        Field(description="Destination directory in VM")
    ],
):
    """Upload a local directory into the VM."""

    if not os.path.exists(local_dir):
        msg = f"Local directory does not exist: {local_dir}"
        print(f"[UPLOAD] {msg}")
        return msg

    if not os.path.isdir(local_dir):
        msg = f"Path is not a directory: {local_dir}"
        print(f"[UPLOAD] {msg}")
        return msg

    make_dir_in_vm(vm_dest_dir)

    for root, dirs, files in os.walk(local_dir):
        if 'node_modules' in dirs:
            dirs.remove('node_modules')

        if '.git' in dirs:
            dirs.remove('.git')

        print(root, dirs, files)

        rel_path = os.path.relpath(root, local_dir)
        vm_subdir = os.path.join(vm_dest_dir, rel_path)

        make_dir_in_vm(vm_subdir)

        for file_name in files:
            local_file_path = os.path.join(root, file_name)
            vm_file_path = os.path.join(vm_subdir, file_name)

            result = run_limavm_command(
                f"copy {local_file_path} lima-test:{vm_file_path}"
            )
            print(result)

    return f"Directory [{local_dir}] uploaded to lima-test:[{vm_dest_dir}] successfully"


if __name__ == "__main__":
    mcp.run(transport="stdio")

    # Example test
    # make_dir_in_vm("/home/user/test")