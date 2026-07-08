"""
合同管理业务逻辑
包含：Pydantic 模型、辅助函数、所有合同 CRUD / 看板 / 文件处理函数
原代码来源：routers/contracts.py
"""
import json
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import quote
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from bson import ObjectId
from minio.error import S3Error

from database import (
    contract_collection, settings_collection,
    write_log, resolve_display_name, now_china,
    minio_client, MINIO_BUCKET,
)
from services.shared import get_guest_data_limit

# ═══════════════════════════════════════════════════════════════
#  Pydantic 数据模型
class ContractData(BaseModel):
    contractId: Optional[str] = None
    name: str
    contractNo: str
    category: Optional[str] = None
    amount: Optional[float] = 0.0
    status: Optional[str] = "草稿"
    customer: Optional[str] = None
    customerType: Optional[str] = None
    contractType: Optional[str] = None
    signingCompany: Optional[str] = None  # 新增：签署公司字段
    contactPerson: Optional[str] = None
    contactPhone: Optional[str] = None
    signDate: Optional[str] = None
    servicePeriod: Optional[str] = None
    remark: Optional[str] = None
    creator: Optional[str] = "admin"
    operator: Optional[str] = "admin"
    fileUrl: Optional[str] = None
    fileName: Optional[str] = None
    filePath: Optional[str] = None
    isDeleted: bool = False


# ═══════════════════════════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════════════════════════

def serialize_doc(doc):
    """将 MongoDB 文档转为 JSON 友好格式"""
    if not doc: return None
    doc["_id"] = str(doc["_id"])
    return doc


def build_query_filter(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    contractType: Optional[str] = None,
    customerType: Optional[str] = None,
    status: Optional[str] = None,
    minAmount: Optional[float] = None,
    maxAmount: Optional[float] = None,
) -> dict:
    """
    构建 MongoDB 查询条件（合同列表和看板数据共用，避免重复代码）
    原封不动保持原筛选逻辑
    """
    query_filter = {"isDeleted": False}

    if keyword:
        query_filter["$or"] = [
            {"name": {"$regex": keyword, "$options": "i"}},
            {"contractId": {"$regex": keyword, "$options": "i"}},
            {"contractNo": {"$regex": keyword, "$options": "i"}},
            {"customer": {"$regex": keyword, "$options": "i"}},
        ]
    if category:
        query_filter["category"] = category
    if contractType:
        query_filter["contractType"] = contractType
    if customerType:
        query_filter["customerType"] = customerType
    if status:
        query_filter["status"] = status
    if minAmount is not None or maxAmount is not None:
        amount_filter = {}
        if minAmount is not None:
            amount_filter["$gte"] = minAmount
        if maxAmount is not None:
            amount_filter["$lte"] = maxAmount
        query_filter["amount"] = amount_filter

    return query_filter


# ═══════════════════════════════════════════════════════════════
#  业务逻辑函数（对应各 API 端点，原封不动提取）
# ═══════════════════════════════════════════════════════════════

