"""
系统设置业务逻辑
包含：常量定义、Pydantic 模型、辅助函数、所有系统设置/日志/密码管理处理函数
原代码来源：routers/settings.py
"""
import re
from typing import Any, List

from fastapi import HTTPException
from pydantic import BaseModel

from database import settings_collection, logs_collection, user_collection, write_log, resolve_display_name
from services.auth_service import verify_admin_token

# ═══════════════════════════════════════════════════════════════
#  常量定义（原封不动提取）
# ═══════════════════════════════════════════════════════════════

SETTINGS_DOC_ID = "system_config"

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
    {"key": "operator",     "label": "最后操作人"},
]

# ── 基础字段 key 集合（不可删除）─────────────────────────────────
BASE_FIELD_KEYS = [f["key"] for f in AVAILABLE_CONTRACT_FIELDS]

# ── 自定义字段可选类型 ───────────────────────────────────────────
FIELD_TYPE_OPTIONS = ["text", "number", "date", "select"]

# ── 默认产品类别 ─────────────────────────────────────────────────
DEFAULT_CATEGORIES = [
    "计算机设备", "办公用品", "电子产品", "福利产品",
    "劳保用品", "办公耗材", "网络安防", "维修维护服务",
]

# ── 默认签署公司 ─────────────────────────────────────────────────
DEFAULT_SIGNING_COMPANIES = ["鸿瑞办公", "政通慧采", "众冠供应链"]

# ── 默认客户类别 ─────────────────────────────────────────────────
DEFAULT_CUSTOMER_TYPES = ["高校", "党政机关", "国企", "央企", "事业单位", "民营企业"]

# ── 默认类别颜色映射（新增类别自动分配颜色）──────────────────────
CATEGORY_COLOR_POOL = [
    "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#f97316",
    "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16", "#f43f5e",
    "#14b8a6", "#a855f7", "#e11d48", "#0ea5e9", "#6366f1",
]

# ── 配置项中文名称映射（用于操作日志友好提示）──────────────────
CONFIG_KEY_LABELS = {
    "guest_data_limit": "访客可查看的数据条数",
    "maintenance_mode": "系统维护模式",
    "allow_guest_upload": "访客上传权限",
    "guest_full_access": "访客查看全部合同权限",
    "show_dashboard_charts": "看板图表显示",
    "big_amount_threshold": "大额合同预警阈值（万元）",
    "default_visible_fields": "合同列表默认显示字段",
    "max_upload_size_mb": "文件上传大小限制（MB）",
    "allowed_file_types": "允许上传的文件类型",
    "session_timeout_minutes": "会话超时时间（分钟）",
    "contract_id_prefix": "合同ID前缀",
    "log_retention_days": "日志保留天数",
    "allow_user_delete": "允许普通用户删除合同",
    "custom_fields": "自定义合同字段",
    "categories": "产品类别配置",
    "category_colors": "类别颜色映射",
    "signing_companies": "签署公司配置",
    "customer_types": "客户类别配置",
}

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
        "operator",
    ],
    # 文件上传控制
    "max_upload_size_mb": 50,
    "allowed_file_types": "pdf,doc,docx,xls,xlsx,jpg,png",
    # 安全与系统
    "session_timeout_minutes": 0,   # 0 = 不限
    "contract_id_prefix": "HT",
    "log_retention_days": 30,
    # 权限控制
    "allow_user_delete": False,  # 默认禁止普通用户删除合同
    # 自定义字段与类别
    "custom_fields": [],         # 管理员新增的自定义合同字段
    "categories": DEFAULT_CATEGORIES,  # 产品类别列表
    "category_colors": {},       # 类别颜色映射（动态生成）
    "signing_companies": DEFAULT_SIGNING_COMPANIES,  # 签署公司列表
    "customer_types": DEFAULT_CUSTOMER_TYPES,        # 客户类别列表
}

