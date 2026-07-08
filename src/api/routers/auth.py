"""
认证管理路由（薄层 — 仅负责路由注册和参数解析，业务逻辑在 services/auth_service.py）
"""
from fastapi import APIRouter
from services.auth_service import (
    LoginData, LogoutData, RegisterData, ApproveUserData,
    UserListQueryData, DeleteUserData, ToggleUserStatusData,
    SetUserRoleData, UpdateUserData, ResetPasswordData, ChangePasswordData, VerifyTokenData,
    login_user, logout_user, change_user_password,
    serve_guest_mode, register_user, list_users,
    approve_user, admin_delete_user, toggle_user_status, set_user_role,
    update_user_info, reset_user_password, verify_user_token,
)

# 创建路由对象
router = APIRouter(
    prefix="/api",  # 所有认证相关接口都以 /api 开头，保持与主文件一致
    tags=["认证管理"]
)

# --- 1. 登录接口 ---
@router.post("/login")
async def login(data: LoginData):
    return await login_user(data)

# --- 2. 退出登录接口 ---
@router.post("/logout")
async def logout(data: LogoutData):
    return await logout_user(data)

# --- 3. 修改密码接口 ---
@router.post("/change-password")
async def change_password(data: ChangePasswordData):
    return await change_user_password(data)

# --- 4. 访客模式接口 ---
@router.get("/guest")
async def guest_mode():
    return await serve_guest_mode()

# --- 5. 用户注册接口 ---
@router.post("/register")
async def register(data: RegisterData):
    return await register_user(data)

# --- 6. 管理员用户列表接口 ---
@router.post("/admin/users")
async def list_users_route(data: UserListQueryData):
    return await list_users(data)

# --- 7. 管理员审批用户接口 ---
@router.post("/admin/approve-user")
async def approve_user_route(data: ApproveUserData):
    return await approve_user(data)

# --- 8. 管理员删除用户接口 ---
@router.post("/admin/delete-user")
async def delete_user_route(data: DeleteUserData):
    return await admin_delete_user(data)

# --- 9. 管理员禁用/启用用户接口 ---
@router.post("/admin/toggle-user-status")
async def toggle_user_status_route(data: ToggleUserStatusData):
    return await toggle_user_status(data)

# --- 10. 管理员设置用户角色接口 ---
@router.post("/admin/set-user-role")
async def set_user_role_route(data: SetUserRoleData):
    return await set_user_role(data)

# --- 11. 管理员编辑用户信息接口 ---
@router.post("/admin/update-user")
async def update_user_route(data: UpdateUserData):
    return await update_user_info(data)

# --- 12. 管理员重置用户密码接口 ---
@router.post("/admin/reset-password")
async def reset_password_route(data: ResetPasswordData):
    return await reset_user_password(data)

# --- 13. 验证 Token 有效性接口 ---
@router.post("/verify-token")
async def verify_token_route(data: VerifyTokenData):
    return await verify_user_token(data)
