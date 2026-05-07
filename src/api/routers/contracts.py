import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# 路由配置
router = APIRouter(
    prefix="/api",
    tags=["合同管理"]
)

# 1. 数据库与文件存储配置
MONGO_DETAILS = "mongodb://admin:Hr85550780@192.168.1.111:32768/?authSource=admin"
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.HRcontract
contract_collection = database.get_collection("contract")

# NAS 文件保存路径（推荐使用环境变量，测试时可直接指定 NAS 共享目录）
# 例如：Path(r"\\192.168.1.111\HR_NAS\contracts")
UPLOAD_DIR = Path(os.getenv("CONTRACT_UPLOAD_DIR", r"\\192.168.1.111\contracts"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 2. 数据模型 (根据图 2 字段补全)
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

# 1. 获取合同列表 (支持增删改查中的“查”)
@router.get("/contracts")
async def get_contracts(role: Optional[str] = Query(None)):
    # 只查询未删除的合同
    cursor = contract_collection.find({"isDeleted": False}).sort("createTime", -1)
    contracts = await cursor.to_list(length=100)
    
    data = [serialize_doc(c) for c in contracts]
    if role == "admin":
        return data
    return data[:2]

# 2. 合同上传与文件保存 (支持“增”)
@router.post("/contracts/upload")
async def upload_contract(
    # 1. 必填字段 (必须和前端 formData.append 的第一个参数完全一致)
    name: str = Form(...),
    contractNo: str = Form(...),
    
    # 2. 可选字段 (全部设为 Form(None)，防止前端没传或传空导致崩溃)
    category: Optional[str] = Form(None),
    amount: Optional[float] = Form(0.0), # 如果前端传空，这里默认为 0.0
    status: Optional[str] = Form("草稿"),
    customer: Optional[str] = Form(None),
    customerType: Optional[str] = Form(None),
    contractType: Optional[str] = Form(None),
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
        # --- A. 后端自动生成系统字段 ---
        contractId = f"HT{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}" # 毫秒级 ID
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
    

# 3. 合同更新 (支持“改”)
@router.put("/contracts/{db_id}")
async def update_contract(
    db_id: str,
    name: Optional[str] = Form(None),
    contractNo: Optional[str] = Form(None),
    file: UploadFile = File(None),
    category: Optional[str] = Form(None),
    amount: Optional[float] = Form(None),
    status: Optional[str] = Form(None),
    contractType: Optional[str] = Form(None),
    customer: Optional[str] = Form(None),
    customerType: Optional[str] = Form(None),
    contactPerson: Optional[str] = Form(None),
    contactPhone: Optional[str] = Form(None),
    signDate: Optional[str] = Form(None),
    servicePeriod: Optional[str] = Form(None),
    remark: Optional[str] = Form(None),
    operator: Optional[str] = Form(None)
):
    # 1. 过滤并组装待更新字段
    update_fields = {}
    
    # 获取函数接收到的所有本地参数
    current_locals = locals()
    # 业务字段清单（排除掉 db_id 和 file 等特殊处理字段）
    business_fields = [
        "name", "contractNo", "contractType", "category", "amount", 
        "status", "customer", "customerType", "contactPerson", 
        "contactPhone", "signDate", "servicePeriod", "remark", "operator"
    ]
    
    for field in business_fields:
        val = current_locals.get(field)
        if val is not None:
            update_fields[field] = val

    # 2. 处理文件重新上传
    if file and file.filename:
        safe_name = Path(file.filename).name
        file_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
        target_path = UPLOAD_DIR / file_name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        update_fields["fileUrl"] = f"/api/contracts/file/{file_name}"
        update_fields["fileName"] = file.filename
        update_fields["filePath"] = str(target_path)

    if not update_fields:
        raise HTTPException(status_code=400, detail="未检测到任何修改内容")

    # 3. 核心：设置更新时间，绝不触碰 createTime 和 creator
    update_fields["updateTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # 4. 执行更新 (使用 $set 确保局部更新)
        result = await contract_collection.update_one(
            {"_id": ObjectId(db_id)}, 
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="数据库中未找到该记录")

        return {"status": "success", "message": "合同资料已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库同步失败: {str(e)}")

# 4. 数据逻辑删除 (前端不再显示，但数据仍在数据库中)
@router.delete("/contracts/{contract_id}")
async def delete_contract(contract_id: str):
    try:
        # 逻辑删除：只标记为已删除，保留历史数据
        result = await contract_collection.update_one(
            {"_id": ObjectId(contract_id)},
            {"$set": {"isDeleted": True, "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}
        )
        
        if result.matched_count == 1:
            return {"message": "删除成功"}
        else:
            raise HTTPException(status_code=404, detail="未找到对应的合同记录")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. 附件下载
@router.get("/contracts/file/{file_name}")
async def download_contract_file(file_name: str):
    try:
        safe_name = Path(file_name).name
        target_path = (UPLOAD_DIR / safe_name).resolve()
        if not str(target_path).startswith(str(UPLOAD_DIR.resolve())) or not target_path.exists():
            raise FileNotFoundError
        return FileResponse(target_path, filename=safe_name, media_type="application/octet-stream")
    except Exception:
        raise HTTPException(status_code=404, detail="文件未找到")