# ═══════════════════════════════════════════════════════════════
#  Pydantic 模型（原封不动提取）
# ═══════════════════════════════════════════════════════════════

class ConfigUpdate(BaseModel):
    key: str
    value: Any
    token: str          # 管理员令牌（必填，用于权限校验）

class FieldsUpdate(BaseModel):
    fields: List[str]
    token: str

class PasswordUpdate(BaseModel):
    new_password: str
    token: str

class CustomFieldCreate(BaseModel):
    key: str = ""       # 字段标识（英文），为空则自动从 label 生成
    label: str
    fieldType: str = "text"
    token: str

class CustomFieldUpdate(BaseModel):
    label: str
    fieldType: str = "text"
    token: str

class CategoryCreate(BaseModel):
    name: str
    color: str = ""       # 可选，管理员自选颜色；为空则自动分配
    token: str

class CategoryUpdate(BaseModel):
    name: str
    color: str = ""       # 可选，为空则保留原颜色不变
    token: str

class SigningCompanyCreate(BaseModel):
    name: str
    token: str

class SigningCompanyUpdate(BaseModel):
    name: str
    token: str

class CustomerTypeCreate(BaseModel):
    name: str
    token: str

class CustomerTypeUpdate(BaseModel):
    name: str
    token: str


# ═══════════════════════════════════════════════════════════════
#  内部辅助函数（原封不动提取）
# ═══════════════════════════════════════════════════════════════

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
        await write_log("system", "系统首次启动，已自动创建默认配置", "info")
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
            # 将缺失的配置 key 映射为中文名称，让管理员看得懂
            missing_labels = [CONFIG_KEY_LABELS.get(k, k) for k in missing.keys()]
            await write_log("system", f"系统升级，自动新增了以下配置项：{'、'.join(missing_labels)}", "info")
        else:
            # 配置完整，写一条启动日志
            await write_log("system", "系统服务已启动，所有配置加载完成", "info")


# ═══════════════════════════════════════════════════════════════
#  业务逻辑函数（对应各 API 端点，原封不动提取）
# ═══════════════════════════════════════════════════════════════

# ── 1. 获取全部配置 ───────────────────────────────────────────
async def get_all_settings():
    """获取所有系统配置（管理员用）"""
    return await _load_settings()


# ── 2. 获取可用字段列表（基础 + 自定义）───────────────────────
async def get_available_fields():
    """返回所有可用合同字段（基础字段 + 管理员自定义字段）"""
    settings = await _load_settings()
    custom_fields = settings.get("custom_fields", [])
    merged = []
    for f in AVAILABLE_CONTRACT_FIELDS:
        merged.append({**f, "isCustom": False})
    for cf in custom_fields:
        merged.append({
            "key": cf["key"],
            "label": cf["label"],
            "fieldType": cf.get("fieldType", "text"),
            "isCustom": True,
        })
    return {"availableFields": merged}


# ── 3. 获取默认可见字段 ───────────────────────────────────────
async def get_default_fields():
    """获取管理员设定的默认可见字段（合同列表页使用）"""
    settings = await _load_settings()
    return {
        "defaultVisibleFields": settings.get("default_visible_fields", []),
    }


# ── 4. 设置默认可见字段 ───────────────────────────────────────
async def set_default_fields(data: FieldsUpdate):
    """管理员设定合同列表页默认显示哪些列"""
    admin = await verify_admin_token(data.token)
    await _save_settings("default_visible_fields", data.fields)
    # 将字段 key 映射为中文标签（查找范围：基础 + 自定义）
    settings = await _load_settings()
    custom_fields = settings.get("custom_fields", [])
    all_field_defs = list(AVAILABLE_CONTRACT_FIELDS)
    for cf in custom_fields:
        all_field_defs.append({"key": cf["key"], "label": cf["label"]})
    field_labels = []
    for f_key in data.fields:
        found = False
        for field_def in all_field_defs:
            if field_def["key"] == f_key:
                field_labels.append(field_def["label"])
                found = True
                break
        if not found:
            field_labels.append(f_key)
    await write_log(admin["username"], f"调整了合同列表的默认显示列，当前显示：{'、'.join(field_labels)}")
    return {"status": "success", "message": "默认显示字段已更新"}


