# 🏢 鸿瑞办公合同管理系统 - 智链合同

> 这是一款面向企业的**数字化合同全生命周期管理平台**，集合同编制、签署、归档、统计分析、文件管理于一体。

---

## 📋 项目概况

### 系统简介
**智链合同**是一个现代化的合同数字管理系统，为企业提供高效、安全的合同生命周期管理解决方案。系统分为**管理员模式**和**访客预览模式**两大用户类型，采用 MongoDB 数据库存储元数据，NAS 存储电子文件，满足不同场景的业务需求。

### 核心功能
- ✅ **用户认证体系** - 管理员登录、访客无密码进入、安全退出机制
- 📋 **合同信息管理** - 新增、编辑、删除、查询合同及其完整信息（数据持久化到 MongoDB）
- 📁 **文件管理** - 支持电子合同文件上传到 NAS、自动识别合同名称、在线预览下载
- 📊 **可视化分析** - 合同分类占比、金额统计、状态分布图表展示
- 🔍 **智能搜索与筛选** - 按关键词、状态、客户类型等多维度快速定位
- 🎯 **字段定制化显示** - 用户可根据需求选择显示/隐藏表格列
- 👥 **权限管理** - 访客模式仅可查看 2 条预览数据，无编辑权限
- 📑 **分页管理** - 支持灵活的翻页、页大小调整、排序
- 💾 **数据持久化** - 使用 MongoDB 存储所有合同信息和文件元数据
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
网络请求：fetch / axios
```

### 后端 (FastAPI + Python)
```
框架：FastAPI
异步支持：async/await + motor（异步 MongoDB 驱动）
数据模型：Pydantic BaseModel
跨域处理：CORSMiddleware
数据存储：MongoDB（192.168.1.111:32771）
文件存储：NAS 共享目录（\\192.168.1.111\contracts）
路由模块化：分离认证、合同、设置等功能
API 文档：
```

### 数据库
```
数据库系统：MongoDB
服务地址：mongodb://admin:Hr85550780@192.168.1.111:32771/?authSource=admin
数据库名：HRcontract
集合：contract（合同信息），user（用户）
自动初始化：首次运行时自动连接
```

### 文件存储
```
存储系统：群晖 NAS
存储地址：\\192.168.1.111\contracts
文件管理：后端负责文件读写，MongoDB 存储元数据
访问方式：Windows 网络共享（需挂载 NAS）
权限管理：NAS 用户级别权限控制
```

---

## 📂 项目结构

```
HRcontract_admin/
├── src/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── auth.py              # 认证路由（登录、登出、访客）
│   │   │   ├── contracts.py         # 合同路由（查询、上传、更新、删除、下载）
│   │   │   ├── settings.py          # 设置路由
│   │   │   └── __init__.py
│   │   ├── main.py                  # FastAPI 应用入口（MongoDB 连接）
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
- **MongoDB** 4.0+ 正常运行（192.168.1.111:32771）
- **NAS 挂载**：将群晖 NAS 共享目录挂载到本地（\\192.168.1.111\contracts）
- **现代浏览器**（Chrome/Firefox/Edge）

### 1️⃣ NAS 配置（重要！）

#### Windows 本地测试
```powershell
# 挂载 NAS 共享（用管理员账户）
net use \\192.168.1.111\contracts /user:admin your_password /persistent:yes

# 验证挂载是否成功
dir \\192.168.1.111\contracts
```

#### 部署到群晖 Docker
```bash
# 在群晖系统级别先挂载 NAS 共享
# 然后在 docker run 时挂载该目录到容器
docker run -v /volume1/contracts:/app/uploads your_image
```

### 2️⃣ 安装依赖

#### 前端依赖
```bash
npm install
```

#### 后端依赖
```bash
cd src/api
pip install -r requirements.txt
```

### 3️⃣ 启动应用

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

### 4️⃣ 验证系统运行

#### 访问应用
- **前端地址**：http://localhost:5173

#### 测试登录
- 管理员账号：`admin`，密码：`admin` 
- 或点击"访客模式直接进入"（不需要账号密码）

### 5️⃣ 开发构建
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
- **权限**：仅支持数据查询，无编辑/删除权限
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
| GET | `/api/contracts?role=admin` | 获取合同列表（admin 返回全部，其他返回预览 2 条） |
| POST | `/api/contracts/upload` | 新建合同并保存到 MongoDB + NAS |
| PUT | `/api/contracts/{db_id}` | 更新指定合同信息 |
| DELETE | `/api/contracts/{contract_id}` | 逻辑删除指定合同（标记为已删除） |
| GET | `/api/contracts/file/{file_name}` | 下载指定合同附件 |

