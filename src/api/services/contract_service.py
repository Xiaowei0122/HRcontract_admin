"""
合同管理业务逻辑
包含：Pydantic 模型、辅助函数、所有合同 CRUD / 看板 / 文件处理函数
原代码来源：routers/contracts.py
"""
import json
import os
import shutil
import zipfile
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from bson import ObjectId

from database import contract_collection, settings_collection, write_log
from services.shared import get_guest_data_limit

# ═══════════════════════════════════════════════════════════════
#  文件存储路径（原封不动提取）
# ═══════════════════════════════════════════════════════════════
# NAS 文件保存路径（推荐使用环境变量 CONTRACT_UPLOAD_DIR 指定）
# 本地测试：默认使用项目根目录下的 contracts 文件夹
# 生产环境：docker-compose.yml 中设置 CONTRACT_UPLOAD_DIR=/contracts，映射到 NAS
# services -> api -> src -> 项目根
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = Path(os.getenv("CONTRACT_UPLOAD_DIR", str(PROJECT_ROOT / "contracts")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
#  Pydantic 数据模型（原封不动提取）
# ═══════════════════════════════════════════════════════════════
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
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- B. 处理文件保存到 NAS ---
        file_url = ""
        file_name = None
        file_path = None
        if file and file.filename:
            safe_name = Path(file.filename).name
            file_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
            target_path = UPLOAD_DIR / file_name
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_path = str(target_path)
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
            "fileName": file_name if file and file.filename else None,  # 存储带时间戳的物理文件名，与磁盘一致
            "filePath": file_path,
            "createTime": now_time,         # 创建时间
            "updateTime": now_time,         # 更新时间
            "isDeleted": False,             # 逻辑删除标记
            "operator": operator            # 操作人
        }

        # --- D. 解析自定义字段 ---
        custom_data = {}
        if customFields:
            try:
                custom_data = json.loads(customFields)
            except json.JSONDecodeError:
                custom_data = {}

        # --- E. 写入 NAS 数据库 ---
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
            "operator": operator,
            "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 记录修改时间
        }

        # 3. 处理文件上传（如果用户在编辑时重新选了新文件）
        if file and file.filename:
            # 🔧 先查旧合同是否有物理文件，有则删除，避免 NAS 空间膨胀
            existing = await contract_collection.find_one({"_id": ObjectId(contract_id)})
            if existing and existing.get("filePath"):
                old_path = Path(existing["filePath"])
                if old_path.exists():
                    old_path.unlink()
                    print(f"🗑️ 已删除旧物理文件: {old_path}")

            original_filename = file.filename
            # 使用时间戳前缀保证物理文件名唯一，与上传逻辑保持一致
            file_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{Path(original_filename).name}"

            file_path = UPLOAD_DIR / file_name
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # 将新的文件路径和名称同步进更新字典里（字段名必须与上传时一致）
            update_data["filePath"] = str(file_path)
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
async def delete_contract(contract_id: str):
    try:
        # 兼容处理：如果传入的是24位ObjectId则按_id查询，否则按contractId查询
        if ObjectId.is_valid(contract_id):
            query = {"_id": ObjectId(contract_id)}
        else:
            query = {"$or": [{"contractId": contract_id}, {"contractNo": contract_id}]}

        # 🔧 删除前先查物理文件并删除，避免 NAS 空间膨胀
        contract = await contract_collection.find_one(query)
        if contract and contract.get("filePath"):
            old_path = Path(contract["filePath"])
            if old_path.exists():
                old_path.unlink()
                print(f"🗑️ 已删除物理文件: {old_path}")

        # 逻辑删除：只标记为已删除，保留历史数据
        result = await contract_collection.update_one(
            query,
            {"$set": {"isDeleted": True, "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}
        )

        if result.matched_count == 1:
            # 记日志
            contract_name = contract.get("name", contract_id) if contract else contract_id
            await write_log("admin", f"删除了合同：「{contract_name}」", "warning")
            return {"message": "删除成功"}
        else:
            raise HTTPException(status_code=404, detail="未找到对应的合同记录")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 6. 批量打包下载合同附件 (Zip) ---
async def batch_download_contracts(contract_ids: List[str]):
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

        # 2. 🌟 核心修复：根据规范，去 UPLOAD_DIR 下精准匹配 file_name 🌟
        files_to_zip = []
        for c in contracts_list:
            # 从数据库中取出当初上传成功时写入的真实物理文件名（包含日期和名称的长文件名）
            db_file_name = c.get("fileName")

            if db_file_name:
                # 安全过滤文件名，利用 Path().name 确保不发生目录穿越攻击
                safe_name = Path(db_file_name).name
                # 拼接成容器内的绝对物理路径：/app/api/contracts/2026xxxx_测试合同.pdf
                target_path = (UPLOAD_DIR / safe_name).resolve()

                # 安全校验：确保文件确实存在于挂载的 NAS 目录下
                if target_path.exists() and str(target_path).startswith(str(UPLOAD_DIR.resolve())):
                    files_to_zip.append({
                        "path": target_path,
                        # 压缩包里显示的名字，优先用合同本来好听的名字，没有就用长物理名
                        "display_name": f"{c.get('name', safe_name)}.pdf" if not safe_name.endswith('.pdf') else safe_name,
                        "contractNo": c.get("contractNo", "未知编号")
                    })
                else:
                    print(f"⚠️ 该文件数据库有记录，但未在文件系统中找到文件: {target_path}")

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

                # 写入压缩包
                zip_file.write(f["path"], archive_name)

        zip_buffer.seek(0)

        # 4. 记日志
        await write_log("admin", f"批量导出了 {len(files_to_zip)} 份合同附件（ZIP压缩包）", "info")

        # 5. 返回流式响应
        zip_name = f"contracts_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
        return StreamingResponse(
            zip_buffer,
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


# --- 7. 单个合同附件下载 ---
async def download_contract_by_id(contract_id: str):
    try:
        # 1. 🔍 拿着唯一的 contract_id 去 MongoDB 中查找对应的合同数据
        contract = await contract_collection.find_one({"contractId": contract_id, "isDeleted": False})

        # 2. 校验合同是否存在，以及当时上传时有没有成功写入 fileName 字段
        if not contract or not contract.get("fileName"):
            raise HTTPException(status_code=444, detail="该合同未关联任何文件或文件记录不存在")

        # 3. 🎯 从数据库直接取出真实的长物理文件名（如 20260613_...pdf）
        real_file_name = contract["fileName"]

        # 4. 🦺 依旧维持你原有的高安全性路径防穿越校验
        safe_name = Path(real_file_name).name
        target_path = (UPLOAD_DIR / safe_name).resolve()

        if not str(target_path).startswith(str(UPLOAD_DIR.resolve())) or not target_path.exists():
            raise FileNotFoundError

        # 5. 📥 返回文件流，这里的 filename 建议用合同的真实名称，让浏览器下载落盘时更好看
        download_display_name = f"{contract.get('name', contract_id)}.pdf"

        return FileResponse(
            target_path,
            filename=download_display_name,
            media_type="application/octet-stream"
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ 下载文件发生异常错误: {str(e)}")
        raise HTTPException(status_code=404, detail="合同附件文件未找到")
