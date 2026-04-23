from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# 导入 auth 路由模块
from routers import auth , contracts, settings

app = FastAPI(title="鸿瑞办公后端系统")

# --- 全局跨域配置 (保持原状) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 【核心】挂载分离开的认证模块 ---
app.include_router(auth.router)
app.include_router(contracts.router)
app.include_router(settings.router)

# --- 统一启动入口 ---
if __name__ == "__main__":
    import uvicorn
    # 统一通过 9080 端口启动，所有挂载的路由都会共享此服务
    uvicorn.run(app, host="127.0.0.1", port=9080)