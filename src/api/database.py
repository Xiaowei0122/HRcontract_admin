"""
统一数据库连接模块
──────────────────────────────────────────────────
所有路由共享同一个 MongoDB 连接，切换环境只需修改下方
USE_PRODUCTION 这一个变量，或设置环境变量 MONGO_URL。
"""
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

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


# ── 便捷函数：惰性获取集合 ────────────────────────────────────
def get_collection(name: str):
    """返回指定名称的集合对象"""
    return database.get_collection(name)


# ── 预定义集合（模块加载时创建，各路由直接 import 使用）───────
user_collection = database.get_collection("user")
contract_collection = database.get_collection("contract")
settings_collection = database.get_collection("settings")
logs_collection = database.get_collection("system_logs")


# ── 共享日志写入函数 ────────────────────────────────────────────
async def write_log(user: str, action: str, log_type: str = "warning") -> None:
    """写操作日志到 MongoDB system_logs 集合（所有路由共用）"""
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action,
        "type": log_type,
    }
    try:
        await logs_collection.insert_one(entry)
        print(f"📝 日志已写入: [{log_type}] {user} - {action}")
    except Exception as e:
        print(f"❌ 日志写入失败: {e}")
