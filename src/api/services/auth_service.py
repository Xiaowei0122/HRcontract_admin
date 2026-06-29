"""
认证管理业务逻辑
包含：Pydantic 模型、辅助函数、所有认证/用户管理相关的异步处理函数
原代码来源：routers/auth.py
"""
import secrets
import hashlib
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel

from database import user_collection, contract_collection, write_log
from services.shared import get_guest_data_limit

# ═══════════════════════════════════════════════════════════════
#  常量
# ═══════════════════════════════════════════════════════════════
# 默认管理员密码的 SHA256 哈希（明文: admin）
DEFAULT_ADMIN_PASSWORD_HASH = hashlib.sha256("admin".encode()).hexdigest()

# ═══════════════════════════════════════════════════════════════
#  Pydantic 数据模型（原封不动从 routers/auth.py 提取）
# ═══════════════════════════════════════════════════════════════
class LoginData(BaseModel):
    username: str
    password: str

class LogoutData(BaseModel):
    token: Optional[str] = None
    username: Optional[str] = None

class RegisterData(BaseModel):
    username: str
    password: str
    realName: str
    email: str = ""
    phone: str = ""
    department: str = ""

class ApproveUserData(BaseModel):
    username: str
    action: str       # "approve" | "reject"
    token: str

class UserListQueryData(BaseModel):
    token: str
    status: str = ""  # "pending" | "active" | "rejected"

class DeleteUserData(BaseModel):
    username: str
    token: str

class ToggleUserStatusData(BaseModel):
    username: str
    action: str       # "disable" | "enable"
    token: str

class SetUserRoleData(BaseModel):
    username: str
    role: str         # "admin" | "user" | "viewer"
    token: str

class ChangePasswordData(BaseModel):
    username: str
    oldPassword: str
    newPassword: str

# ═══════════════════════════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════════════════════════

async def init_admin_user():
    """检查数据库中是否存在管理员账号，不存在则创建默认管理员；存在则补全缺失字段"""
    admin_user = await user_collection.find_one({"role": "admin"})
    if not admin_user:
        await user_collection.insert_one({
            "username": "admin",
            "password": DEFAULT_ADMIN_PASSWORD_HASH,
            "role": "admin",
            "status": "active",
            "realName": "管理员",
            "email": "",
            "phone": "",
            "department": "数字化工程部",
            "registerTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "lastLogin": None,
            "current_token": None,
            "is_default_password": True
        })
        print("✅ 已创建默认管理员账号 admin/admin，请登录后修改密码")
    else:
        # 兼容旧数据：补全缺失的字段
        missing = {}
        if "status" not in admin_user:
            missing["status"] = "active"
        if "registerTime" not in admin_user:
            missing["registerTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "department" not in admin_user:
            missing["department"] = "数字化工程部"
        if missing:
            await user_collection.update_one(
                {"_id": admin_user["_id"]},
                {"$set": missing}
            )
            print(f"✅ 已补全管理员账号缺失字段: {list(missing.keys())}")


async def verify_admin_token(token: str):
    """校验 token 是否属于活跃管理员，否则抛出 403"""
    admin = await user_collection.find_one({
        "current_token": token,
        "role": "admin"
    })
    if not admin:
        raise HTTPException(status_code=403, detail="无管理员权限或令牌已过期")
    # 兼容旧数据：无 status 字段视为 active
    status = admin.get("status", "active")
    if status not in ("active",):
        raise HTTPException(status_code=403, detail="管理员账号已被禁用")
    return admin


# ═══════════════════════════════════════════════════════════════
#  业务逻辑函数（对应各 API 端点，原封不动提取）
# ═══════════════════════════════════════════════════════════════

# --- 1. 登录 ---
async def login_user(data: LoginData):
    """
    用户登录处理：
    1. 校验用户名和密码
    2. 登录成功后自动更新最后登录时间
    """
    # 在数据库中查找匹配的记录
    user = await user_collection.find_one({
        "username": data.username.strip(),
        "password": data.password.strip()
    })

    if not user:
        # 如果找不到匹配项，返回 401 错误
        raise HTTPException(status_code=401, detail="账号或密码错误")

    # --- 账号状态校验 ---
    user_status = user.get("status", "active")  # 兼容旧数据，默认 active
    if user_status == "pending":
        raise HTTPException(status_code=403, detail="您的账号正在等待管理员审核，审核通过后方可登录")
    if user_status == "rejected":
        raise HTTPException(status_code=403, detail="您的账号注册申请已被拒绝，请联系管理员")
    if user_status == "disabled":
        raise HTTPException(status_code=403, detail="您的账号已被管理员禁用，请联系管理员")

    # --- 业务逻辑：更新最后登录时间 ---
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # --- 2. 随机 Token验证 ---
    # 生成一个 32 字节的随机字符串，安全等级极高
    dynamic_token = f"hr_token_{secrets.token_urlsafe(32)}"

    await user_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"lastLogin": current_time, "current_token": dynamic_token}} # 存入 current_token
    )
    # 记日志
    await write_log(data.username.strip(), "登录了系统", "info")

    # --- 返回结果 ---
    return {
        "status": "success",
        "userRole": user.get("role", "admin"), # 从数据库获取角色
        "realName": user.get("realName", "管理员"), # 从数据库获取真实姓名
        "isGuest": False,
        "token": dynamic_token, # 使用生成的动态 Token
        "lastLogin": current_time,
        "isDefaultPassword": user.get("is_default_password", False)
    }


