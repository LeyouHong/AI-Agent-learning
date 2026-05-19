import hashlib
import os
import requests
from alibabacloud_bailian20231229 import client as bailian_20231229_client
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from dotenv import load_dotenv

load_dotenv()

def _calculate_md5(file_path: str) -> str:
    """
    计算文件的 MD5 哈希值。

    参数:
        file_path (str): 文件路径。

    返回:
        str: 文件的 MD5 哈希值。
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def _get_file_info(file_path):
    """
    获取指定文件的名称、MD5哈希值和大小。

    参数:
        file_path (str): 文件的完整路径。

    返回:
        tuple: (file_name, file_md5, file_size)
    """

    # 获取文件名
    file_name = os.path.basename(file_path)

    # 获取文件大小（字节）
    file_size = os.path.getsize(file_path)

    # 计算MD5哈希值
    file_md5 = _calculate_md5(file_path)

    return file_name, file_md5, file_size

def _apply_lease_by_file_path(client, category_id, workspace_id, file_path):
    file_name, file_md5, file_size = _get_file_info(file_path)
    return _apply_lease(client, category_id, file_name, file_md5, file_size, workspace_id)

def _upload_file_to_bailian(upload_url, headers, file_path):
    """
    将文件上传到阿里云百炼服务。

    参数:
        lease_id (str): 租约 ID。
        upload_url (str): 上传 URL。
        headers (dict): 上传请求的头部。
        file_path (str): 文件路径。
    """
    with open(file_path, 'rb') as f:
        file_content = f.read()
    upload_headers = {
        "X-bailian-extra": headers["X-bailian-extra"],
        "Content-Type": headers["Content-Type"]
    }
    response = requests.put(upload_url, data=file_content, headers=upload_headers)
    response.raise_for_status()

def _add_file_to_bailian_category(client, lease_id: str, parser: str, category_id: str, workspace_id: str):
    """
    将文件添加到阿里云百炼指定类目。

    参数:
        client: 阿里云百炼客户端。
        lease_id (str): 租约 ID。
        parser (str): 用于文件的解析器。
        category_id (str): 类别 ID。
        workspace_id (str): 业务空间 ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    request = bailian_20231229_models.AddFileRequest(
        lease_id=lease_id,
        parser=parser,
        category_id=category_id,
    )
    runtime = util_models.RuntimeOptions()
    return client.add_file_with_options(workspace_id, request, headers, runtime)

def _apply_lease(client, category_id, file_name, file_md5, file_size, workspace_id):
    """
    从阿里云百炼服务申请文件上传租约。

    参数:
        client (bailian20231229Client): 阿里云百炼客户端。
        category_id (str): 类别 ID。
        file_name (str): 文件名称。
        file_md5 (str): 文件的 MD5 哈希值。
        file_size (int): 文件大小（以字节为单位）。
        workspace_id (str): 业务空间 ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    request = bailian_20231229_models.ApplyFileUploadLeaseRequest(
        file_name=file_name,
        md_5=file_md5,
        size_in_bytes=file_size,
    )
    runtime = util_models.RuntimeOptions()
    return client.apply_file_upload_lease_with_options(category_id, workspace_id, request, headers, runtime)

def _describe_file(client, workspace_id, file_id):
    """
    获取文档的基本信息。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        file_id (str): 文档ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    runtime = util_models.RuntimeOptions()
    return client.describe_file_with_options(workspace_id, file_id, headers, runtime)

def _create_client() -> bailian_20231229_client.Client:
    config = open_api_models.Config(
        access_key_id=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID"),
        access_key_secret=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
    )
    config.endpoint = 'bailian.cn-beijing.aliyuncs.com'
    return bailian_20231229_client.Client(config=config)

def _create_index(client, workspace_id, file_id, name, structure_type, source_type, sink_type):
    """
    在阿里云百炼服务中创建知识库（初始化）。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        file_id (str): 文档ID。
        name (str): 知识库名称。
        structure_type (str): 知识库的数据类型。
        source_type (str): 应用数据的数据类型，支持类目类型和文档类型。
        sink_type (str): 知识库的向量存储类型。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    request = bailian_20231229_models.CreateIndexRequest(
        structure_type=structure_type,
        name=name,
        source_type=source_type,
        sink_type=sink_type,
        document_ids=[file_id]
    )
    runtime = util_models.RuntimeOptions()
    return client.create_index_with_options(workspace_id, request, headers, runtime)

def _submit_index(client, workspace_id, index_id):
    """
    向阿里云百炼服务提交索引任务。

    参数:
        client (bailian20231229Client): 阿里云百炼客户端。
        workspace_id (str): 业务空间 ID。
        index_id (str): 索引 ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    submit_index_job_request = bailian_20231229_models.SubmitIndexJobRequest(
        index_id=index_id
    )
    runtime = util_models.RuntimeOptions()
    return client.submit_index_job_with_options(workspace_id, submit_index_job_request, headers, runtime)

