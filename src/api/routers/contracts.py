import os
import shutil
import zipfile
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# 路由配置
router = APIRouter(
    prefix="/api",
    tags=["合同管理"]
)

# 1. 数据库与文件存储配置
#本地测试修改@地址为 192.168.1.111:32771, 生产环境请替换为 mongo-1:27017，并确保 docker-compose.yml 中的服务名称和端口映射正确
# 测试
#MONGO_DETAILS = os.getenv("MONGO_URL", "mongodb://admin:Hr85550780@192.168.1.111:32771/?authSource=admin")

# 生产
MONGO_DETAILS = os.getenv("MONGO_URL", "mongodb://admin:Hr85550780@mongo-1:27017/?authSource=admin")

client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.HRcontract
contract_collection = database.get_collection("contract")

# NAS 文件保存路径（推荐使用环境变量，测试时可直接指定 NAS 共享目录）
# 测试Path(r"\\192.168.1.111\HR_NAS\contracts")
# 生产环境请替换为/contracts，然后在docker-compose.yml中将/contracts映射到NASdocker容器的挂载目录

UPLOAD_DIR = Path(os.getenv("CONTRACT_UPLOAD_DIR", str(Path(__file__).resolve().parent.parent / "/contracts")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 2. 数据模型
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

# 辅助函数：将 MongoDB 文档转为 JSON
def serialize_doc(doc):
    if not doc: return None
    doc["_id"] = str(doc["_id"])
    return doc

# --- 接口实现 ---
# 1.获取合同数量统计数据
@router.get("/contracts/dashboard-stats")
async def get_dashboard_stats(
    role: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    contractType: Optional[str] = Query(None),
    customerType: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    minAmount: Optional[float] = Query(None),
    maxAmount: Optional[float] = Query(None),
):
    try:
        # 1. 组装与列表完全一致的筛选条件，保证大看板数据和当前筛选框同步
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

        # 2. 统计当前筛选条件下的：符合要求的合同总数量、总金额、已归档数量
        # 管理员看真实总数，访客默认写死限制（保持你原本的访客逻辑）
        if role == "admin":
            total_count = await contract_collection.count_documents(query_filter)
            
            # 利用 MongoDB 聚合直接算出：销售总额
            pipeline_amount = [{"$match": query_filter}, {"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
            amount_res = await contract_collection.aggregate(pipeline_amount).to_list(length=1)
            total_amount = amount_res[0]["total"] if amount_res else 0

            # 算已归档数量
            archived_filter = {**query_filter, "status": "已签署"}
            archived_count = await contract_collection.count_documents(archived_filter)
        else:
            # 访客模式下的写死兜底
            total_count = 2
            total_amount = 50000.0
            archived_count = 1

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


# 2. 获取合同详细信息 (支持增删改查中的“查”)
@router.get("/contracts")
async def get_contracts(
    role: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1),
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    contractType: Optional[str] = Query(None),
    customerType: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    minAmount: Optional[float] = Query(None),
    maxAmount: Optional[float] = Query(None),
):
    # 统一的基础查询：只查询未删除的合同
    query_filter = {"isDeleted": False}
    
    # 组合筛选条件
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
        # 依然保持你原本的死锁逻辑：总数只有 2 条，数据也只查 2 条
        cursor = contract_collection.find(query_filter).sort("createTime", -1)
        contracts = await cursor.to_list(length=2)
        
        data = [serialize_doc(c) for c in contracts]
        return {
            "list": data,
            "total": 2  # 强制让前端分页器知道访客只有 2 条，无法翻页
        }

# 3. 合同上传与文件保存 (支持“增”)
@router.post("/contracts/upload")
async def upload_contract(
    # 1. 必填字段 (必须和前端 formData.append 的第一个参数完全一致)
    contractId: str = Form(...), # 前端直接传入唯一 contractId
    name: str = Form(...),
    contractNo: str = Form(...),
    
    # 2. 可选字段 (全部设为 Form(None)，防止前端没传或传空导致崩溃)
    category: Optional[str] = Form(None),
    amount: Optional[float] = Form(0.0), # 如果前端传空，这里默认为 0.0
    status: Optional[str] = Form("草稿"),
    customer: Optional[str] = Form(None),
    customerType: Optional[str] = Form(None),
    contractType: Optional[str] = Form(None),
    signingCompany: Optional[str] = Form(None),  # 新增：签署公司
    contactPerson: Optional[str] = Form(None),
    contactPhone: Optional[str] = Form(None),
    signDate: Optional[str] = Form(None),
    servicePeriod: Optional[str] = Form(None),
    remark: Optional[str] = Form(None),
    operator: Optional[str] = Form("admin"),
    
    # 3. 文件对象 (字段名必须叫 file)
    file: UploadFile = File(None)
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
            "fileName": file.filename if file and file.filename else None,
            "filePath": file_path,
            "createTime": now_time,         # 创建时间
            "updateTime": now_time,         # 更新时间
            "isDeleted": False,             # 逻辑删除标记
            "operator": operator            # 操作人
        }

        # --- D. 写入 NAS 数据库 ---
        result = await contract_collection.insert_one(new_doc)
        
        return {
            "status": "success", 
            "message": "同步成功", 
            "contractId": contractId,
            "db_id": str(result.inserted_id)
        }

    except Exception as e:
        print(f"服务器内部错误: {str(e)}")
        return {"status": "error", "message": str(e)}
    

# 4. 合同更新 (支持“改”)
@router.put("/contracts/{contract_id}")
async def update_contract(
    contract_id: str,
    contractId: Optional[str] = Form(None),
    contractNo: Optional[str] = Form(None),
    name: str = Form(...),
    category: Optional[str] = Form(None),
    amount: float = Form(...),
    status: Optional[str] = Form(None),
    customer: Optional[str] = Form(None),
    customerType: Optional[str] = Form(None),
    contractType: Optional[str] = Form(None),
    contactPerson: Optional[str] = Form(None),
    contactPhone: Optional[str] = Form(None),
    signDate: Optional[str] = Form(None),
    servicePeriod: Optional[str] = Form(None),
    remark: Optional[str] = Form(None),
    operator: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
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
            "contactPerson": contactPerson,
            "contactPhone": contactPhone,
            "signDate": signDate,
            "servicePeriod": servicePeriod,
            "remark": remark,
            "operator": operator,
            "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 记录修改时间
        }

        # 3. 处理文件上传（如果用户在编辑时重新选了新文件）
        if file:
            filename = file.filename
            # 使用 contractNo 或 contractId 作为物理文件名，保持磁盘存储整洁
            use_no = contractNo if contractNo else contractId
            safe_name = f"{use_no}.pdf"
            
            file_path = UPLOAD_DIR / safe_name
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            # 将新的文件路径和名称同步进更新字典里
            update_data["path"] = str(file_path)
            update_data["name"] = filename

        # 4. 执行数据库更新操作
        result = await contract_collection.update_one(
            {"_id": ObjectId(contract_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="未找到对应的合同记录，修改失败")

        return {"status": "success", "message": "合同数据及附件已成功更新"}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"后端修改报错详情: {str(e)}") # 方便控制台查错
        raise HTTPException(status_code=500, detail=f"服务器内部修改失败: {str(e)}")
    

# 5. 数据逻辑删除 (前端不再显示，但数据仍在数据库中)
@router.delete("/contracts/{contract_id}")
async def delete_contract(contract_id: str):
    try:
        # 兼容处理：如果传入的是24位ObjectId则按_id查询，否则按contractId查询
        if ObjectId.is_valid(contract_id):
            query = {"_id": ObjectId(contract_id)}
        else:
            query = {"$or": [{"contractId": contract_id}, {"contractNo": contract_id}]}
        
        # 逻辑删除：只标记为已删除，保留历史数据
        result = await contract_collection.update_one(
            query,
            {"$set": {"isDeleted": True, "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}
        )
        
        if result.matched_count == 1:
            return {"message": "删除成功"}
        else:
            raise HTTPException(status_code=404, detail="未找到对应的合同记录")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. 批量打包下载合同附件 (Zip)
@router.get("/api/contracts/batch-download")
async def batch_download_contracts(
    contract_ids: List[str] = Query(...)
):
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
            db_file_name = c.get("file_name")
            
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
        
        # 4. 返回流式响应
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

# 7. 附件下载
@router.get("/api/contracts/download-by-id/{contract_id}")
async def download_contract_by_id(contract_id: str):
    try:
        # 1. 🔍 拿着唯一的 contract_id 去 MongoDB 中查找对应的合同数据
        contract = await contract_collection.find_one({"contractId": contract_id, "isDeleted": False})
        
        # 2. 校验合同是否存在，以及当时上传时有没有成功写入 file_name 字段
        if not contract or not contract.get("file_name"):
            raise HTTPException(status_code=444, detail="该合同未关联任何文件或文件记录不存在")
            
        # 3. 🎯 从数据库直接取出真实的长物理文件名（如 20260613_...pdf）
        real_file_name = contract["file_name"]
        
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