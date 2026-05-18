# ============ 阶段1: 构建前端 ============
FROM node:20-alpine AS frontend-build

WORKDIR /app

COPY package.json ./
RUN npm install

COPY index.html vite.config.js ./
COPY public/ ./public/
COPY src/ ./src/

# 将前端中硬编码的 API 地址替换为相对路径，以配合 nginx 反向代理
RUN find src -name '*.vue' -exec sed -i 's|http://localhost:9080||g' {} +

RUN npm run build

# ============ 阶段2: 最终镜像 ============
FROM python:3.11-slim

# 安装 nginx 和必要系统依赖（opencv/paddleocr 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
WORKDIR /app/api

# 先转换 requirements.txt 编码（源文件为 UTF-16LE）
COPY src/api/requirements.txt ./requirements_raw.txt
RUN python -c "open('requirements.txt','w').write(open('requirements_raw.txt','rb').read().decode('utf-16'))" \
    && rm requirements_raw.txt \
    && sed -i 's/paddlepaddle==3.3.1/paddlepaddle==3.2.2/' requirements.txt \
    && sed -i '/^PyQt5/d; /^PyQt6/d; /^pyinstaller/d; /^pefile/d; /^altgraph/d; /^pywin32/d' requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY src/api/main.py ./
COPY src/api/routers/ ./routers/
COPY src/api/data/ ./data/

# 复制前端构建产物
COPY --from=frontend-build /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf
# 删除默认站点配置以防冲突
RUN rm -f /etc/nginx/sites-enabled/default

# 复制启动脚本
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
