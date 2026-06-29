"""
系统设置路由（薄层 — 仅负责路由注册和参数解析，业务逻辑在 services/settings_service.py）
"""
from fastapi import APIRouter, Query
from services.settings_service import (
    ConfigUpdate, FieldsUpdate, PasswordUpdate,
    CustomFieldCreate, CustomFieldUpdate,
    CategoryCreate, CategoryUpdate,
    SigningCompanyCreate, SigningCompanyUpdate,
    CustomerTypeCreate, CustomerTypeUpdate,
    init_settings,
    get_all_settings, get_available_fields, get_default_fields,
    set_default_fields, update_setting, get_logs, update_admin_password,
    get_field_definitions, add_custom_field, update_custom_field, delete_custom_field,
    get_categories, add_category, update_category, delete_category,
    get_signing_companies, add_signing_company, update_signing_company, delete_signing_company,
    get_customer_types, add_customer_type, update_customer_type, delete_customer_type,
)

router = APIRouter(prefix="/api/settings", tags=["系统设置"])

# ── 1. 获取全部配置 ───────────────────────────────────────────
@router.get("/")
async def all_settings():
    return await get_all_settings()

# ── 2. 获取可用字段列表（基础 + 自定义）─────────────────────
@router.get("/fields")
async def available_fields():
    return await get_available_fields()

# ── 3. 获取默认可见字段 ───────────────────────────────────────
@router.get("/default-fields")
async def default_fields():
    return await get_default_fields()

# ── 4. 设置默认可见字段 ───────────────────────────────────────
@router.post("/default-fields")
async def set_fields(data: FieldsUpdate):
    return await set_default_fields(data)

# ── 5. 更新单个配置项 ─────────────────────────────────────────
@router.post("/update")
async def update_config(item: ConfigUpdate):
    return await update_setting(item)

# ── 6. 操作日志（分页）───────────────────────────────────────
@router.get("/logs")
async def logs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
):
    return await get_logs(page=page, pageSize=pageSize)

# ── 7. 修改管理员密码 ─────────────────────────────────────────
@router.post("/update_password")
async def change_pwd(data: PasswordUpdate):
    return await update_admin_password(data)

# ═══════════════════════════════════════════════════════════════
#  8. 自定义字段 CRUD
# ═══════════════════════════════════════════════════════════════

@router.get("/field-definitions")
async def field_defs():
    """获取所有字段定义（基础 + 自定义），供字段管理页使用"""
    return await get_field_definitions()

@router.post("/custom-fields")
async def create_custom_field(data: CustomFieldCreate):
    """新增自定义合同字段"""
    return await add_custom_field(data)

@router.put("/custom-fields/{field_key}")
async def edit_custom_field(field_key: str, data: CustomFieldUpdate):
    """修改自定义字段"""
    return await update_custom_field(field_key, data)

@router.delete("/custom-fields/{field_key}")
async def remove_custom_field(field_key: str, token: str = Query(...)):
    """删除自定义字段"""
    return await delete_custom_field(field_key, token)

# ═══════════════════════════════════════════════════════════════
#  9. 产品类别管理
# ═══════════════════════════════════════════════════════════════

@router.get("/categories")
async def cat_list():
    """获取产品类别列表及颜色映射"""
    return await get_categories()

@router.post("/categories")
async def cat_create(data: CategoryCreate):
    """新增产品类别"""
    return await add_category(data)

@router.put("/categories/{cat_index}")
async def cat_edit(cat_index: int, data: CategoryUpdate):
    """修改产品类别"""
    return await update_category(cat_index, data)

@router.delete("/categories/{cat_index}")
async def cat_remove(cat_index: int, token: str = Query(...)):
    """删除产品类别"""
    return await delete_category(cat_index, token)

# ═══════════════════════════════════════════════════════════════
#  10. 签署公司管理
# ═══════════════════════════════════════════════════════════════

@router.get("/signing-companies")
async def signing_company_list():
    """获取签署公司列表"""
    return await get_signing_companies()

@router.post("/signing-companies")
async def signing_company_create(data: SigningCompanyCreate):
    """新增签署公司"""
    return await add_signing_company(data)

@router.put("/signing-companies/{company_index}")
async def signing_company_edit(company_index: int, data: SigningCompanyUpdate):
    """修改签署公司"""
    return await update_signing_company(company_index, data)

@router.delete("/signing-companies/{company_index}")
async def signing_company_remove(company_index: int, token: str = Query(...)):
    """删除签署公司"""
    return await delete_signing_company(company_index, token)


# ═══════════════════════════════════════════════════════════════
#  11. 客户类别管理
# ═══════════════════════════════════════════════════════════════

@router.get("/customer-types")
async def customer_type_list():
    """获取客户类别列表"""
    return await get_customer_types()

@router.post("/customer-types")
async def customer_type_create(data: CustomerTypeCreate):
    """新增客户类别"""
    return await add_customer_type(data)

@router.put("/customer-types/{type_index}")
async def customer_type_edit(type_index: int, data: CustomerTypeUpdate):
    """修改客户类别"""
    return await update_customer_type(type_index, data)

@router.delete("/customer-types/{type_index}")
async def customer_type_remove(type_index: int, token: str = Query(...)):
    """删除客户类别"""
    return await delete_customer_type(type_index, token)