---

## 📝 合同数据结构

### 请求体（POST /api/contracts/upload 或 PUT /api/contracts/{db_id}）
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
  "remark": "合同备注信息",
  "file": "[二进制文件流]"
}
```

### 响应体（成功返回）
```json
{
  "status": "success",
  "message": "同步成功",
  "contractId": "HT20260507153824844",
  "db_id": "66d3b4f8c9e4a123456789ab"
}
```

### MongoDB 文档结构
| 字段 | 类型 | 说明 |
|------|------|------|
| _id | ObjectId | MongoDB 主键（自动生成） |
| contractId | String | 合同唯一标识（业务键） |
| name | String | 合同名称 |
| contractNo | String | 合同编号 |
| contractType | String | 合同类型 |
| category | String | 产品类别 |
| customerType | String | 客户类别 |
| customer | String | 客户名称 |
| contactPerson | String | 联系人 |
| contactPhone | String | 联系电话 |
| servicePeriod | String | 服务期限 |
| signDate | String | 签订日期 |
| amount | Float | 合同金额（万元） |
| status | String | 合同状态 |
| remark | String | 备注 |
| fileUrl | String | 文件下载链接 `/api/contracts/file/{filename}` |
| fileName | String | 原始文件名 |
| filePath | String | NAS 实际文件路径 |
| createTime | String | 创建时间（YYYY-MM-DD HH:MM:SS） |
| updateTime | String | 更新时间（YYYY-MM-DD HH:MM:SS） |
| operator | String | 操作人员 |
| isDeleted | Boolean | 逻辑删除标记 |

---

## 📁 文件管理说明

### 上传流程
1. 前端选择文件 → 自动识别文件名填充"合同名称"
2. 前端发送 POST `/api/contracts/upload` 含 FormData（包括文件和合同信息）
3. 后端接收文件 → 保存到 NAS（`\\192.168.1.111\contracts\{timestamp}_{filename}` 已映射NAS内部路径）
4. 后端记录文件元数据到 MongoDB（fileUrl、fileName、filePath）
5. 前端列表中自动显示"下载"按钮

### 下载流程
1. 前端点击操作列"下载"按钮
2. 前端请求 GET `/api/contracts/file/{file_name}`
3. 后端从 NAS 读取文件 → 以附件形式返回给浏览器
4. 浏览器自动下载文件

### 文件存储位置
```
NAS 路径：\\192.168.1.111\contracts\ 已映射NAS内部路径
文件命名：{timestamp}_{original_filename}
示例：20260507153824_采购合同.docx
```

### 文件权限管理
- NAS 层级权限由群晖系统控制（创建专用用户账号）
- MongoDB 层级权限由后端认证控制
- 访客模式可查看但无法下载文件

---

## 🎨 主要页面功能

### 登录页面
- 现代化玻璃态设计
- 背景渐变装饰圆圈
- 两种登录模式选择（管理员/访客）

### 合同管理页面

#### 顶部统计卡片
- 合同总量
- 累计总金额
- 已签署合同数
- 待处理合同数

#### 分类占比分析
- 圆环图展示各产品类别合同数量占比
- 实时更新统计数据

#### 高级搜索
- 按合同名称/编号/客户名称搜索
- 按状态筛选

#### 字段显示管理
- 勾选/取消显示表格列
- 自定义表格展示内容

#### 合同管理表格
- 支持多列显示（名称、编号、金额、状态等）
- 操作列包含：
  - 📝 **编辑**：修改合同信息
  - 📥 **下载**：下载附件（无附件时禁用显示灰化）
  - 🗑️ **删除**：逻辑删除合同

#### 翻页功能
- 支持自定义页大小（5、10、20、50）
- 实时显示当前数据总数
- 支持直接跳页

---

## 🔄 业务流程

### 用户操作流程
```
登录/访客进入 → 查看合同列表 → 搜索/筛选 → 
(管理员) 新增/编辑合同 → 上传附件 → 保存 → 
(管理员/访客) 下载附件 → 查看统计分析 → 
(管理员) 删除合同 → 退出系统
```

### 新建合同流程
```
前端：点击"录入新合同" → 打开编辑弹窗 → 
      拖拽/点击选择文件 → 自动识别合同名称 → 
      填写其他信息 → 点击"保存提交"
      ↓
