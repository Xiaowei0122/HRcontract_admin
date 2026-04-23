from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/api/settings", tags=["系统设置"])

# 模拟数据库存储系统配置
# 这里的初始值会同步给前端的 configForm
SYSTEM_CONFIG = {
    "guest_data_limit": 2,       # 访客可见合同条数
    "maintenance_mode": False,   # 系统维护模式
    "allow_guest_upload": False  # 是否允许访客录入
}

# 模拟操作日志存储
SYSTEM_LOGS = [
    {"time": "2026-04-23 18:00:00", "user": "admin", "action": "系统初始化完成", "type": "info"}
]

# 定义更新配置的请求模型
class ConfigUpdate(BaseModel):
    key: str
    value: Any

@router.get("/")
async def get_all_settings():
    """获取所有系统配置"""
    return SYSTEM_CONFIG

@router.post("/update")
async def update_setting(item: ConfigUpdate):
    """动态更新配置，无需重启后端或修改代码"""
    if item.key not in SYSTEM_CONFIG:
        raise HTTPException(status_code=400, detail="未定义的配置项")
    
    # 更新内存中的配置
    SYSTEM_CONFIG[item.key] = item.value
    
    # 记录日志
    from datetime import datetime
    log_entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": "admin",
        "action": f"修改配置 {item.key} 为 {item.value}",
        "type": "warning"
    }
    SYSTEM_LOGS.insert(0, log_entry)
    
    print(f"⚙️ 系统配置更新: {item.key} -> {item.value}")
    return {"status": "success", "message": f"已更新 {item.key}"}

@router.get("/logs")
async def get_logs():
    """获取系统操作日志"""
    return SYSTEM_LOGS[:20] # 返回最近20条日志