# --- 1. 获取合同数量统计数据（看板用）---
async def get_dashboard_stats(
    role: Optional[str] = None,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    contractType: Optional[str] = None,
    customerType: Optional[str] = None,
    status: Optional[str] = None,
    minAmount: Optional[float] = None,
    maxAmount: Optional[float] = None,
):
    try:
        # 1. 组装与列表完全一致的筛选条件，保证大看板数据和当前筛选框同步
        query_filter = build_query_filter(
            keyword=keyword, category=category, contractType=contractType,
            customerType=customerType, status=status,
            minAmount=minAmount, maxAmount=maxAmount,
        )

        # 2. 统计当前筛选条件下的：符合要求的合同总数量、总金额、已归档数量
        # 管理员看真实总数，访客默认写死限制（保持你原本的访客逻辑）
        if role == "admin":
            total_count = await contract_collection.count_documents(query_filter)

            # 利用 MongoDB 聚合直接算出：销售总额
            pipeline_amount = [{"$match": query_filter}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
            amount_res = await contract_collection.aggregate(pipeline_amount).to_list(length=1)
            total_amount = amount_res[0]["total"] / 10000 if amount_res else 0

            # 算已归档数量
            archived_filter = {**query_filter, "status": "已签署"}
            archived_count = await contract_collection.count_documents(archived_filter)
        else:
            # 访客模式：从系统设置读取 guest_data_limit，实时联动
            guest_limit = await get_guest_data_limit()
            # 仅统计前 guest_limit 条
            guest_cursor = contract_collection.find(query_filter).limit(guest_limit)
            guest_docs = await guest_cursor.to_list(length=guest_limit)
            total_count = len(guest_docs)
            total_amount = sum(doc.get("amount", 0) for doc in guest_docs) / 10000
            archived_count = sum(1 for doc in guest_docs if doc.get("status") == "已签署")

        # 3. 🧠 降维打击核心：让 MongoDB 直接在底层按产品类别分组（Group）计数
        pipeline_category = [
            {"$match": query_filter},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        category_cursor = contract_collection.aggregate(pipeline_category)
        category_rows = await category_cursor.to_list(length=100)

        # 将聚合出来的结果转化为前端 Chart.js 最喜欢的扁平化字典：{"计算机设备": 3, "办公用品": 2}
        category_stats_map = {row["_id"]: row["count"] for row in category_rows if row["_id"]}

        # 4. 只返回高精、轻量级的统计账本
        return {
            "totalCount": total_count,
            "totalAmount": total_amount,
            "archivedCount": archived_count,
            "categoryStats": category_stats_map
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"看板数据渲染失败: {str(e)}")


# --- 2. 获取合同列表（支持分页和筛选）---
async def get_contracts(
    role: Optional[str] = None,
    page: int = 1,
    size: int = 100,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    contractType: Optional[str] = None,
    customerType: Optional[str] = None,
    status: Optional[str] = None,
    minAmount: Optional[float] = None,
    maxAmount: Optional[float] = None,
):
    # 统一的基础查询：只查询未删除的合同
    query_filter = build_query_filter(
        keyword=keyword, category=category, contractType=contractType,
        customerType=customerType, status=status,
        minAmount=minAmount, maxAmount=maxAmount,
    )

    # 【权限控制分支 1】：如果是 admin 管理员
    if role == "admin":
        # 1. 动态计算当前页需要跳过多少条
        skip_count = (page - 1) * size

        # 2. 去数据库计算符合条件的总合同数（比如 7 条、100 条、1 万条）
        total_count = await contract_collection.count_documents(query_filter)

        # 3. 核心限流：利用 skip 和 limit，让 MongoDB 每次最多只交出 size 条数据（默认10条）
        cursor = contract_collection.find(query_filter).sort("createTime", -1).skip(skip_count).limit(size)
        contracts = await cursor.to_list(length=size)

        data = [serialize_doc(c) for c in contracts]

        # 4. 完美打包：把当前页需要的这几条，连同总条数一起丢给前端
        return {
            "list": data,
            "total": total_count
        }

    # 【权限控制分支 2】：如果不是 admin（如访客 guest）
    else:
        # 从系统设置读取 guest_data_limit，实现实时联动
        guest_limit = await get_guest_data_limit()
        cursor = contract_collection.find(query_filter).sort("createTime", -1)
        contracts = await cursor.to_list(length=guest_limit)

        data = [serialize_doc(c) for c in contracts]
        return {
            "list": data,
            "total": guest_limit  # 强制让前端分页器知道访客只能看到限制条数
        }


# --- 3. 合同上传（支持文件附件）---
async def upload_contract(
    contractId: str,
    name: str,
    contractNo: str,
    category: Optional[str] = None,
    amount: Optional[float] = 0.0,
    status: Optional[str] = "草稿",
    customer: Optional[str] = None,
    customerType: Optional[str] = None,
    contractType: Optional[str] = None,
    signingCompany: Optional[str] = None,
    contactPerson: Optional[str] = None,
    contactPhone: Optional[str] = None,
    signDate: Optional[str] = None,
    servicePeriod: Optional[str] = None,
    remark: Optional[str] = None,
    operator: Optional[str] = "admin",
    customFields: Optional[str] = None,
    file: Optional[UploadFile] = None,
):
    try:
        # --- A. 生成系统时间字段 ---
        now_time = now_china().strftime("%Y-%m-%d %H:%M:%S")

        # --- B. 处理文件上传到 MinIO ---
        file_url = ""
        file_name = None
        file_path = None
        if file and file.filename:
            # 使用 contractId + 时间戳 + 扩展名，纯 ASCII，规避中文编码问题
            ext = Path(file.filename).suffix or ".pdf"
            file_name = f"{contractId}_{now_china().strftime('%Y%m%d%H%M%S')}{ext}"
            file_content = await file.read()
            minio_client.put_object(
                MINIO_BUCKET,
                file_name,
                BytesIO(file_content),
                len(file_content),
                content_type=file.content_type or "application/octet-stream",
            )
            file_path = file_name  # MinIO object name
            file_url = f"/api/contracts/file/{file_name}"

        # --- C. 组装存入 MongoDB 的真数据 (严格对应图 2 字段) ---
        new_doc = {
            "contractId": contractId,       # 唯一标识

            "name": name,
            "contractNo": contractNo,
            "category": category,
            "amount": amount,
            "status": status,
            "customer": customer,
            "customerType": customerType,
            "contractType": contractType,
            "signingCompany": signingCompany,  # 新增：签署公司
            "contactPerson": contactPerson,
            "contactPhone": contactPhone,
            "signDate": signDate,
            "servicePeriod": servicePeriod,
            "remark": remark,
            "fileUrl": file_url,           # 附件访问路径
            "fileName": file_name if file and file.filename else None,  # MinIO 对象名（带时间戳前缀，全局唯一）
            "filePath": file_path,
            "createTime": now_time,         # 创建时间
            "updateTime": now_time,         # 更新时间
            "isDeleted": False,             # 逻辑删除标记
            "operator": await resolve_display_name(operator if operator else "admin")  # 最后操作人
        }

        # --- D. 解析自定义字段 ---
        custom_data = {}
        if customFields:
            try:
                custom_data = json.loads(customFields)
            except json.JSONDecodeError:
                custom_data = {}

        # --- E. 写入 MongoDB ---
        doc_to_insert = {**new_doc}
        if custom_data:
            doc_to_insert["customFields"] = custom_data

        result = await contract_collection.insert_one(doc_to_insert)

        # 记日志
        op_user = operator if operator else "admin"
        await write_log(op_user, f"创建了合同：「{name}」，合同编号：{contractNo}", "info")

        return {
            "status": "success",
            "message": "同步成功",
            "contractId": contractId,
            "db_id": str(result.inserted_id)
        }

    except Exception as e:
        print(f"服务器内部错误: {str(e)}")
        return {"status": "error", "message": str(e)}


# --- 4. 合同更新（支持文件替换）---
async def update_contract(
    contract_id: str,
    contractId: Optional[str] = None,
    contractNo: Optional[str] = None,
    name: str = "",
    category: Optional[str] = None,
    amount: float = 0.0,
    status: Optional[str] = None,
    customer: Optional[str] = None,
    customerType: Optional[str] = None,
    contractType: Optional[str] = None,
    signingCompany: Optional[str] = None,
    contactPerson: Optional[str] = None,
    contactPhone: Optional[str] = None,
    signDate: Optional[str] = None,
    servicePeriod: Optional[str] = None,
    remark: Optional[str] = None,
    operator: Optional[str] = None,
    customFields: Optional[str] = None,
    file: Optional[UploadFile] = None,
):
    try:
        # 1. 验证传过来的 24 位 MongoDB ObjectId 是否符合规范
        if not ObjectId.is_valid(contract_id):
            raise HTTPException(status_code=400, detail="修改失败: 传入的 contract_id 格式不正确")

        # 2. 💡 核心修复：把所有从前端接收到的 Form 表单字段，打包组装进 update_data 字典中
        update_data = {
            "contractId": contractId if contractId else contractNo, # 新旧字段兼容
            "contractNo": contractNo if contractNo else contractId,
            "name": name,
            "category": category,
            "amount": amount,
            "status": status,
            "customer": customer,
            "customerType": customerType,
            "contractType": contractType,
            "signingCompany": signingCompany,  # 签署公司 — 修复编辑时无法同步
            "contactPerson": contactPerson,
            "contactPhone": contactPhone,
            "signDate": signDate,
            "servicePeriod": servicePeriod,
            "remark": remark,
            "operator": await resolve_display_name(operator if operator else "admin"),
            "updateTime": now_china().strftime("%Y-%m-%d %H:%M:%S") # 记录修改时间
        }

        # 3. 处理文件上传（如果用户在编辑时重新选了新文件）
        if file and file.filename:
            # 🔧 先查旧合同，从 MinIO 删除旧文件，避免存储空间膨胀
            existing = await contract_collection.find_one({"_id": ObjectId(contract_id)})
            if existing and existing.get("fileName"):
                try:
                    minio_client.remove_object(MINIO_BUCKET, existing["fileName"])
                    print(f"🗑️ 已删除 MinIO 旧文件: {existing['fileName']}")
                except S3Error as e:
                    print(f"⚠️ 删除 MinIO 旧文件失败: {e}")

            # 使用 contractId + 时间戳 + 扩展名，纯 ASCII，与上传逻辑一致
            ext = Path(file.filename).suffix or ".pdf"
            file_name = f"{contractId if contractId else contract_id}_{now_china().strftime('%Y%m%d%H%M%S')}{ext}"

            file_content = await file.read()
            minio_client.put_object(
                MINIO_BUCKET,
                file_name,
                BytesIO(file_content),
                len(file_content),
                content_type=file.content_type or "application/octet-stream",
            )

            # 将新的文件对象名和路径同步进更新字典里
            update_data["filePath"] = file_name
            update_data["fileName"] = file_name
            update_data["fileUrl"] = f"/api/contracts/file/{file_name}"

        # 4. 执行数据库更新操作
        # 解析自定义字段
        custom_data = {}
        if customFields:
            try:
                custom_data = json.loads(customFields)
            except json.JSONDecodeError:
                custom_data = {}
        if custom_data:
            update_data["customFields"] = custom_data

        result = await contract_collection.update_one(
            {"_id": ObjectId(contract_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="未找到对应的合同记录，修改失败")

        # 记日志
        op_user = operator if operator else "admin"
        await write_log(op_user, f"修改了合同：「{name}」", "info")

        return {"status": "success", "message": "合同数据及附件已成功更新"}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"后端修改报错详情: {str(e)}") # 方便控制台查错
        raise HTTPException(status_code=500, detail=f"服务器内部修改失败: {str(e)}")


# --- 5. 数据逻辑删除 ---
async def delete_contract(contract_id: str, operator: Optional[str] = None):
    try:
        # 兼容处理：如果传入的是24位ObjectId则按_id查询，否则按contractId查询
        if ObjectId.is_valid(contract_id):
            query = {"_id": ObjectId(contract_id)}
        else:
            query = {"$or": [{"contractId": contract_id}, {"contractNo": contract_id}]}

        # 🔧 删除前先删 MinIO 中的文件，避免存储空间膨胀
        contract = await contract_collection.find_one(query)
        if contract and contract.get("fileName"):
            try:
                minio_client.remove_object(MINIO_BUCKET, contract["fileName"])
                print(f"🗑️ 已删除 MinIO 文件: {contract['fileName']}")
            except S3Error as e:
                print(f"⚠️ 删除 MinIO 文件失败: {e}")

        # 逻辑删除：只标记为已删除，保留历史数据（同时记录最后操作人）
        result = await contract_collection.update_one(
            query,
            {"$set": {
                "isDeleted": True,
                "updateTime": now_china().strftime("%Y-%m-%d %H:%M:%S"),
                "operator": await resolve_display_name(operator if operator else "admin"),
            }}
        )

        if result.matched_count == 1:
            # 记日志
            contract_name = contract.get("name", contract_id) if contract else contract_id
            op_user = operator if operator else "admin"
            await write_log(op_user, f"删除了合同：「{contract_name}」", "warning")
            return {"message": "删除成功"}
        else:
            raise HTTPException(status_code=404, detail="未找到对应的合同记录")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 6. 批量打包下载合同附件 (Zip) ---
async def batch_download_contracts(contract_ids: List[str], operator: Optional[str] = None):
    try:
        # 1. 查找合同（兼容 contractId 和 contractNo）
        cursor = contract_collection.find({
            "$or": [
                {"contractId": {"$in": contract_ids}},
                {"contractNo": {"$in": contract_ids}}
            ],
            "isDeleted": False
        })
        # 注意：length 改为真实请求数组长度
        contracts_list = await cursor.to_list(length=len(contract_ids))

        if not contracts_list:
            raise HTTPException(status_code=404, detail="未找到任何有效的合同记录")

        # 2. 🌟 核心修复：从 MinIO 中精准匹配文件 🌟
        files_to_zip = []
        for c in contracts_list:
            # 从数据库中取出 MinIO 对象名（当初上传时写入的真实物理文件名）
            db_file_name = c.get("fileName")

            if db_file_name:
                try:
                    # 检查 MinIO 中文件是否存在
                    minio_client.stat_object(MINIO_BUCKET, db_file_name)
                    files_to_zip.append({
                        "object_name": db_file_name,
                        # 压缩包里显示的名字，始终使用合同名称
                        "display_name": f"{c.get('name', c.get('contractId', '合同'))}.pdf",
                        "contractNo": c.get("contractNo", "未知编号")
                    })
                except S3Error:
                    print(f"⚠️ 该文件数据库有记录，但 MinIO 中未找到: {db_file_name}")

        if not files_to_zip:
            raise HTTPException(status_code=400, detail="选中的合同文件均未在数据库中找到文件，无法打包")

        # 3. 在内存中打包成 ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            existing_names = set()
            for f in files_to_zip:
                original_name = f["display_name"]
                archive_name = original_name

                # 如果不同合同的下载显示名称重名了（例如都叫 采购合同.pdf），用编号区分，防止压缩包内覆盖
                if archive_name in existing_names:
                    archive_name = f"{f['contractNo']}_{original_name}"
                existing_names.add(archive_name)

                # 从 MinIO 读取文件并写入压缩包
                response = None
                try:
                    response = minio_client.get_object(MINIO_BUCKET, f["object_name"])
                    zip_file.writestr(archive_name, response.data)
                except S3Error as e:
                    print(f"⚠️ 从 MinIO 读取文件失败: {f['object_name']}, {e}")
                    continue
                finally:
                    if response:
                        response.close()
                        response.release_conn()

        zip_buffer.seek(0)

        # 4. 记日志
        op_user = operator if operator else "admin"
        await write_log(op_user, f"批量导出了 {len(files_to_zip)} 份合同附件（ZIP压缩包）", "info")

        # 5. 返回流式响应（使用分块生成器，避免 BytesIO 按换行符迭代损坏二进制数据）
        zip_name = f"contracts_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"

        def zip_stream():
            """分块读取 BytesIO，避免 __iter__ 按 \\n 分割破坏 ZIP 二进制"""
            zip_buffer.seek(0)
            while True:
                chunk = zip_buffer.read(64 * 1024)
                if not chunk:
                    break
                yield chunk

        return StreamingResponse(
            zip_stream(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_name}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ 批量打包发生异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量打包失败: {str(e)}")


# --- 7. 单个合同附件下载（还原 ced298a 原始实现）---
async def download_contract_by_id(contract_id: str):
    try:
        # 1. 🔍 查 MongoDB
        contract = await contract_collection.find_one({"contractId": contract_id, "isDeleted": False})
        if not contract or not contract.get("fileName"):
            raise HTTPException(status_code=444, detail="该合同未关联任何文件或文件记录不存在")

        # 2. 🎯 从 MinIO 获取文件流
        real_file_name = contract["fileName"]

        # 先确认文件在 MinIO 中存在
        try:
            minio_client.stat_object(MINIO_BUCKET, real_file_name)
        except S3Error:
            raise HTTPException(status_code=404, detail="合同附件文件未找到")

        # 3. 📥 以流式响应返回文件（使用 read() 分块，避免 stream() 行为不一致）
        download_display_name = f"{contract.get('name', contract_id)}.pdf"
        # RFC 5987 编码：HTTP 头只支持 ASCII，中文文件名必须 URL-encode
        encoded_filename = quote(download_display_name, safe='')

        def file_stream():
            """MinIO 文件流生成器 — 显式 read(64KB) 分块，自动释放连接"""
            response = None
            try:
                response = minio_client.get_object(MINIO_BUCKET, real_file_name)
                while True:
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    yield chunk
            finally:
                if response:
                    response.close()
                    response.release_conn()

        return StreamingResponse(
            file_stream(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Access-Control-Expose-Headers": "Content-Disposition",
            }
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ 下载文件发生异常错误: {str(e)}")
        raise HTTPException(status_code=404, detail="合同附件文件未找到")


# --- 8. 检查单个合同文件是否存在（轻量级预检，前端在触发下载前调用）---
async def check_contract_file_exists(contract_id: str) -> dict:
    """查询数据库和文件系统，确认合同附件是否就绪，返回 JSON 供前端判断"""
    try:
        contract = await contract_collection.find_one(
            {"contractId": contract_id, "isDeleted": False}
        )
        if not contract or not contract.get("fileName"):
            print(f"📎 [文件检查] contractId={contract_id} → 数据库无文件记录")
            return {"exists": False, "message": "该合同未关联任何附件文件"}

        real_file_name = contract["fileName"]

        try:
            minio_client.stat_object(MINIO_BUCKET, real_file_name)
        except S3Error:
            print(f"📎 [文件检查] contractId={contract_id} → MinIO 中不存在: {real_file_name}")
            return {"exists": False, "message": "服务器上未找到合同附件文件，可能已被删除"}

        print(f"📎 [文件检查] contractId={contract_id} → 文件就绪: {real_file_name}")
        return {
            "exists": True,
            "fileName": contract.get("name", contract_id),
            "message": "文件就绪，可以下载",
        }
    except Exception as e:
        print(f"❌ [文件检查] contractId={contract_id} → 异常: {str(e)}")
        return {"exists": False, "message": f"检查文件状态时出错: {str(e)}"}


# --- 9. 批量检查合同文件是否存在 ---
async def check_batch_files_exist(contract_ids: List[str]) -> dict:
    """批量预检：返回各文件的就绪状态，前端据此决定是否触发打包下载"""
    try:
        results = []
        for cid in contract_ids:
            r = await check_contract_file_exists(cid)
            results.append({"contractId": cid, "exists": r["exists"], "message": r["message"]})

        exists_list = [r for r in results if r["exists"]]
        missing_list = [r for r in results if not r["exists"]]

        all_exist = len(missing_list) == 0
        print(f"📦 [批量文件检查] 共 {len(contract_ids)} 个，就绪 {len(exists_list)}，缺失 {len(missing_list)}")

        return {
            "allExist": all_exist,
            "total": len(contract_ids),
            "existsCount": len(exists_list),
            "missingCount": len(missing_list),
            "missingIds": [r["contractId"] for r in missing_list],
            "details": results,
        }
    except Exception as e:
        print(f"❌ [批量文件检查] 异常: {str(e)}")
        return {"allExist": False, "total": len(contract_ids), "existsCount": 0,
                "missingCount": len(contract_ids), "missingIds": contract_ids,
                "details": [], "error": str(e)}
