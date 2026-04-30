import site

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import secrets
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from .contracts import MOCK_CONTRACTS  # 导入合同数据模拟

# 配置数据库连接类型
MONGO_DETAILS = "mongodb://admin:Hr85550780@192.168.1.111:32768/?authSource=admin"
client = AsyncIOMotorClient(MONGO_DETAILS)
# 假设数据库名为 contract_db，用户集合名为 users
database = client.HRcontract
user_collection = database.get_collection("user")
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
    username: str

# --- 1. 登录接口 ---
@router.post("/login")
async def login(data: LoginData):
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

    # --- 业务逻辑：更新最后登录时间 ---
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # --- 2. 随机 Token验证 ---
    # 生成一个 32 字节的随机字符串，安全等级极高
    dynamic_token = f"hr_token_{secrets.token_urlsafe(32)}"

    await user_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"lastLogin": current_time, "current_token": dynamic_token}} # 存入 current_token
    )
    # --- 返回结果 ---
    return {
        "status": "success",
        "userRole": user.get("role", "admin"), # 从数据库获取角色
        "realName": user.get("realName", "管理员"), # 从数据库获取真实姓名
        "isGuest": False,
        "token": dynamic_token, # 使用生成的动态 Token
        "lastLogin": current_time
    }

# --- 2. 退出登录接口 ---
@router.post("/logout")
async def logout(data: LogoutData):
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