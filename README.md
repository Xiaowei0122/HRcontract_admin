# 🏢 鸿瑞办公合同管理系统 - 智链合同

> 这是一款面向企业的**数字化合同全生命周期管理平台**，集合同编制、签署、归档、统计分析于一体。

---

## 📋 项目概况

### 系统简介
**智链合同**是一个现代化的合同数字管理系统，为企业提供高效、安全的合同生命周期管理解决方案。系统分为**管理员模式**和**访客预览模式**两大用户类型，满足不同场景的业务需求。

### 核心功能
- ✅ **用户认证体系** - 管理员登录、访客无密码进入、安全退出机制
- 📋 **合同信息管理** - 新增、编辑、查询合同及其完整信息（数据持久化到SQLite）
- 📊 **可视化分析** - 合同分类占比、金额统计、状态分布图表展示
- 🔍 **智能搜索与筛选** - 按关键词、状态、客户类型等多维度快速定位
- 🎯 **字段定制化显示** - 用户可根据需求选择显示/隐藏表格列
- 📁 **文件上传识别** - 支持电子合同文件上传，自动识别合同名称
- 👥 **权限管理** - 访客模式仅可查看2条预览数据，无编辑权限
- 💾 **数据持久化** - 使用SQLite数据库存储所有合同信息
- 📱 **响应式界面** - 现代化 UI 设计，适配多种屏幕尺寸

---

## 🛠️ 技术架构

### 前端 (Vue 3 + Vite)
```
框架：Vue 3 with Composition API (Script Setup)
构建工具：Vite
UI 组件库：Element Plus
路由管理：Vue Router
图表库：Chart.js
状态管理：localStorage（会话状态）
```

### 后端 (FastAPI + Python)
```
框架：FastAPI
异步支持：async/await
数据模型：Pydantic BaseModel
跨域处理：CORSMiddleware
数据存储：SQLite 3
路由模块化：分离认证、合同、设置等功能
API 文档：自动生成 Swagger/OpenAPI（访问 http://localhost:9080/docs）
```

### 数据库
```
引擎：SQLite（无需额外部署）
数据库文件：src/api/data/contracts.db
表名：contracts
自动初始化：首次运行时自动创建表和初始化数据
```

---

## 📂 项目结构

```
HRcontract_admin/
├── src/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── auth.py              # 认证路由（登录、登出、访客）
│   │   │   ├── contracts.py         # 合同路由（查询、上传、更新）+ SQLite数据库
│   │   │   ├── settings.py          # 设置路由
│   │   │   └── __init__.py
│   │   ├── data/
│   │   │   └── contracts.db         # SQLite数据库（自动创建）
│   │   ├── main.py                  # FastAPI 应用入口
│   │   └── requirements.txt          # Python 依赖清单
│   ├── views/
│   │   ├── login.vue                # 登录页面（管理员/访客模式）
│   │   └── ContractManager.vue      # 合同管理主界面
│   ├── router/
│   │   └── index.js                 # 路由配置
│   ├── assets/                      # 静态资源
│   ├── App.vue                      # 根组件
│   ├── main.js                      # Vue 应用入口
│   └── style.css                    # 全局样式
├── public/                          # 公共静态文件
├── index.html                       # HTML 入口
├── vite.config.js                   # Vite 配置
├── package.json                     # Node.js 依赖
└── README.md                        # 项目说明文档
```

---

## 🚀 快速开始

### 前置环境要求
- **Node.js** 16+ 和 npm 8+
- **Python** 3.8+ 和 pip
- **现代浏览器**（Chrome/Firefox/Edge）

### 1️⃣ 安装依赖

#### 前端依赖
```bash
npm install
```

#### 后端依赖
```bash
cd src/api
pip install -r requirements.txt
```

### 2️⃣ 启动应用

#### 启动后端（FastAPI）
```bash
cd src/api
python main.py
# 或使用 uvicorn 直接运行
uvicorn main:app --host 127.0.0.1 --port 9080 --reload
```

#### 启动前端（Vue 3 + Vite）
```bash
npm run dev
# 默认访问：http://localhost:5173
```

### 3️⃣ 验证系统运行

#### 访问应用
- **前端地址**：http://localhost:5173
- **后端 Swagger 文档**：http://localhost:9080/docs
- **后端 ReDoc 文档**：http://localhost:9080/redoc

#### 测试登录
- 管理员账号：`admin`，密码：`123456`
- 或点击"访客模式直接进入"（不需要账号密码）

### 4️⃣ 开发构建
```bash
npm run build    # 生产环境打包
npm run preview  # 预览打包结果
```

---

## 🔐 用户认证说明

### 管理员登录
- **默认账号**：`admin`
- **默认密码**：`123456`
- **权限**：完全的增删改查权限

### 访客模式
- **无需账号密码**，点击"访客模式直接进入"
- **权限**：仅支持数据查询和报表下载，无编辑权限
- **显示标识**：页面右上角显示"访客预览模式"标签

---

## 📊 核心 API 接口

### 认证管理
| 方法 | 路由 | 描述 |
|------|------|------|
| POST | `/api/login` | 管理员登录（账号: admin, 密码: 123456） |
| POST | `/api/logout` | 安全退出（需传入 token） |
| GET | `/api/guest` | 访客模式直接进入 |

### 合同管理
| 方法 | 路由 | 描述 |
|------|------|------|
| GET | `/api/contracts?role=admin` | 获取合同列表（admin 返回全部，其他返回预览2条） |
| POST | `/api/contracts/upload` | 新建合同并保存到数据库 |
| PUT | `/api/contracts/{id}` | 更新指定ID合同信息 |

---

## 📝 合同数据结构