# ── 5. 更新单个配置项 ─────────────────────────────────────────
async def update_setting(item: ConfigUpdate):
    """动态更新单个系统配置项，持久化到 MongoDB"""
    admin = await verify_admin_token(item.token)
    if item.key not in SYSTEM_CONFIG_DEFAULTS:
        raise HTTPException(status_code=400, detail=f"未定义的配置项: {item.key}")

    await _save_settings(item.key, item.value)
    friendly_name = CONFIG_KEY_LABELS.get(item.key, item.key)
    await write_log(admin["username"], f"修改了系统设置「{friendly_name}」为：{item.value}")

    print(f"⚙️ 系统配置更新: {item.key} -> {item.value}")
    return {"status": "success", "message": f"已更新 {item.key}"}


# ── 6. 操作日志（分页）───────────────────────────────────────
async def get_logs(page: int = 1, pageSize: int = 20):
    """分页获取系统操作日志，默认每页 20 条

    自动将旧日志中的原始用户名解析为显示名称（新日志在写入时已包含显示名称）。
    """
    try:
        total = await logs_collection.count_documents({})
        skip = (page - 1) * pageSize
        cursor = logs_collection.find().sort("time", -1).skip(skip).limit(pageSize)
        logs = await cursor.to_list(length=pageSize)
        # 去掉 _id，并兼容旧日志：将原始用户名解析为显示名称
        for log in logs:
            log.pop("_id", None)
            # resolve_display_name 对已解析的名称（如"系统管理员"）会原样返回
            # 对旧日志中的原始用户名（如"admin"、"xiaowei"）会解析为显示名称
            log["user"] = await resolve_display_name(log["user"])
        return {"logs": logs, "total": total, "page": page, "pageSize": pageSize}
    except Exception as e:
        print(f"❌ 获取日志失败: {e}")
        return {"logs": [], "total": 0, "page": page, "pageSize": pageSize}


