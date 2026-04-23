from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from .contracts import MOCK_CONTRACTS  # 导入合同数据模拟

# 创建路由对象
router = APIRouter(
    prefix="/api",  #所有认证相关接口都以 /api 开头，保持与主文件一致
    tags=["认证管理"]
)

# --- 数据模型保持原状 ---
class LoginData(BaseModel):
    username: str
    password: str

class LogoutData(BaseModel):
    token: str

# --- 1. 登录接口 ---
@router.post("/login")
async def login(data: LoginData):
    if data.username == "admin" and data.password == "123456":
        return {
            "status": "success",
            "userRole": "admin",
            "isGuest": False,
            "token": "admin-session-token-001",
            "source": "Python FastAPI Is Back send"
        }
    raise HTTPException(status_code=401, detail="账号或密码错误")

# --- 2. 退出登录接口 ---
@router.post("/logout")
async def logout(data: LogoutData):
    if data.token == "admin-session-token-001":
        print(f"📢 后端收到登出请求：Token {data.token} 已失效")
        return {"status": "success", "message": "已安全退出系统"}
    else:
        raise HTTPException(status_code=401, detail="无效的 token")

# --- 3. 访客模式接口 ---
@router.get("/guest")
async def guest_mode():
    return {
        "status": "success",
        "userRole": "guest",
        "isGuest": True,
        "message": "访客模式：仅可预览数据，无法进行编辑或管理操作",
        "previewData": MOCK_CONTRACTS[:2]  # 仅返回前2条数据作为预览
    }