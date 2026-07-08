"""
系统设置业务逻辑
包含：常量定义、Pydantic 模型、辅助函数、所有系统设置/日志/密码管理处理函数
原代码来源：routers/settings.py
"""
import asyncio
import re
from datetime import datetime, timedelta
from typing import Any, List

from fastapi import HTTPException
from pydantic import BaseModel

from database import settings_collection, logs_collection, user_collection, write_log, resolve_display_name, now_china
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

# ── 默认合同类型 ─────────────────────────────────────────────────
DEFAULT_CONTRACT_TYPES = ["销售合同", "采购合同", "服务合同"]

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
    "log_auto_cleanup": "日志自动清理",
    "allow_user_delete": "允许普通用户删除合同",
    "custom_fields": "自定义合同字段",
    "categories": "产品类别配置",
    "category_colors": "类别颜色映射",
    "signing_companies": "签署公司配置",
    "contract_types": "合同类型配置",
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
    "log_auto_cleanup": True,  # 日志自动清理开关：开启则按保留天数清理，关闭则永久保存
    # 权限控制
    "allow_user_delete": False,  # 默认禁止普通用户删除合同
    # 自定义字段与类别
    "custom_fields": [],         # 管理员新增的自定义合同字段
    "categories": DEFAULT_CATEGORIES,  # 产品类别列表
    "category_colors": {},       # 类别颜色映射（动态生成）
    "signing_companies": DEFAULT_SIGNING_COMPANIES,  # 签署公司列表
    "contract_types": DEFAULT_CONTRACT_TYPES,  # 合同类型列表
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
    old_password: str
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

class ContractTypeCreate(BaseModel):
    name: str
    token: str

class ContractTypeUpdate(BaseModel):
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


# ── 6. 操作日志（分页 + 分类筛选）────────────────────────────
async def get_logs(page: int = 1, pageSize: int = 20, logType: str = "all"):
    """分页获取系统操作日志，支持按分类筛选

    分类匹配逻辑与前端 getLogCategory 保持一致：
    - contract: action 含「合同」「附件」「导出」
    - user:     action 含「用户」「注册」「登录」「密码」「角色」「禁用」「启用」
    - settings: action 含「配置」「设置」「字段」「系统」
    - system:   user 为 system/系统，或不属于以上任何分类
    - all:      不筛选

    新日志（含 displayName 字段）直接使用写入时的历史快照；
    旧日志（无 displayName 字段）则按当前数据库状态解析显示名称。
    """
    try:
        # 构建分类筛选条件（严格复现前端 getLogCategory 优先级链）
        # 前端优先级: 1.system(user=system) > 2.contract > 3.user > 4.settings > 5.system(兜底)
        # 后面的类别要 $not 排除前面类别的关键词，避免交叉匹配
        if logType == "contract":
            query = {
                "user": {"$nin": ["system", "系统"]},
                "action": {"$regex": "合同|附件|导出"}
            }
        elif logType == "user":
            query = {
                "user": {"$nin": ["system", "系统"]},
                "$and": [
                    {"action": {"$not": {"$regex": "合同|附件|导出"}}},
                    {"action": {"$regex": "用户|注册|登录|密码|角色|禁用|启用"}},
                ]
            }
        elif logType == "settings":
            query = {
                "user": {"$nin": ["system", "系统"]},
                "$and": [
                    {"action": {"$not": {"$regex": "合同|附件|导出|用户|注册|登录|密码|角色|禁用|启用"}}},
                    {"action": {"$regex": "配置|设置|字段|系统"}},
                ]
            }
        elif logType == "system":
            query = {"$or": [
                {"user": {"$in": ["system", "系统"]}},
                {"$and": [
                    {"user": {"$nin": ["system", "系统"]}},
                    {"action": {"$not": {"$regex": "合同|附件|导出|用户|注册|登录|密码|角色|禁用|启用|配置|设置|字段|系统"}}}
                ]}
            ]}
        else:
            query = {}

        total = await logs_collection.count_documents(query)
        skip = (page - 1) * pageSize
        cursor = logs_collection.find(query).sort("time", -1).skip(skip).limit(pageSize)
        logs = await cursor.to_list(length=pageSize)
        # 去掉 _id，并处理显示名称
        for log in logs:
            log.pop("_id", None)
            # 优先使用写入时保存的历史显示名称（不受后续角色变更影响）
            if log.get("displayName"):
                log["user"] = log["displayName"]
            else:
                # 兼容旧日志（无 displayName 字段）：按当前数据库状态解析
                log["user"] = await resolve_display_name(log.get("user", ""))
            # 清理内部字段，不暴露给前端
            log.pop("displayName", None)
        return {"logs": logs, "total": total, "page": page, "pageSize": pageSize}
    except Exception as e:
        print(f"❌ 获取日志失败: {e}")
        return {"logs": [], "total": 0, "page": page, "pageSize": pageSize}


