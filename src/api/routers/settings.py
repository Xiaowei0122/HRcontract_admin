from typing import Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import settings_collection, logs_collection, user_collection, write_log

router = APIRouter(prefix="/api/settings", tags=["系统设置"])

# ── 所有可用合同字段定义（字段管理用）─────────────────────────
AVAILABLE_CONTRACT_FIELDS = [
    {"key": "contractId",   "label": "合同ID"},
    {"key": "name",         "label": "合同名称"},
    {"key": "contractType", "label": "合同类型"},
    {"key": "category",     "label": "产品类别"},
    {"key": "customerType", "label": "客户类别"},
    {"key": "customer",     "label": "客户名称"},
    {"key": "signingCompany","label": "签署公司"},
    {"key": "contactPerson","label": "联系人"},
    {"key": "contactPhone", "label": "联系电话"},
    {"key": "servicePeriod","label": "服务期限"},
    {"key": "signDate",     "label": "签订日期"},
    {"key": "amount",       "label": "合同金额(元)"},
    {"key": "status",       "label": "状态"},
    {"key": "remark",       "label": "备注"},
    {"key": "createTime",   "label": "创建时间"},
    {"key": "updateTime",   "label": "更新时间"},
    {"key": "contractNo",   "label": "合同编号"},
    {"key": "operator",     "label": "操作人"},
]

# ── 系统配置默认值（MongoDB 中无记录时使用）────────────────────
SYSTEM_CONFIG_DEFAULTS = {
    # 权限与预览控制
    "guest_data_limit": 2,
    "maintenance_mode": False,
    "allow_guest_upload": False,
    "guest_full_access": False,  # 访客全部开放：开启后访客可查看所有合同
    # 业务预警与显示
    "show_dashboard_charts": True,
    "big_amount_threshold": 100,  # 万元
    "default_visible_fields": [
        "contractId", "name", "category", "contractType", "customer",
        "customerType", "signingCompany", "amount", "status", "signDate",
    ],
    # 文件上传控制
    "max_upload_size_mb": 50,
    "allowed_file_types": "pdf,doc,docx,xls,xlsx,jpg,png",
    # 安全与系统
    "session_timeout_minutes": 0,   # 0 = 不限
    "contract_id_prefix": "HT",
    "log_retention_days": 30,
}

# ── Pydantic 模型 ─────────────────────────────────────────────
class ConfigUpdate(BaseModel):
    key: str
    value: Any

class FieldsUpdate(BaseModel):
    fields: List[str]

class PasswordUpdate(BaseModel):
    new_password: str

# ── 内部辅助 ──────────────────────────────────────────────────
SETTINGS_DOC_ID = "system_config"


async def _load_settings() -> dict:
    """从 MongoDB 加载配置，不存在则用默认值初始化"""
    doc = await settings_collection.find_one({"_id": SETTINGS_DOC_ID})
    if not doc:
        await settings_collection.insert_one({
            "_id": SETTINGS_DOC_ID,
            **SYSTEM_CONFIG_DEFAULTS,
        })
        return dict(SYSTEM_CONFIG_DEFAULTS)
    # 合并默认值：新加的 key 自动补全
    merged = dict(SYSTEM_CONFIG_DEFAULTS)
    for k in SYSTEM_CONFIG_DEFAULTS:
        if k in doc:
            merged[k] = doc[k]
    # 如果文档中有默认值里没有的旧 key，也保留
    for k, v in doc.items():
        if k != "_id" and k not in merged:
            merged[k] = v
    return merged


async def _save_settings(key: str, value: Any) -> None:
    """持久化单个配置项到 MongoDB"""
    await settings_collection.update_one(
        {"_id": SETTINGS_DOC_ID},
        {"$set": {key: value}},
        upsert=True,
    )


