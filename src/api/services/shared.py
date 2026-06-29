"""
共享工具函数 — 多个 service 模块复用
"""
from database import settings_collection


async def get_guest_data_limit() -> int:
    """从 settings 集合读取 guest_data_limit，读取失败则返回默认值 2"""
    try:
        doc = await settings_collection.find_one({"_id": "system_config"})
        if doc and "guest_data_limit" in doc:
            return int(doc["guest_data_limit"])
    except Exception:
        pass
    return 2