# ── 7. 修改管理员密码 ─────────────────────────────────────────
async def update_admin_password(data: PasswordUpdate):
    """管理员修改自己的密码（需验证原密码；子管理员不可修改超级管理员密码）"""
    import hashlib

    admin = await verify_admin_token(data.token)

    if not data.old_password:
        raise HTTPException(status_code=400, detail="请输入原密码")
    if not data.new_password or len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于6位")

    # 🔒 验证原密码是否正确
    old_hash = hashlib.sha256(data.old_password.encode()).hexdigest()
    if admin.get("password") != old_hash:
        raise HTTPException(status_code=401, detail="原密码错误")

    # 🔒 子管理员不可修改超级管理员 admin 的密码
    if admin["username"] != "admin":
        raise HTTPException(status_code=403, detail="仅超级管理员可修改管理员密码，子管理员请前往主页修改自己的密码")

    new_hash = hashlib.sha256(data.new_password.encode()).hexdigest()

    # 🔒 仅更新当前登录管理员的密码（不再批量更新所有管理员）
    result = await user_collection.update_one(
        {"username": admin["username"]},
        {"$set": {"password": new_hash, "is_default_password": False}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="未找到管理员账号")

    await write_log(admin["username"], "管理员密码已被修改", "warning")
    return {"status": "success", "message": "密码已修改，请妥善保管"}


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


# ═══════════════════════════════════════════════════════════════
#  12. 合同类型管理
# ═══════════════════════════════════════════════════════════════

async def get_contract_types():
    """获取合同类型列表"""
    settings = await _load_settings()
    types = settings.get("contract_types", DEFAULT_CONTRACT_TYPES)
    return {"contractTypes": types}


async def add_contract_type(data: ContractTypeCreate):
    """新增合同类型"""
    admin = await verify_admin_token(data.token)
    settings = await _load_settings()
    types = list(settings.get("contract_types", DEFAULT_CONTRACT_TYPES))
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="类型名称不能为空")
    if name in types:
        raise HTTPException(status_code=400, detail="该类型已存在")
    types.append(name)
    await _save_settings("contract_types", types)
    await write_log(admin["username"], f"新增了合同类型「{name}」", "info")
    return {"status": "success", "contractTypes": types}


async def update_contract_type(type_index: int, data: ContractTypeUpdate):
    """修改合同类型名称"""
    admin = await verify_admin_token(data.token)
    settings = await _load_settings()
    types = list(settings.get("contract_types", DEFAULT_CONTRACT_TYPES))
    if type_index < 0 or type_index >= len(types):
        raise HTTPException(status_code=400, detail="无效的类型索引")
    old_name = types[type_index]
    new_name = data.name.strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="类型名称不能为空")
    if new_name != old_name and new_name in types:
        raise HTTPException(status_code=400, detail="该类型已存在")
    types[type_index] = new_name
    await _save_settings("contract_types", types)
    await write_log(admin["username"], f"将合同类型「{old_name}」修改为「{new_name}」", "info")
    return {"status": "success", "contractTypes": types}


async def delete_contract_type(type_index: int, token: str):
    """删除合同类型"""
    admin = await verify_admin_token(token)
    settings = await _load_settings()
    types = list(settings.get("contract_types", DEFAULT_CONTRACT_TYPES))
    if type_index < 0 or type_index >= len(types):
        raise HTTPException(status_code=400, detail="无效的类型索引")
    removed = types.pop(type_index)
    await _save_settings("contract_types", types)
    await write_log(admin["username"], f"删除了合同类型「{removed}」", "warning")
    return {"status": "success", "contractTypes": types}


# ═══════════════════════════════════════════════════════════════
#  13. 日志自动清理（后台任务）
# ═══════════════════════════════════════════════════════════════

async def log_cleanup_loop():
    """后台任务：每隔 24 小时检查一次，删除超过保留天数的旧日志（受 log_auto_cleanup 开关控制）"""
    # 启动后先等 5 分钟，避免和初始化流程抢资源
    await asyncio.sleep(300)

    while True:
        try:
            settings = await _load_settings()
            auto_cleanup = settings.get("log_auto_cleanup", True)
            retention_days = settings.get("log_retention_days", 30)

            if auto_cleanup and retention_days > 0:
                cutoff_time = now_china() - timedelta(days=retention_days)
                cutoff_str = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")

                result = await logs_collection.delete_many(
                    {"time": {"$lt": cutoff_str}}
                )

                if result.deleted_count > 0:
                    print(f"🧹 日志自动清理: 已删除 {result.deleted_count} 条超过 {retention_days} 天的旧日志（早于 {cutoff_str}）")
                    await write_log("system", f"自动清理了 {result.deleted_count} 条超过 {retention_days} 天的旧日志", "info")
        except Exception as e:
            print(f"⚠️ 日志自动清理任务执行失败: {e}")

        # 每 24 小时检查一次
        await asyncio.sleep(86400)