后端：验证必填字段 → 将文件保存到 NAS → 
      记录元数据到 MongoDB → 返回成功响应
      ↓
前端：关闭弹窗 → 刷新表格 → 显示新增的合同
```

### 编辑合同流程
```
前端：点击操作列"编辑" → 打开编辑弹窗（预填充数据） → 
      修改信息/替换附件 → 点击"保存提交"
      ↓
后端：验证字段 → 可选保存新附件到 NAS → 
      更新 MongoDB 记录（不修改 createTime） → 返回成功响应
      ↓
前端：关闭弹窗 → 刷新表格 → 显示更新的合同
```

### 删除合同流程
```
前端：点击操作列"删除" → 弹出确认对话框 → 点击"确定"
      ↓
后端：将 isDeleted 字段标记为 True → 保存到 MongoDB
      ↓
前端：自动刷新列表 → 已删除合同不显示（逻辑删除）
```

### 下载附件流程
```
前端：点击操作列"下载"按钮（无附件时禁用）
      ↓
后端：读取 NAS 文件 → 以附件形式返回
      ↓
浏览器：自动下载文件到本地
```

---

## 🔗 前后端交互说明

### 跨域配置
- 后端已配置允许所有来源的请求（开发环境）
- 生产环境建议在 `src/api/main.py` 中修改 `allow_origins` 为具体的前端地址

### 数据流向
```
前端（Vue）← 网络请求 → 后端（FastAPI）
                            ↓
                      MongoDB 数据库（元数据）
                            ↓
                      NAS 共享目录（文件数据）
```

### 环境变量配置
```python
# 后端 contracts.py 中的 NAS 路径配置
UPLOAD_DIR = Path(os.getenv("CONTRACT_UPLOAD_DIR", r"\\192.168.1.111\contracts"))
```

部署时可通过设置环境变量修改路径：
```powershell
# Windows
set CONTRACT_UPLOAD_DIR=\\192.168.1.111\contracts

# Linux/Docker
export CONTRACT_UPLOAD_DIR=/mnt/nas/contracts
```

---

## 🐛 常见问题

### Q: 后端提示"Permission Denied"无法访问 NAS
**A:** 
1. 确认 NAS 共享目录已挂载到本地
2. 确认挂载时使用的账户有读写权限
3. 运行：`net use \\192.168.1.111\contracts /user:admin password /persistent:yes`

### Q: 文件上传后看不到下载按钮
**A:**
1. 检查 fileUrl 是否为空
2. 查看后端日志是否有文件保存错误
3. 确认 NAS 路径可访问

### Q: 删除合同后还能看到
**A:**
这是正常的逻辑删除行为，合同数据仍在数据库中，只是标记为已删除。如需彻底删除，需要在 MongoDB 中手动清理。

### Q: 翻页后数据显示不对
**A:**
刷新页面或重新搜索/筛选。分页基于过滤后的数据集。

---

## 📞 支持

如有问题，请查阅：
- 后端 API 文档：http://localhost:9080/docs
- 代码注释和类型提示
- 浏览器开发者工具（F12）查看网络请求

---

**最后更新**：2026 年 5 月 7 日


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


## 📌 版本更新与bug修复日志

### v1.2.3-beta (2026-06-02)
**💡 核心架构升级与性能优化**
- **[新增] 真·后端分页懒加载**：重构 `FastAPI + MongoDB` 吞吐逻辑，采用底层 `.skip().limit()` 动态切片，消除后期全量加载撑爆内存的隐患。
- **[数据解耦] 大盘统计独立化**：引入 `allContractsData` 全量数据源。顶部的看板、四大统计卡片以及饼图文字比对全盘大盘，下列表格独立走懒加载。
- **[体验优化] 稳定图表重绘动画**：重写 `updateChart` 逻辑，增加新旧数据特征值判定拦截。在非增删操作（如日常翻页、切换条数）时，圆环图表及占比动画不改变，解决数据统计问题。

**🐛 严重 Bug 修复 (Bug Fixes)**
- **[修复] 清理多余标签报错**：剔除 HTML 模板中冗余的空表格标签；修正因移除前端切片变量引发的底部 `initPageData` 作用域未定义引用错误（`ReferenceError`）。

*上次更新时间：2026年06月02日*