# ── 初始化（main.py startup 调用）─────────────────────────────
async def init_settings():
    """服务启动时确保 settings 文档存在并补全新字段"""
    doc = await settings_collection.find_one({"_id": SETTINGS_DOC_ID})
    if not doc:
        await settings_collection.insert_one({
            "_id": SETTINGS_DOC_ID,
            **SYSTEM_CONFIG_DEFAULTS,
        })
        print("✅ 已初始化系统配置文档")
        await write_log("system", "系统初始化完成，已创建默认配置", "info")
    else:
        # 补全新增的 key
        missing = {}
        for k, v in SYSTEM_CONFIG_DEFAULTS.items():
            if k not in doc:
                missing[k] = v
        if missing:
            await settings_collection.update_one(
                {"_id": SETTINGS_DOC_ID},
                {"$set": missing},
            )
            print(f"✅ 已补全系统配置缺失字段: {list(missing.keys())}")
            await write_log("system", f"自动补全新配置项: {', '.join(missing.keys())}", "info")
        else:
            # 配置完整，写一条启动日志
            await write_log("system", "后端服务启动，系统配置加载完成", "info")


# ═══════════════════════════════════════════════════════════════
#  接口
# ═══════════════════════════════════════════════════════════════

# ── 1. 获取全部配置 ───────────────────────────────────────────
@router.get("/")
async def get_all_settings():
    """获取所有系统配置（管理员用）"""
    return await _load_settings()


# ── 2. 获取可用字段列表 ───────────────────────────────────────
@router.get("/fields")
async def get_available_fields():
    """返回所有可管理的合同字段列表"""
    return {
        "availableFields": AVAILABLE_CONTRACT_FIELDS,
    }


# ── 3. 获取默认可见字段 ───────────────────────────────────────
@router.get("/default-fields")
async def get_default_fields():
    """获取管理员设定的默认可见字段（合同列表页使用）"""
    settings = await _load_settings()
    return {
        "defaultVisibleFields": settings.get("default_visible_fields", []),
    }


# ── 4. 设置默认可见字段 ───────────────────────────────────────
@router.post("/default-fields")
async def set_default_fields(data: FieldsUpdate):
    """管理员设定合同列表页默认显示哪些列"""
    await _save_settings("default_visible_fields", data.fields)
    await write_log("admin", f"修改默认显示字段为: {', '.join(data.fields)}")
    return {"status": "success", "message": "默认显示字段已更新"}


# ── 5. 更新单个配置项 ─────────────────────────────────────────
@router.post("/update")
async def update_setting(item: ConfigUpdate):
    """动态更新单个系统配置项，持久化到 MongoDB"""
    if item.key not in SYSTEM_CONFIG_DEFAULTS:
        raise HTTPException(status_code=400, detail=f"未定义的配置项: {item.key}")

    await _save_settings(item.key, item.value)
    await write_log("admin", f"修改配置「{item.key}」为 {item.value}")

    print(f"⚙️ 系统配置更新: {item.key} -> {item.value}")
    return {"status": "success", "message": f"已更新 {item.key}"}


# ── 6. 操作日志 ───────────────────────────────────────────────
@router.get("/logs")
async def get_logs():
    """获取最近 50 条系统操作日志"""
    try:
        cursor = logs_collection.find().sort("time", -1).limit(50)
        logs = await cursor.to_list(length=50)
        # 去掉 _id
        for log in logs:
            log.pop("_id", None)
        return logs
    except Exception as e:
        print(f"❌ 获取日志失败: {e}")
        return []


# ── 7. 修改管理员密码 ─────────────────────────────────────────
@router.post("/update_password")
async def update_password(data: PasswordUpdate):
    """管理员修改自己的密码"""
    import hashlib

    if not data.new_password or len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于6位")

    new_hash = hashlib.sha256(data.new_password.encode()).hexdigest()

    result = await user_collection.update_one(
        {"role": "admin"},
        {"$set": {"password": new_hash, "is_default_password": False}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="未找到管理员账号")

    await write_log("admin", "修改了管理员密码", "warning")
    return {"status": "success", "message": "管理员密码已修改，请妥善保管"}
