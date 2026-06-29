"""
合同管理路由（薄层 — 仅负责路由注册和参数解析，业务逻辑在 services/contract_service.py）
"""
from typing import List, Optional

from fastapi import APIRouter, Query, UploadFile, File, Form
from services.contract_service import (
    get_dashboard_stats, get_contracts,
    upload_contract, update_contract, delete_contract,
    batch_download_contracts, download_contract_by_id,
)

# 路由配置
router = APIRouter(
    prefix="/api",
    tags=["合同管理"]
)

# --- 1. 获取合同数量统计数据（看板用）---
@router.get("/contracts/dashboard-stats")
async def dashboard_stats(
    role: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    contractType: Optional[str] = Query(None),
    customerType: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    minAmount: Optional[float] = Query(None),
    maxAmount: Optional[float] = Query(None),
):
    return await get_dashboard_stats(
        role=role, keyword=keyword, category=category,
        contractType=contractType, customerType=customerType,
        status=status, minAmount=minAmount, maxAmount=maxAmount,
    )


# --- 2. 获取合同列表（支持分页和筛选）---
@router.get("/contracts")
async def contracts_list(
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
    return await get_contracts(
        role=role, page=page, size=size, keyword=keyword,
        category=category, contractType=contractType,
        customerType=customerType, status=status,
        minAmount=minAmount, maxAmount=maxAmount,
    )


# --- 3. 合同上传（支持文件附件）---
@router.post("/contracts/upload")
async def upload(
    contractId: str = Form(...),
    name: str = Form(...),
    contractNo: str = Form(...),
    category: Optional[str] = Form(None),
    amount: Optional[float] = Form(0.0),
    status: Optional[str] = Form("草稿"),
    customer: Optional[str] = Form(None),
    customerType: Optional[str] = Form(None),
    contractType: Optional[str] = Form(None),
    signingCompany: Optional[str] = Form(None),
    contactPerson: Optional[str] = Form(None),
    contactPhone: Optional[str] = Form(None),
    signDate: Optional[str] = Form(None),
    servicePeriod: Optional[str] = Form(None),
    remark: Optional[str] = Form(None),
    operator: Optional[str] = Form("admin"),
    customFields: Optional[str] = Form(None),
    file: UploadFile = File(None),
):
    return await upload_contract(
        contractId=contractId, name=name, contractNo=contractNo,
        category=category, amount=amount, status=status,
        customer=customer, customerType=customerType,
        contractType=contractType, signingCompany=signingCompany,
        contactPerson=contactPerson, contactPhone=contactPhone,
        signDate=signDate, servicePeriod=servicePeriod,
        remark=remark, operator=operator, customFields=customFields, file=file,
    )


# --- 4. 合同更新（支持文件替换）---
@router.put("/contracts/{contract_id}")
async def update(
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
    signingCompany: Optional[str] = Form(None),
    contactPerson: Optional[str] = Form(None),
    contactPhone: Optional[str] = Form(None),
    signDate: Optional[str] = Form(None),
    servicePeriod: Optional[str] = Form(None),
    remark: Optional[str] = Form(None),
    operator: Optional[str] = Form(None),
    customFields: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    return await update_contract(
        contract_id=contract_id,
        contractId=contractId, contractNo=contractNo, name=name,
        category=category, amount=amount, status=status,
        customer=customer, customerType=customerType,
        contractType=contractType, signingCompany=signingCompany,
        contactPerson=contactPerson, contactPhone=contactPhone,
        signDate=signDate, servicePeriod=servicePeriod,
        remark=remark, operator=operator, customFields=customFields, file=file,
    )


# --- 5. 数据逻辑删除 ---
@router.delete("/contracts/{contract_id}")
async def delete(contract_id: str):
    return await delete_contract(contract_id)


# --- 6. 批量打包下载合同附件 (Zip) ---
@router.get("/contracts/batch-download")
async def batch_download(
    contract_ids: List[str] = Query(...)
):
    return await batch_download_contracts(contract_ids)


# --- 7. 单个合同附件下载 ---
@router.get("/contracts/download-by-id/{contract_id}")
async def download_by_id(contract_id: str):
    return await download_contract_by_id(contract_id)