def get_index_job_status(client, workspace_id, index_id, job_id):
    """
    查询索引任务状态。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。
        job_id (str): 任务ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    get_index_job_status_request = bailian_20231229_models.GetIndexJobStatusRequest(
        index_id=index_id,
        job_id=job_id
    )
    runtime = util_models.RuntimeOptions()
    return client.get_index_job_status_with_options(workspace_id, get_index_job_status_request, headers, runtime)

def _list_indices(client, workspace_id):
    """
    获取指定业务空间下一个或多个知识库的详细信息。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    list_indices_request = bailian_20231229_models.ListIndicesRequest()
    runtime = util_models.RuntimeOptions()
    return client.list_indices_with_options(workspace_id, list_indices_request, headers, runtime)

def _submit_index_add_documents_job(client, workspace_id, index_id, file_id, source_type="DATA_CENTER_FILE"):
    """
    向一个非结构化知识库追加导入已解析的文档。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。
        file_id (str): 文档ID。
        source_type(str): 数据类型。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    submit_index_add_documents_job_request = bailian_20231229_models.SubmitIndexAddDocumentsJobRequest(
        index_id=index_id,
        document_ids=[file_id],
        source_type=source_type
    )
    runtime = util_models.RuntimeOptions()
    return client.submit_index_add_documents_job_with_options(workspace_id, submit_index_add_documents_job_request, headers, runtime)

def _delete_index_document(client, workspace_id, index_id, file_id):
    """
    从指定的非结构化知识库中永久删除一个或多个文档。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。
        file_id (str): 文档ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    delete_index_document_request = bailian_20231229_models.DeleteIndexDocumentRequest(
        index_id=index_id,
        document_ids=[file_id]
    )
    runtime = util_models.RuntimeOptions()
    return client.delete_index_document_with_options(workspace_id, delete_index_document_request, headers, runtime)

def _delete_index(client, workspace_id, index_id):
    """
    永久性删除指定的知识库。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    delete_index_request = bailian_20231229_models.DeleteIndexRequest(
        index_id=index_id
    )
    runtime = util_models.RuntimeOptions()
    return client.delete_index_with_options(workspace_id, delete_index_request, headers, runtime)

def upload_rag_file_to_bailian(client, workspace_id, category_id, file_path):
    """
    upload file to bailian datacenter and add to specific category.

    params:
        client
        workspace_id
        category_id
        file_path

    return:
        file upload status
    """
    # apply lease
    print("=" * 100)
    lease = _apply_lease_by_file_path(client, category_id, workspace_id, file_path)
    headers = lease.body.data.param.headers
    lease_id = lease.body.data.file_upload_lease_id
    upload_url = lease.body.data.param.url
    print("-" * 60)
    print("file lease applied successfully")
    print("-" * 60)

    # upload file to bailian datacenter
    _upload_file_to_bailian(upload_url, headers, file_path)
    print("-" * 60)
    print("file uploaded successfully")
    print("-" * 60)

    # add file to bailian category
    add_file_response = _add_file_to_bailian_category(client, lease_id, "DASHSCOPE_DOCMIND", category_id, workspace_id)
    file_id = add_file_response.body.data.file_id
    print("-" * 60)
    print("file added to category successfully")
    print("-" * 60)

    # get file upload status
    describe_file_response = _describe_file(client, workspace_id, file_id)
    print("-" * 60)
    print("file upload status: ", describe_file_response.body.data.status)
    print("-" * 60)

    return file_id

def add_document_to_index(client, workspace_id, index_id, file_id):
    job_response = _submit_index_add_documents_job(client, workspace_id, index_id, file_id)
    job_id = job_response.body.data.id

    job_status = get_index_job_status(client, workspace_id, index_id, job_id)

    return job_status.body.data

# if __name__ == "__main__":
#     bailian_client = _create_client()
#     workspace_id = os.environ.get("ALIBABA_CLOUD_WORKSPACE_ID")
#     category_id = str("cate_09abba3ae98f42daaad626c8ec25ed41_16382109")
    
#     upload_rag_file_to_bailian(bailian_client, workspace_id, category_id, "/Users/leyouhong/workspace/ai-projects/ai-agent-test/app/code_agent/rag/upload_test_rag.txt")