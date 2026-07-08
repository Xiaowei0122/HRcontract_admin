"""
统一数据库连接模块
──────────────────────────────────────────────────
所有路由共享同一个 MongoDB 连接，切换环境只需修改下方
USE_PRODUCTION 这一个变量，或设置环境变量 MONGO_URL。
"""
import os
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

# 中国时区 UTC+8 — 所有模块统一使用此函数获取当前时间
CHINA_TZ = timezone(timedelta(hours=8))

def now_china() -> datetime:
    """返回中国时区的当前时间（UTC+8）"""
    return datetime.now(CHINA_TZ)

# ═══════════════════════════════════════════════════════════════
#  🔧  切换环境：改这一行即可  (False = 测试, True = 生产)
# ═══════════════════════════════════════════════════════════════
USE_PRODUCTION = True

# ── 环境对应的 MongoDB 连接串 ──────────────────────────────────
_TEST_URL = "mongodb://admin:Hr85550780@192.168.1.111:32768/?authSource=admin"
_PROD_URL = "mongodb://admin:Hr85550780@mongo-1:27017/?authSource=admin"

# 环境变量优先 > 开关变量
MONGO_URL = os.getenv("MONGO_URL", _PROD_URL if USE_PRODUCTION else _TEST_URL)

# ── 全局单例连接 ──────────────────────────────────────────────
client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URL)
database = client.HRcontract

print(f"📡 MongoDB 已连接: {'生产' if USE_PRODUCTION else '测试'}环境 → {MONGO_URL.split('@')[1].split('?')[0] if '@' in MONGO_URL else MONGO_URL}")


# ═══════════════════════════════════════════════════════════════
#  📦  MinIO 对象存储配置（与 MongoDB 共用 USE_PRODUCTION 开关）
# ═══════════════════════════════════════════════════════════════
_MINIO_TEST_URL = "192.168.1.111:9000"
_MINIO_PROD_URL = "minio-1:9000"
MINIO_URL = os.getenv("MINIO_URL", _MINIO_PROD_URL if USE_PRODUCTION else _MINIO_TEST_URL)
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "Hrbg@85550780")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "contracts")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

from minio import Minio
from minio.error import S3Error

minio_client = Minio(
    MINIO_URL,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)

# 确保 MinIO Bucket 存在（程序启动时自动创建）
try:
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)
        print(f"📦 MinIO Bucket '{MINIO_BUCKET}' 已创建")
    else:
        print(f"📦 MinIO Bucket '{MINIO_BUCKET}' 已就绪")
except Exception as e:
    print(f"⚠️ MinIO 连接失败: {e}")

print(f"📦 MinIO 对象存储已配置: {'生产' if USE_PRODUCTION else '测试'}环境 → {MINIO_URL}")


# ── 便捷函数：惰性获取集合 ────────────────────────────────────
def get_collection(name: str):
    """返回指定名称的集合对象"""
    return database.get_collection(name)


# ── 预定义集合（模块加载时创建，各路由直接 import 使用）───────
user_collection = database.get_collection("user")
contract_collection = database.get_collection("contract")
settings_collection = database.get_collection("settings")
logs_collection = database.get_collection("system_logs")


# ── 用户显示名称解析 ──────────────────────────────────────────
async def resolve_display_name(username: str) -> str:
    """将用户名解析为面向用户的显示名称（日志、操作人记录等共用）

    解析规则：
    - system       → 系统
    - admin        → 系统管理员
    - 其他管理员角色 → 管理员{真实姓名}
    - 普通用户     → {真实姓名}
    - 查不到的用户  → 返回原始 username

    支持同时按 username 和 realName 查找（因为前端可能传入 realName）。
    """
    if username == "system":
        return "系统"
    if username == "admin":
        return "系统管理员"
    try:
        # 优先按 username 查找，再按 realName 查找
        user_doc = await user_collection.find_one(
            {"$or": [{"username": username}, {"realName": username}]}
        )
        if user_doc:
            real_name = user_doc.get("realName", username)
            role = user_doc.get("role", "")
            if role == "admin" and user_doc.get("username") != "admin":
                return f"管理员{real_name}"
            return real_name
    except Exception:
        pass
    return username  # 解析失败则使用原始值


# ── 共享日志写入函数 ────────────────────────────────────────────
async def write_log(user: str, action: str, log_type: str = "warning") -> None:
    """写操作日志到 MongoDB system_logs 集合（所有路由共用）

    同时存储原始 username 和写入时解析的显示名称，确保历史日志不受后续角色变更影响。
    """
    display_name = await resolve_display_name(user)

    entry = {
        "time": now_china().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,               # 原始 username，用于旧日志兼容
        "displayName": display_name, # 写入时解析的显示名称，历史快照不会变
        "action": action,
        "type": log_type,
    }
    try:
        await logs_collection.insert_one(entry)
        print(f"📝 日志已写入: [{log_type}] {display_name} - {action}")
    except Exception as e:
        print(f"❌ 日志写入失败: {e}")