# --- 2. 退出登录 ---
async def logout_user(data: LogoutData):
    # 访客模式退出：无用户名和 token，直接返回成功
    if not data.username:
        return {"status": "success", "message": "访客已退出"}

    # 1. 改进查询条件：直接根据用户名清除其 Token
    result = await user_collection.update_one(
        {"username": data.username},
        {"$set": {"current_token": None}}
    )

    if result.modified_count > 0:
        print(f"✅ 成功：用户 {data.username} 的 Token 已销毁")
    else:
        print(f"⚠️ 警告：未找到用户 {data.username} 或 Token 已为空")

    return {"status": "success", "message": "已从服务器安全登出"}


# --- 3. 修改密码 ---
async def change_user_password(data: ChangePasswordData):
    user = await user_collection.find_one({
        "username": data.username.strip(),
        "password": data.oldPassword.strip()
    })
    if not user:
        raise HTTPException(status_code=401, detail="原密码错误")

    await user_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"password": data.newPassword.strip(), "is_default_password": False}}
    )
    # 记日志
    await write_log(data.username.strip(), "修改了自己的登录密码", "warning")
    return {"status": "success", "message": "密码修改成功"}


# --- 4. 访客模式 ---
async def serve_guest_mode():
    try:
        # 1. 实时从 MongoDB 获取前 2 条未删除的合同数据
        # 使用 find({"isDeleted": False}) 确保不显示已删除的数据
        guest_limit = await get_guest_data_limit()
        cursor = contract_collection.find({"isDeleted": False}).sort("createTime", -1)
        preview_docs = await cursor.to_list(length=guest_limit)

        # 2. 格式化数据（处理 ObjectId 序列化问题）
        formatted_data = []
        for doc in preview_docs:
            doc["_id"] = str(doc["_id"]) # 将 MongoDB 对象转为前端可识别的字符串
            formatted_data.append(doc)

        return {
            "status": "success",
            "userRole": "guest",
            "isGuest": True,
            "message": "访客模式：仅可预览数据，无法进行编辑或管理操作",
            "previewData": formatted_data  # 现在这里是来自 NAS 数据库的真数据
        }
    except Exception as e:
        # 增加错误处理，防止数据库连不上时整个接口挂掉
        return {
            "status": "error",
            "message": f"无法获取预览数据: {str(e)}",
            "previewData": []
        }


# --- 5. 用户注册 ---
async def register_user(data: RegisterData):
    """自助注册，status=pending，需管理员审核后方可登录"""
    username = data.username.strip()
    password = data.password.strip()
    real_name = data.realName.strip()

    if not username or not password or not real_name:
        raise HTTPException(status_code=400, detail="用户名、密码和真实姓名为必填项")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于6位")

    existing = await user_collection.find_one({"username": username})
    if existing:
        raise HTTPException(status_code=409, detail="该用户名已被注册")

    await user_collection.insert_one({
        "username": username,
        "password": password,  # 前端已 SHA256 哈希
        "role": "user",
        "status": "pending",
        "realName": real_name,
        "email": data.email.strip() if data.email else "",
        "phone": data.phone.strip() if data.phone else "",
        "department": data.department.strip() if data.department else "",
        "registerTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lastLogin": None,
        "current_token": None,
        "is_default_password": False
    })

    # 记日志
    await write_log(data.username.strip(), f"新用户「{data.username.strip()}」提交了注册申请，等待管理员审核", "info")

    return {"status": "success", "message": "注册成功，请等待管理员审核通过后登录"}