# ── 7. 修改管理员密码 ─────────────────────────────────────────
async def update_admin_password(data: PasswordUpdate):
    """管理员修改自己的密码"""
    import hashlib

    admin = await verify_admin_token(data.token)

    if not data.new_password or len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于6位")

    new_hash = hashlib.sha256(data.new_password.encode()).hexdigest()

    result = await user_collection.update_one(
        {"role": "admin"},
        {"$set": {"password": new_hash, "is_default_password": False}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="未找到管理员账号")

    await write_log(admin["username"], "管理员密码已被修改", "warning")
    return {"status": "success", "message": "管理员密码已修改，请妥善保管"}


# ═══════════════════════════════════════════════════════════════
#  8. 自定义字段 CRUD
# ═══════════════════════════════════════════════════════════════

async def get_field_definitions():
    """获取所有字段定义（基础 + 自定义），供前端字段管理使用"""
    settings = await _load_settings()
    custom_fields = settings.get("custom_fields", [])
    base_fields = []
    for f in AVAILABLE_CONTRACT_FIELDS:
        base_fields.append({**f, "isCustom": False, "fieldType": "text"})
    result = base_fields + [
        {"key": cf["key"], "label": cf["label"],
         "fieldType": cf.get("fieldType", "text"), "isCustom": True}
        for cf in custom_fields
    ]
    return {"fields": result, "baseFieldKeys": BASE_FIELD_KEYS}


async def add_custom_field(data: CustomFieldCreate):
    """新增自定义合同字段（key 由用户提供，必须以英文命名）"""
    admin = await verify_admin_token(data.token)
    settings = await _load_settings()
    custom_fields = list(settings.get("custom_fields", []))

    all_keys = set(BASE_FIELD_KEYS + [f["key"] for f in custom_fields])

    if data.key and data.key.strip():
        # 用户手动指定了 key — 校验必须以英文字母开头，只能包含英文/数字/下划线
        key = data.key.strip()
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', key):
            raise HTTPException(status_code=400,
                detail="字段标识必须以英文字母开头，只能包含英文字母、数字和下划线")
        if key in all_keys:
            raise HTTPException(status_code=400, detail=f"字段标识 '{key}' 已存在，请换一个")
    else:
        # 兼容旧逻辑：未提供 key 时自动从 label 拼音生成
        key = "custom_" + re.sub(r'[^a-zA-Z0-9]', '_', data.label.lower()).strip('_')
        suffix = 1
        base_key = key
        while key in all_keys:
            key = f"{base_key}_{suffix}"
            suffix += 1

    if data.fieldType not in FIELD_TYPE_OPTIONS:
        raise HTTPException(status_code=400, detail=f"字段类型必须为: {', '.join(FIELD_TYPE_OPTIONS)}")

    new_field = {"key": key, "label": data.label, "fieldType": data.fieldType}
    custom_fields.append(new_field)
    await _save_settings("custom_fields", custom_fields)
    await write_log(admin["username"], f"新增了自定义字段「{data.label}」（{key}）", "info")
    return {"status": "success", "field": new_field}


async def update_custom_field(field_key: str, data: CustomFieldUpdate):
    """修改自定义字段的显示名称或类型"""
    admin = await verify_admin_token(data.token)
    if field_key in BASE_FIELD_KEYS:
        raise HTTPException(status_code=400, detail="基础字段不可修改，只能修改显示名称")

    if data.fieldType not in FIELD_TYPE_OPTIONS:
        raise HTTPException(status_code=400, detail=f"字段类型必须为: {', '.join(FIELD_TYPE_OPTIONS)}")

    settings = await _load_settings()
    custom_fields = list(settings.get("custom_fields", []))
    for f in custom_fields:
        if f["key"] == field_key:
            f["label"] = data.label
            f["fieldType"] = data.fieldType
            await _save_settings("custom_fields", custom_fields)
            await write_log(admin["username"], f"修改了自定义字段「{data.label}」", "info")
            return {"status": "success", "field": f}
    raise HTTPException(status_code=404, detail=f"未找到自定义字段: {field_key}")


async def delete_custom_field(field_key: str, token: str):
    """删除自定义字段（基础字段不可删除）"""
    admin = await verify_admin_token(token)
    if field_key in BASE_FIELD_KEYS:
        raise HTTPException(status_code=400, detail="基础字段不可删除")

    settings = await _load_settings()
    custom_fields = list(settings.get("custom_fields", []))
    removed = None
    new_list = []
    for f in custom_fields:
        if f["key"] == field_key:
            removed = f
        else:
            new_list.append(f)
    if removed is None:
        raise HTTPException(status_code=404, detail=f"未找到自定义字段: {field_key}")

    await _save_settings("custom_fields", new_list)

    # 同步清理 default_visible_fields 中的该字段
    default_fields = list(settings.get("default_visible_fields", []))
    if field_key in default_fields:
        default_fields.remove(field_key)
        await _save_settings("default_visible_fields", default_fields)

    await write_log(admin["username"], f"删除了自定义字段「{removed['label']}」", "warning")
    return {"status": "success", "message": f"字段「{removed['label']}」已删除"}


# ═══════════════════════════════════════════════════════════════
#  9. 产品类别管理
# ═══════════════════════════════════════════════════════════════

async def get_categories():
    """获取产品类别列表及颜色映射"""
    settings = await _load_settings()
    cats = settings.get("categories", DEFAULT_CATEGORIES)
    colors = settings.get("category_colors", {})
    # 为没有颜色的类别自动分配（使用首个未被占用的颜色，而非 index 取模）
    changed = False
    for cat in cats:
        if cat not in colors or not colors[cat]:
            colors[cat] = _get_next_color(colors)
            changed = True
    # 持久化：确保后续增/删操作不会读取到空的 category_colors 导致前端标签全蓝
    if changed:
        await _save_settings("category_colors", colors)
    return {"categories": cats, "categoryColors": colors}


def _get_next_color(colors_dict: dict) -> str:
    """从颜色池中选取第一个未被现有类别占用的颜色"""
    used = set(v for v in colors_dict.values() if v)
    for c in CATEGORY_COLOR_POOL:
        if c not in used:
            return c
    # 颜色池耗尽，循环复用
    return CATEGORY_COLOR_POOL[len(used) % len(CATEGORY_COLOR_POOL)]


async def add_category(data: CategoryCreate):
    """新增产品类别"""
    admin = await verify_admin_token(data.token)
    settings = await _load_settings()
    cats = list(settings.get("categories", DEFAULT_CATEGORIES))
    colors = dict(settings.get("category_colors", {}))
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="类别名称不能为空")
    if name in cats:
        raise HTTPException(status_code=400, detail="该类别已存在")
    cats.append(name)
    # 颜色：优先使用管理员自选颜色，否则自动从池中分配首个未占用色
    if data.color and data.color.strip():
        colors[name] = data.color.strip()
    else:
        colors[name] = _get_next_color(colors)
    await _save_settings("categories", cats)
    await _save_settings("category_colors", colors)
    await write_log(admin["username"], f"新增了产品类别「{name}」", "info")
    return {"status": "success", "categories": cats, "categoryColors": colors}


