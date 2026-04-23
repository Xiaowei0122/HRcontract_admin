import sqlite3
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# 创建合同业务路由
router = APIRouter(
    prefix="/api",
    tags=["合同管理"]
)

# 完整保留你原有的 7 条模拟数据
MOCK_CONTRACTS = [
    { "id": 1, "name": "2026年度实验室服务器采购", "contractNo": "HT-001", "category": "计算机设备", "amount": 128.5, "status": "已签署", "customer": "华南理工大学" },
    { "id": 2, "name": "办公耗材协议", "contractNo": "HT-042", "category": "办公用品", "amount": 12.8, "status": "待签署", "customer": "省政务中心" },
    { "id": 3, "name": "2026年度实验室服务器群组采购", "contractNo": "HT-2026-JSJ-001", "category": "计算机设备", "amount": 128.50, "status": "已签署", "customer": "华南理工大学", "customerType": "高校", "contractType": "采购合同", "contactPerson": "张教授", "signDate": "2026-03-12" },
    { "id": 4, "name": "省政务中心办公耗材框架协议", "contractNo": "HT-2026-BG-042", "category": "办公用品", "amount": 12.80, "status": "待签署", "customer": "省政务服务中心", "customerType": "党政机关", "contractType": "框架合同", "contactPerson": "李主任", "signDate": "2026-04-05" },
    { "id": 5, "name": "智慧校园多媒体终端升级", "contractNo": "HT-2026-DZ-015", "category": "电子产品", "amount": 45.00, "status": "已签署", "customer": "市第一中学", "customerType": "事业单位", "contractType": "销售合同", "contactPerson": "王老师", "signDate": "2026-02-28" },
    { "id": 6, "name": "企业云端协作系统定制服务", "contractNo": "HT-2026-FW-009", "category": "计算机设备", "amount": 86.40, "status": "草稿", "customer": "中铁建某局分公司", "customerType": "国企", "contractType": "服务合同", "contactPerson": "赵经理", "signDate": "-" },
    { "id": 7, "name": "员工端午节福利礼品采购", "contractNo": "HT-2026-FL-003", "category": "福利产品", "amount": 5.20, "status": "已终止", "customer": "腾讯科技(深圳)", "customerType": "民营企业", "contractType": "采购合同", "contactPerson": "陈女士", "signDate": "2026-01-15" }
]

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "contracts.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contractNo TEXT NOT NULL,
            contractType TEXT,
            category TEXT,
            customerType TEXT,
            customer TEXT,
            contactPerson TEXT,
            contactPhone TEXT,
            servicePeriod TEXT,
            signDate TEXT,
            amount REAL,
            status TEXT,
            remark TEXT
        )
    """)
    conn.commit()

    count = conn.execute("SELECT COUNT(1) FROM contracts").fetchone()[0]
    if count == 0:
        for item in MOCK_CONTRACTS:
            conn.execute(
                "INSERT INTO contracts (name, contractNo, contractType, category, customerType, customer, contactPerson, contactPhone, servicePeriod, signDate, amount, status, remark) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item.get("name"),
                    item.get("contractNo"),
                    item.get("contractType"),
                    item.get("category"),
                    item.get("customerType"),
                    item.get("customer"),
                    item.get("contactPerson"),
                    item.get("contactPhone"),
                    item.get("servicePeriod"),
                    item.get("signDate"),
                    item.get("amount"),
                    item.get("status"),
                    item.get("remark")
                )
            )
        conn.commit()
    conn.close()


init_db()


def row_to_dict(row: sqlite3.Row):
    return {key: row[key] for key in row.keys()}


def fetch_contracts(role: Optional[str] = None) -> List[dict]:
    conn = get_db_conn()
    rows = conn.execute("SELECT * FROM contracts ORDER BY id").fetchall()
    conn.close()
    data = [row_to_dict(row) for row in rows]
    if role == "admin":
        print("🔐 安全日志：管理员正在调取全量合同数据")
        return data
    print("ℹ️ 业务日志：访客正在预览合同数据")
    return data[:2]


def insert_contract(contract: "ContractData") -> dict:
    conn = get_db_conn()
    cursor = conn.execute(
        "INSERT INTO contracts (name, contractNo, contractType, category, customerType, customer, contactPerson, contactPhone, servicePeriod, signDate, amount, status, remark) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            contract.name,
            contract.contractNo,
            contract.contractType,
            contract.category,
            contract.customerType,
            contract.customer,
            contract.contactPerson,
            contract.contactPhone,
            contract.servicePeriod,
            contract.signDate,
            contract.amount,
            contract.status,
            contract.remark
        )
    )
    conn.commit()
    contract_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


def update_contract_by_id(contract_id: int, contract: "ContractData") -> dict:
    conn = get_db_conn()
    existing = conn.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="合同不存在")

    conn.execute(
        "UPDATE contracts SET name = ?, contractNo = ?, contractType = ?, category = ?, customerType = ?, customer = ?, contactPerson = ?, contactPhone = ?, servicePeriod = ?, signDate = ?, amount = ?, status = ?, remark = ? WHERE id = ?",
        (
            contract.name,
            contract.contractNo,
            contract.contractType,
            contract.category,
            contract.customerType,
            contract.customer,
            contract.contactPerson,
            contract.contactPhone,
            contract.servicePeriod,
            contract.signDate,
            contract.amount,
            contract.status,
            contract.remark,
            contract_id
        )
    )
    conn.commit()
    row = conn.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


class ContractData(BaseModel):
    name: str
    contractNo: str
    contractType: Optional[str] = None
    category: Optional[str] = None
    customerType: Optional[str] = None
    customer: Optional[str] = None
    contactPerson: Optional[str] = None
    contactPhone: Optional[str] = None
    servicePeriod: Optional[str] = None
    signDate: Optional[str] = None
    amount: Optional[float] = 0.0
    status: Optional[str] = "草稿"
    remark: Optional[str] = None


# 1. 获取合同列表接口
@router.get("/contracts")
async def get_contracts(role: Optional[str] = Query(None)):
    return fetch_contracts(role)


# 2. 合同上传接口
@router.post("/contracts/upload")
async def upload_contract(data: ContractData):
    saved = insert_contract(data)
    return {"status": "success", "message": "合同上传成功", "contract": saved}


# 3. 合同更新接口
@router.put("/contracts/{contract_id}")
async def update_contract(contract_id: int, data: ContractData):
    updated = update_contract_by_id(contract_id, data)
    return {"status": "success", "message": "合同更新成功", "contract": updated}