# --- 6. 管理员用户列表 ---
async def list_users(data: UserListQueryData):
    """管理员查看用户列表，可按状态筛选"""
    await verify_admin_token(data.token)

    query = {}
    if data.status:
        query["status"] = data.status

    cursor = user_collection.find(query).sort("registerTime", -1)
    users = await cursor.to_list(length=200)

    result = []
    for u in users:
        result.append({
            "username": u.get("username", ""),
            "role": u.get("role", "user"),
            "status": u.get("status", "active"),
            "realName": u.get("realName", ""),
            "email": u.get("email", ""),
            "phone": u.get("phone", ""),
            "department": u.get("department", ""),
            "registerTime": u.get("registerTime", ""),
            "lastLogin": u.get("lastLogin", ""),
            "createTime": u.get("registerTime", ""),  # 兼容字段：创建时间
            "isDisable": u.get("status") == "disabled",  # 是否禁用
            "currentToken": u.get("current_token") or "",  # 当前会话令牌
        })

    return {"status": "success", "users": result}


# --- 7. 管理员审批用户 ---
async def approve_user(data: ApproveUserData):
    """管理员审批通过或拒绝用户注册"""
    await verify_admin_token(data.token)

    if data.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action 必须为 approve 或 reject")

    target = await user_collection.find_one({"username": data.username.strip()})
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.get("role") == "admin":
        raise HTTPException(status_code=400, detail="不能审批管理员账号")
    if target.get("status") != "pending":
        raise HTTPException(status_code=400, detail="该用户当前状态不允许此操作")

    new_status = "active" if data.action == "approve" else "rejected"
    await user_collection.update_one(
        {"username": data.username.strip()},
        {"$set": {"status": new_status}}
    )

    label = "通过" if data.action == "approve" else "拒绝"
    # 记日志
    target_realname = target.get("realName", "") or data.username
    await write_log("admin", f"{label}了用户「{target_realname}」的注册申请", "warning")
    return {"status": "success", "message": f"用户 {data.username} 的注册申请已{label}"}


# --- 8. 管理员删除用户 ---
async def admin_delete_user(data: DeleteUserData):
    """管理员删除用户（不可删除管理员）"""
    await verify_admin_token(data.token)

    target = await user_collection.find_one({"username": data.username.strip()})
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.get("role") == "admin":
        raise HTTPException(status_code=400, detail="不能删除管理员账号")

    await user_collection.delete_one({"username": data.username.strip()})
    # 记日志
    target_realname = target.get("realName", "") or data.username
    await write_log("admin", f"删除了用户「{target_realname}」", "warning")
    return {"status": "success", "message": f"用户 {data.username} 已删除"}


# --- 9. 管理员禁用/启用用户 ---
async def toggle_user_status(data: ToggleUserStatusData):
    """管理员禁用或启用用户（不可操作管理员）"""
    await verify_admin_token(data.token)

    if data.action not in ("disable", "enable"):
        raise HTTPException(status_code=400, detail="action 必须为 disable 或 enable")

    target = await user_collection.find_one({"username": data.username.strip()})
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.get("role") == "admin":
        raise HTTPException(status_code=400, detail="不能禁用/启用管理员账号")

    new_status = "disabled" if data.action == "disable" else "active"
    await user_collection.update_one(
        {"username": data.username.strip()},
        {"$set": {"status": new_status}}
    )

    label = "禁用" if data.action == "disable" else "启用"
    # 记日志
    target_realname = target.get("realName", "") or data.username
    await write_log("admin", f"{label}了用户「{target_realname}」", "warning")
    return {"status": "success", "message": f"用户 {data.username} 已{label}"}


# --- 10. 管理员设置用户角色 ---
async def set_user_role(data: SetUserRoleData):
    """管理员修改用户角色（不可修改自己的角色）"""
    admin = await verify_admin_token(data.token)

    if data.role not in ("admin", "user", "viewer"):
        raise HTTPException(status_code=400, detail="role 必须为 admin、user 或 viewer")

    # 不能修改当前登录管理员自己的角色
    if data.username.strip() == "admin":
        raise HTTPException(status_code=400, detail="不能修改超级管理员 admin 的角色")
    if admin["username"] == data.username.strip():
        raise HTTPException(status_code=400, detail="不能修改自己的角色")

    target = await user_collection.find_one({"username": data.username.strip()})
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    await user_collection.update_one(
        {"username": data.username.strip()},
        {"$set": {"role": data.role}}
    )

    role_label_map = {"admin": "管理员", "user": "普通用户", "viewer": "查看者"}
    role_label = role_label_map.get(data.role, data.role)
    # 记日志
    target_realname = target.get("realName", "") or data.username
    await write_log("admin", f"将用户「{target_realname}」的角色设置为「{role_label}」", "warning")
    return {"status": "success", "message": f"用户 {data.username} 的角色已设为{role_label}"}