async def update_category(cat_index: int, data: CategoryUpdate):
    """修改产品类别名称（及可选颜色）"""
    admin = await verify_admin_token(data.token)
    settings = await _load_settings()
    cats = list(settings.get("categories", DEFAULT_CATEGORIES))
    colors = dict(settings.get("category_colors", {}))
    if cat_index < 0 or cat_index >= len(cats):
        raise HTTPException(status_code=400, detail="无效的类别索引")
    old_name = cats[cat_index]
    new_name = data.name.strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="类别名称不能为空")
    if new_name != old_name and new_name in cats:
        raise HTTPException(status_code=400, detail="该类别已存在")
    cats[cat_index] = new_name
    # 迁移颜色
    if old_name in colors:
        colors[new_name] = colors.pop(old_name)
    # 如果管理员指定了新颜色，覆盖
    if data.color and data.color.strip():
        colors[new_name] = data.color.strip()
    await _save_settings("categories", cats)
    await _save_settings("category_colors", colors)
    await write_log(admin["username"], f"将产品类别「{old_name}」修改为「{new_name}」", "info")
    return {"status": "success", "categories": cats, "categoryColors": colors}


async def delete_category(cat_index: int, token: str):
    """删除产品类别"""
    admin = await verify_admin_token(token)
    settings = await _load_settings()
    cats = list(settings.get("categories", DEFAULT_CATEGORIES))
    if cat_index < 0 or cat_index >= len(cats):
        raise HTTPException(status_code=400, detail="无效的类别索引")
    removed = cats.pop(cat_index)
    await _save_settings("categories", cats)
    await write_log(admin["username"], f"删除了产品类别「{removed}」", "warning")
    colors = settings.get("category_colors", {})
    return {"status": "success", "categories": cats, "categoryColors": colors}


# ═══════════════════════════════════════════════════════════════
#  10. 签署公司管理
# ═══════════════════════════════════════════════════════════════

async def get_signing_companies():
    """获取签署公司列表"""
    settings = await _load_settings()
    companies = settings.get("signing_companies", DEFAULT_SIGNING_COMPANIES)
    return {"signingCompanies": companies}


async def add_signing_company(data: SigningCompanyCreate):
    """新增签署公司"""
    admin = await verify_admin_token(data.token)
    settings = await _load_settings()
    companies = list(settings.get("signing_companies", DEFAULT_SIGNING_COMPANIES))
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="公司名称不能为空")
    if name in companies:
        raise HTTPException(status_code=400, detail="该公司已存在")
    companies.append(name)
    await _save_settings("signing_companies", companies)
    await write_log(admin["username"], f"新增了签署公司「{name}」", "info")
    return {"status": "success", "signingCompanies": companies}


