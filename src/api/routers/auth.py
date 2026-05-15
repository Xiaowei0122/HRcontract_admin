import os
import site

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import secrets
import hashlib
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# 配置数据库连接类型
MONGO_DETAILS = os.getenv("MONGO_URL", "mongodb://admin:Hr85550780@192.168.1.111:32768/?authSource=admin")
client = AsyncIOMotorClient(MONGO_DETAILS)
# 假设数据库名为 contract_db，用户集合名为 users
database = client.HRcontract
user_collection = database.get_collection("user")
# 创建路由对象
router = APIRouter(
    prefix="/api",  #所有认证相关接口都以 /api 开头，保持与主文件一致
    tags=["认证管理"]
)
contract_collection = database.get_collection("contract")

# 默认管理员密码的 SHA256 哈希（明文: admin）
DEFAULT_ADMIN_PASSWORD_HASH = hashlib.sha256("admin".encode()).hexdigest()

async def init_admin_user():
    """检查数据库中是否存在管理员账号，不存在则创建默认管理员"""
    admin_user = await user_collection.find_one({"role": "admin"})
    if not admin_user:
        await user_collection.insert_one({
            "username": "admin",
            "password": DEFAULT_ADMIN_PASSWORD_HASH,
            "role": "admin",
            "realName": "管理员",
            "lastLogin": None,
            "current_token": None,
            "is_default_password": True
        })
        print("✅ 已创建默认管理员账号 admin/admin，请登录后修改密码")
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
        "lastLogin": current_time,
        "isDefaultPassword": user.get("is_default_password", False)
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

# --- 3. 修改密码接口 ---
class ChangePasswordData(BaseModel):
    username: str
    oldPassword: str
    newPassword: str

@router.post("/change-password")
async def change_password(data: ChangePasswordData):
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
    return {"status": "success", "message": "密码修改成功"}

# --- 4. 访客模式接口 ---
@router.get("/guest")
async def guest_mode():
    try:
        # 1. 实时从 MongoDB 获取前 2 条未删除的合同数据
        # 使用 find({"isDeleted": False}) 确保不显示已删除的数据
        cursor = contract_collection.find({"isDeleted": False}).sort("createTime", -1)
        preview_docs = await cursor.to_list(length=2)
        
        # 2. 格式化数据（处理 ObjectId 序列化问题）[cite: 1]
        formatted_data = []
        for doc in preview_docs:
            doc["_id"] = str(doc["_id"]) # 将 MongoDB 对象转为前端可识别的字符串[cite: 1]
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