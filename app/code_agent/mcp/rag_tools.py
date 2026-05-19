import os
from typing import Annotated

from alibabacloud_bailian20231229 import client as bailian_20231229_client
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from dotenv import load_dotenv
from langsmith import traceable
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from app.code_agent.rag.rag import add_document_to_index, get_index_job_status, upload_rag_file_to_bailian

load_dotenv()

mcp = FastMCP()


def create_client() -> bailian_20231229_client.Client:
    config = open_api_models.Config(
        access_key_id=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID"),
        access_key_secret=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
    )
    config.endpoint = 'bailian.cn-beijing.aliyuncs.com'
    return bailian_20231229_client.Client(config=config)


def retrieve_index(client, workspace_id: str, index_id: str, query: str):
    headers = {}
    retrieve_request = bailian_20231229_models.RetrieveRequest(
        index_id=index_id,
        query=query,
    )
    runtime = util_models.RuntimeOptions()
    return client.retrieve_with_options(
        workspace_id, retrieve_request, headers, runtime
    )


def format_nodes(rag) -> str:
    body = getattr(rag, "body", None)
    data = getattr(body, "data", None) if body else None
    nodes = getattr(data, "nodes", None) if data else None
    nodes = nodes or []

    if not nodes:
        return "No results found."

    sections: list[str] = []
    for index, node in enumerate(nodes, start=1):
        text = getattr(node, "text", None) or ""
        sections.append(f"{index} section: knowledge\n{text}\n--")
    return "\n".join(sections)


@traceable(run_type="tool", name="Query RAG")
@mcp.tool(name="query_rag", description="Query knowledge from bailian")
def query_rag_from_bailian(
    query: Annotated[
        str,
        Field(
            description="query content",
            json_schema_extra={"example": "Terminal Operation Instruction"},
        ),
    ],
) -> str:
        workspace_id = os.environ.get("ALIBABA_CLOUD_WORKSPACE_ID")
        index_id = os.environ.get("ALIBABA_CLOUD_INDEX_ID")

        bailian_client = create_client()
        rag = retrieve_index(bailian_client, workspace_id, index_id, query)
        return format_nodes(rag)


@traceable(run_type="tool", name="Upload Local File to Bailian RAG")
@mcp.tool(name="upload_local_file_to_rag", description="Upload local knowledge files to bailian")
def upload_rag_to_bailian(file_path: Annotated[str, 
    Field(description="local knowledge file path, need absolute path", 
          json_schema_extra={"example": "/Users/leyouhong/workspace/ai-projects/ai-agent-test/app/code_agent/rag/upload_test_rag.txt"})]):
    
    client = create_client()
    workspace_id = os.environ.get("ALIBABA_CLOUD_WORKSPACE_ID")
    category_id = os.environ.get("ALIBABA_CLOUD_CATEGORY_ID")
    file_id = upload_rag_file_to_bailian(client, workspace_id, category_id, file_path)
    index_id = os.environ.get("ALIBABA_CLOUD_INDEX_ID")
    
    return add_document_to_index(client, workspace_id, index_id, file_id)

@traceable(run_type="tool", name="Query RAG Job Status")
@mcp.tool(name="query_rag_job_status", description="Query the processing status of knowledge uploaded to the Bailian Knowledge Base.")
def query_bailian_rag_job_status(job_id: str):
     bailian_client = create_client()
     workspace_id = os.environ.get("ALIBABA_CLOUD_WORKSPACE_ID")
     index_id = os.environ.get("ALIBABA_CLOUD_INDEX_ID")

     job_status = get_index_job_status(bailian_client, workspace_id, index_id, job_id)

     return job_status.body.data

if __name__ == "__main__":
    mcp.run(transport="stdio")