async def update_signing_company(company_index: int, data: SigningCompanyUpdate):
    """修改签署公司名称"""
    admin = await verify_admin_token(data.token)
    settings = await _load_settings()
    companies = list(settings.get("signing_companies", DEFAULT_SIGNING_COMPANIES))
    if company_index < 0 or company_index >= len(companies):
        raise HTTPException(status_code=400, detail="无效的公司索引")
    old_name = companies[company_index]
    new_name = data.name.strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="公司名称不能为空")
    if new_name != old_name and new_name in companies:
        raise HTTPException(status_code=400, detail="该公司已存在")
    companies[company_index] = new_name
    await _save_settings("signing_companies", companies)
    await write_log(admin["username"], f"将签署公司「{old_name}」修改为「{new_name}」", "info")
    return {"status": "success", "signingCompanies": companies}


async def delete_signing_company(company_index: int, token: str):
    """删除签署公司"""
    admin = await verify_admin_token(token)
    settings = await _load_settings()
    companies = list(settings.get("signing_companies", DEFAULT_SIGNING_COMPANIES))
    if company_index < 0 or company_index >= len(companies):
        raise HTTPException(status_code=400, detail="无效的公司索引")
    removed = companies.pop(company_index)
    await _save_settings("signing_companies", companies)
    await write_log(admin["username"], f"删除了签署公司「{removed}」", "warning")
    return {"status": "success", "signingCompanies": companies}


# ═══════════════════════════════════════════════════════════════
#  11. 客户类别管理
# ═══════════════════════════════════════════════════════════════

async def get_customer_types():
    """获取客户类别列表"""
    settings = await _load_settings()
    types = settings.get("customer_types", DEFAULT_CUSTOMER_TYPES)
    return {"customerTypes": types}


async def add_customer_type(data: CustomerTypeCreate):
    """新增客户类别"""
    admin = await verify_admin_token(data.token)
    settings = await _load_settings()
    types = list(settings.get("customer_types", DEFAULT_CUSTOMER_TYPES))
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="类别名称不能为空")
    if name in types:
        raise HTTPException(status_code=400, detail="该类别已存在")
    types.append(name)
    await _save_settings("customer_types", types)
    await write_log(admin["username"], f"新增了客户类别「{name}」", "info")
    return {"status": "success", "customerTypes": types}


async def update_customer_type(type_index: int, data: CustomerTypeUpdate):
    """修改客户类别名称"""
    admin = await verify_admin_token(data.token)
    settings = await _load_settings()
    types = list(settings.get("customer_types", DEFAULT_CUSTOMER_TYPES))
    if type_index < 0 or type_index >= len(types):
        raise HTTPException(status_code=400, detail="无效的类别索引")
    old_name = types[type_index]
    new_name = data.name.strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="类别名称不能为空")
    if new_name != old_name and new_name in types:
        raise HTTPException(status_code=400, detail="该类别已存在")
    types[type_index] = new_name
    await _save_settings("customer_types", types)
    await write_log(admin["username"], f"将客户类别「{old_name}」修改为「{new_name}」", "info")
    return {"status": "success", "customerTypes": types}


async def delete_customer_type(type_index: int, token: str):
    """删除客户类别"""
    admin = await verify_admin_token(token)
    settings = await _load_settings()
    types = list(settings.get("customer_types", DEFAULT_CUSTOMER_TYPES))
    if type_index < 0 or type_index >= len(types):
        raise HTTPException(status_code=400, detail="无效的类别索引")
    removed = types.pop(type_index)
    await _save_settings("customer_types", types)
    await write_log(admin["username"], f"删除了客户类别「{removed}」", "warning")
    return {"status": "success", "customerTypes": types}