### 请求体（POST /api/contracts/upload 或 PUT /api/contracts/{id}）
```json
{
  "name": "合同名称",
  "contractNo": "HT-2026-JSJ-001",
  "contractType": "采购合同",
  "category": "计算机设备",
  "customerType": "高校",
  "customer": "华南理工大学",
  "contactPerson": "张教授",
  "contactPhone": "13800000000",
  "servicePeriod": "2026-01-01 ~ 2027-12-31",
  "signDate": "2026-03-12",
  "amount": 128.50,
  "status": "已签署",
  "remark": "合同备注信息"
}
```

### 响应体（成功返回）
```json
{
  "status": "success",
  "message": "合同上传成功",
  "contract": {
    "id": 1,
    "name": "合同名称",
    "contractNo": "HT-2026-JSJ-001",
    "contractType": "采购合同",
    "category": "计算机设备",
    "customerType": "高校",
    "customer": "华南理工大学",
    "contactPerson": "张教授",
    "contactPhone": "13800000000",
    "servicePeriod": "2026-01-01 ~ 2027-12-31",
    "signDate": "2026-03-12",
    "amount": 128.50,
    "status": "已签署",
    "remark": "合同备注信息"
  }
}
```

### 数据库表结构
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | TEXT | 合同名称 |
| contractNo | TEXT | 合同编号 |
| contractType | TEXT | 合同类型 |
| category | TEXT | 产品类别 |
| customerType | TEXT | 客户类别 |
| customer | TEXT | 客户名称 |
| contactPerson | TEXT | 联系人 |
| contactPhone | TEXT | 联系电话 |
| servicePeriod | TEXT | 服务期限 |
| signDate | TEXT | 签订日期 |
| amount | REAL | 合同金额 |
| status | TEXT | 合同状态 |
| remark | TEXT | 备注 |

---

## 🎨 主要页面预览

### 登录页面
- 现代化玻璃态设计
- 背景渐变装饰圆圈
- 两种登录模式选择

### 合同管理页面
- 实时统计卡片（合同总量、金额、已签署等）
- 合同分类占比分析圆环图
- 高级搜索和多字段筛选
- 动态列显示/隐藏功能
- 弹窗式新增/编辑表单
- 文件上传和自动识别

---

## 🔄 业务流程

### 用户操作流程
```
登录/访客进入 → 查看合同数据 → 筛选/搜索 → 
(管理员) 编辑/新增 → 填写表单 → 后端保存到数据库 → 
查看统计分析 → 退出系统
```

### 数据同步流程
```
前端启动 → 获取当前用户角色 → 发送GET /api/contracts?role=xxx → 
后端查询SQLite数据库 → 返回JSON数据 → 前端渲染表格
```

### 新建/编辑合同流程
```
用户点击"录入新合同" → 打开弹窗 → 填写表单信息 → 点击"保存提交" →
前端序列化表单数据 → 
新建：POST /api/contracts/upload 
编辑：PUT /api/contracts/{id}
→ 后端验证并保存到数据库 → 返回保存结果 → 前端更新表格 → 关闭弹窗
```

---

## � 前后端交互说明

### 跨域配置
- 后端已配置允许所有来源的请求（开发环境）
- 生产环境建议在 `src/api/main.py` 中修改 `allow_origins` 为具体的前端地址

### 数据流向
```
前端（Vue） ← 网络请求 → 后端（FastAPI）
                              ↓
                        SQLite 数据库
```

### 环境变量
- 前端和后端通过硬编码地址通信：`http://localhost:9080`
- 如需改为其他端口，需同时修改前后端代码

---

## 🛡️ 安全特性

- ✅ **Token 验证**：退出时传入 Token 确保合法性
- ✅ **CORS 跨域配置**：仅允许指定域名访问（生产环境需配置）
- ✅ **访问权限隔离**：访客模式自动禁用编辑按钮
- ✅ **本地存储加密**：敏感信息存储在 localStorage 中
- ✅ **SQL 注入防护**：使用参数化查询防止 SQL 注入
- ⚠️ **备份建议**：生产环境定期备份 `src/api/data/contracts.db`

---

## 📦 依赖清单

### 前端 (package.json)
```
vue@^3.x
element-plus
chart.js
vue-router@4.x
```

### 后端 (requirements.txt)
```
fastapi
uvicorn
pydantic
python-multipart
```

### 数据库
- SQLite 3（Python 内置，无需额外安装）

---

## 🤝 常见问题

**Q: 后端服务无法连接怎么办？**
A: 确保 FastAPI 服务已在 `http://localhost:9080` 启动，检查终端是否有错误日志。

**Q: 访客模式和管理员模式的区别是什么？**
A: 访客模式仅可查看前2条数据预览，"新建合同"按钮被禁用，无法进行编辑操作。

**Q: 如何修改默认登录凭证？**
A: 编辑 `src/api/routers/auth.py` 中 `login()` 函数的用户名和密码验证逻辑。

**Q: 数据保存到哪里了？**
A: 保存到 `src/api/data/contracts.db`（SQLite 数据库），会自动创建。

**Q: 如何重置数据库？**
A: 删除 `src/api/data/contracts.db` 文件，重启后端服务会自动重新初始化。

**Q: 支持多用户同时编辑吗？**
A: 目前支持，但无并发控制机制，建议生产环境加入锁机制或版本控制。

**Q: 前端数据卡顿或不更新？**
A: 检查浏览器控制台是否有网络请求错误，确认后端返回的数据格式是否正确。

---

## 📄 许可证

© 2026 鸿瑞办公 · 数字化工程部

---

## 📞 支持与反馈

如有问题或建议，欢迎联系数字化工程团队。
