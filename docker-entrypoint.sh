#!/bin/sh

# 启动 FastAPI 后端（后台运行）
cd /app/api
python -m uvicorn main:app --host 127.0.0.1 --port 9080 &

# 启动 nginx（前台运行，保持容器存活）
nginx -g 'daemon off;'
