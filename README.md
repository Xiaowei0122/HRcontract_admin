# 🏢 鸿瑞办公合同管理系统 — 智链合同 `v1.4.6`

> 一款面向企业的**数字化合同全生命周期管理平台**，集合同编制、签署、归档、统计分析、文件管理于一体。

---

## 📋 项目概况

### 系统简介
**智链合同**是一个现代化的合同数字管理系统，为企业提供高效、安全的合同生命周期管理解决方案。系统支持**管理员**、**普通用户**和**访客**三种角色，采用 **MongoDB** 数据库存储元数据，**NAS** 存储电子文件，满足不同场景的业务需求。

### 核心功能
- ✅ **用户认证体系** — 管理员登录、用户注册审核、访客无密码进入、安全退出、密码修改
- 📋 **合同信息管理** — 新增、编辑、删除、查询合同（数据持久化到 MongoDB）
- 📁 **文件管理** — 支持电子合同文件上传到 NAS、自动识别合同名称、在线预览/下载、批量打包下载
- 📊 **可视化分析** — 合同分类占比饼图、金额统计、状态分布、大额高亮预警
- 🔍 **智能搜索与筛选** — 按关键词、分类、状态、客户类型、金额区间等 7 个维度组合筛选
- 🎯 **字段定制化** — 用户可自定义显示/隐藏表格列，管理员可新增自定义字段
- 👥 **角色权限** — 三级角色体系（admin / user / viewer），支持禁用/启用、角色变更
- 📑 **真分页懒加载** — MongoDB 后端分页，支持灵活翻页与页大小调整
- 🔧 **系统配置面板** — 维护模式、访客数据量、大额阈值、合同ID前缀等 14+ 项动态配置
- 📝 **操作日志** — 全操作覆盖（登录/注册/合同CRUD/用户管理/配置变更），持久化到 MongoDB
- 📱 **响应式界面** — 现代化 UI 设计，适配多种屏幕尺寸

---

## 🛠️ 技术架构

### 前端 (Vue 3 + Vite)
```
框架：Vue 3.5 (Composition API + `<script setup>`)
构建工具：Vite 8.0
UI 组件库：Element Plus 2.13
路由管理：Vue Router 4.6
图表库：Chart.js 4.5 + vue-chartjs 5.3
加密库：CryptoJS 4.2
Excel 导出：xlsx 0.18
HTTP 客户端：axios 1.16 + fetch
```

### 后端 (FastAPI + Python)
```
框架：FastAPI（异步）
数据库驱动：motor（异步 MongoDB 驱动）
数据校验：Pydantic v2
跨域处理：CORSMiddleware（全局）
架构模式：Router（薄层）+ Service（业务逻辑）+ Database（共享连接）
```

### 数据库
```
数据库系统：MongoDB
测试环境：mongodb://admin:***@192.168.1.111:32768/?authSource=admin
生产环境：mongodb://admin:***@mongo-1:27017/?authSource=admin
数据库名：HRcontract
集合：
  - user         用户账户
  - contract     合同信息
  - settings     系统配置
  - system_logs  操作日志
自动初始化：首次运行时自动创建管理员账号和默认配置
```

### 文件存储
```
存储系统：群晖 NAS
测试环境：\\192.168.1.111\HR_NAS\contracts
生产环境：/contracts（Docker 挂载）
文件管理：后端负责文件读写，MongoDB 存储元数据
权限管理：NAS 用户级别权限控制
```

---

## 📂 项目结构

```
HRcontract_admin/
├── index.html                           # HTML 入口
├── vite.config.js                       # Vite 配置
├── package.json                         # Node.js 依赖
├── jsconfig.json                        # JS/TS 项目配置（IDE 支持）
│
├── src/
│   ├── main.js                          # Vue 应用入口
│   ├── App.vue                          # 根组件
│   ├── style.css                        # 全局样式
│   │
│   ├── views/                           # 页面视图组件
│   │   ├── login.vue                    # 登录页面（管理员/访客模式 + 修改密码弹窗）
│   │   ├── Register.vue                 # 用户自助注册页面
│   │   ├── ContractManager.vue          # 合同管理主界面（看板 + 饼图 + 筛选 + 表格 + 编辑弹窗）
│   │   └── SystemSettings.vue           # 系统设置页面（参数配置 / 用户管理 / 操作日志）
│   │
│   ├── router/                          # 前端路由
│   │   ├── index.js                     # 路由配置（含路由守卫）
│   │   ├── auth/
│   │   │   ├── login.js                 # 登录/退出/访客逻辑 composable
│   │   │   └── register.js              # 注册逻辑 composable
│   │   ├── contract/
│   │   │   └── contractManager.js       # 合同管理业务逻辑 composable
│   │   └── settings/
│   │       └── systemSettings.js        # 系统设置业务逻辑 composable
│   │
│   ├── api/                             # FastAPI 后端
│   │   ├── main.py                      # 应用入口（启动初始化、路由挂载、CORS）
│   │   ├── database.py                  # 共享 MongoDB 连接 + 日志写入
│   │   ├── requirements.txt             # Python 依赖清单
│   │   ├── routers/                     # 路由层（薄层 — 参数解析 + 路由注册）
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                  # 认证路由（10 个端点）
│   │   │   ├── contracts.py             # 合同路由（7 个端点）
│   │   │   └── settings.py              # 设置路由（12 个端点）
│   │   └── services/                    # 业务逻辑层（Pydantic 模型 + 业务函数）
│   │       ├── __init__.py
│   │       ├── shared.py                # 共享工具（访客数据量读取）
│   │       ├── auth_service.py          # 认证业务逻辑
│   │       ├── contract_service.py      # 合同 CRUD + 文件处理
│   │       └── settings_service.py      # 系统配置 + 自定义字段 + 类别/公司管理
│   │
│   └── assets/                          # 静态资源（logo、图标）
│       ├── hero.png
│       ├── vite.svg
│       └── vue.svg
│
└── public/                              # 公共静态文件
```

---

## 🚀 快速开始

### 前置环境要求
- **Node.js** 16+ 和 npm 8+
- **Python** 3.8+ 和 pip
- **MongoDB** 4.0+ 正常运行
- **NAS 挂载**：将群晖 NAS 共享目录挂载到本地（或 Docker 映射）
- **现代浏览器**（Chrome / Firefox / Edge）

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

### 2️⃣ 配置环境

#### MongoDB 连接
编辑 `src/api/database.py`，切换 `USE_PRODUCTION` 变量：
```python
USE_PRODUCTION = False   # 测试环境（192.168.1.111:32768）
USE_PRODUCTION = True    # 生产环境（Docker mongo-1:27017）
```
或通过环境变量覆盖：`export MONGO_URL="mongodb://..."`

#### NAS 文件存储
```powershell
# 测试环境Windows 挂载 NAS
net use \\192.168.1.111\HR_NAS\contracts /user:admin password /persistent:yes

# 或通过环境变量指定
export CONTRACT_UPLOAD_DIR="/mnt/nas/contracts"
```

### 3️⃣ 启动应用

#### 启动后端（FastAPI）
```bash
cd src/api
python main.py
# 后端运行在 http://localhost:9080
# Swagger 文档：http://localhost:9080/docs
```

#### 启动前端（Vite）
```bash
npm run dev
# 前端运行在 http://localhost:5173
```

### 4️⃣ 验证系统

- **前端地址**：http://localhost:5173
- **后端 Swagger**：http://localhost:9080/docs
- **管理员登录**：`admin` / `admin`
- **访客模式**：点击"访客模式直接进入"

### 5️⃣ 生产构建
```bash
npm run build        # 生产环境打包
npm run preview      # 预览打包结果
```

---

## 🔐 角色权限体系

| 角色 | 查看 | 新增 | 编辑 | 删除 | 下载 | 系统设置 |
|------|------|------|------|------|------|----------|
| admin（管理员） | ✅ 全部 | ✅ | ✅ | ✅ | ✅ | ✅ |
| user（普通用户） | ✅ 全部 | ✅ | ✅ | ✅(可配置) | ✅ | ❌ |
| viewer（查看者） | ✅ 全部 | ❌ | ❌ | ❌ | ✅ | ❌ |
| guest（访客） | ✅ N条(可配置) | ❌ | ❌ | ❌ | ✅ | ❌ |

**注册审核流程**：用户自助注册 → 状态 `pending` → 管理员审核通过 → 状态 `active`

---

## 🔄 业务流程

### 用户操作流程
```
注册/登录/访客 → 合同列表 → 搜索筛选 →
  (有权限) 新增/编辑合同 → 上传附件 → 保存 →
  (有权限) 批量/单个下载 → 查看统计 →
  (管理员) 系统设置 → 用户管理 → 退出
```

### 新建合同流程
```
前端：点击"录入新合同" → 打开编辑弹窗 →
      选择/拖拽文件 → 自动识别合同名称 →
      填写表单（含自定义字段） → 保存提交
       ↓
后端：验证必填字段 → 文件保存到 NAS →
      元数据写入 MongoDB → 记录操作日志 → 返回成功
       ↓
前端：关闭弹窗 → 刷新列表 → 显示新合同
```

### 数据流向
```
前端（Vue 3） ← HTTP/fetch → 后端（FastAPI）
                                  ↓  Router（薄层）
                                  ↓  Service（业务逻辑）
                                  ↓  Database（共享连接）
                            MongoDB 数据库（元数据）
                            NAS 共享目录（文件数据）
```

---

## 📊 系统配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `guest_data_limit` | integer | 2 | 访客可预览的合同条数 |
| `maintenance_mode` | boolean | false | 系统维护模式 |
| `allow_guest_upload` | boolean | false | 访客上传权限 |
| `guest_full_access` | boolean | false | 访客查看全部合同 |
| `show_dashboard_charts` | boolean | true | 看板图表显示 |
| `big_amount_threshold` | number | 100 | 大额合同预警阈值（万元） |
| `default_visible_fields` | array | [...] | 合同列表默认显示字段 |
| `max_upload_size_mb` | number | 50 | 文件上传大小限制 |
| `allowed_file_types` | array | [...] | 允许上传的文件类型 |
| `session_timeout_minutes` | number | 480 | 会话超时时间 |
| `contract_id_prefix` | string | "HT" | 合同ID前缀 |
| `log_retention_days` | number | 90 | 日志保留天数 |
| `allow_user_delete` | boolean | false | 允许普通用户删除合同 |

---

## 🔗 前后端交互说明

### 跨域配置
后端已配置全局 CORS，允许所有来源。生产环境建议在 `main.py` 中修改 `allow_origins` 为具体的前端地址。

### API 接口总览

| 模块 | 端点数 | 说明 |
|------|--------|------|
| 认证管理 | 10 | 登录、退出、注册、密码修改、访客、用户管理 |
| 合同管理 | 7 | 看板统计、列表分页、上传、更新、删除、单个/批量下载 |
| 系统设置 | 12 | 配置读写、字段定义、自定义字段CRUD、类别CRUD、签署公司CRUD、日志 |

> 完整 API 接口文档见 [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

## 🛡️ 安全特性

- ✅ **Token 验证**：动态 32 位随机令牌，会话级别管理
- ✅ **密码加密**：SHA256 哈希存储，默认密码检测与强制修改提醒
- ✅ **角色隔离**：前端路由守卫 + 后端 Token 校验双重保护
- ✅ **逻辑删除**：合同数据标记删除保留审计记录
- ✅ **操作日志**：全操作持久化到 MongoDB，支持追溯
- ✅ **超级管理员保护**：admin 账号不可被删除、禁用、修改角色
- ✅ **CORS 跨域配置**：可限制允许的源域名
- ✅ **注册审核**：新用户需管理员审核通过方可登录

---

## 🐛 常见问题

### Q: 后端提示无法连接 MongoDB
**A:** 检查 `database.py` 中 `MONGO_URL` 是否正确，确认 MongoDB 服务正在运行，网络策略是否放行端口。

### Q: 文件上传后看不到下载按钮
**A:** 检查 `fileUrl` 是否为空，确认 NAS 路径可访问，查看后端日志是否有文件保存错误。

### Q: 访客模式看到的合同数量不对
**A:** 数量由系统配置 `guest_data_limit` 动态控制，管理员可在"系统设置 → 参数配置"中调整。

### Q: 注册后无法登录
**A:** 新注册用户状态为 `pending`，需等待管理员在"系统设置 → 用户管理"中审核通过。

### Q: 删除合同后还能看到
**A:** 这是逻辑删除，数据保留在数据库，仅标记 `isDeleted: true`。如需物理删除，需在 MongoDB 中手动清理。

---

## 📞 支持

- 后端 Swagger 文档：http://localhost:9080/docs
- IDE 项目配置：[jsconfig.json](jsconfig.json)
- 浏览器开发者工具（F12）查看网络请求与前端日志

---

## 📦 依赖清单

### 前端 (package.json)
```
vue@^3.5.32
element-plus@^2.13.7
vue-router@^4.6.4
chart.js@^4.5.1, vue-chartjs@^5.3.3
crypto-js@^4.2.0, xlsx@^0.18.5
axios@^1.16.0
@vitejs/plugin-vue@^6.0.5, vite@^8.0.4
```

### 后端 (requirements.txt)
```
fastapi, uvicorn
motor (异步 MongoDB 驱动)
pydantic
python-multipart
```

---

## 📄 许可证

© 2026 鸿瑞办公 · 数字化工程部

---

## 📌 版本更新与 Bug 修复日志

### v1.4.7 (2026-06-29)
**👤 用户名称统一显示 & 日志即时刷新**

- **[新增] 操作人名称统一解析机制**
  - 新增 `resolve_display_name()` 函数（`database.py`），自动将原始标识符解析为面向用户的显示名称
  - **内置 admin** → 显示为「系统管理员」；**其他管理员** → 显示为「管理员XXX」；**普通用户** → 显示真实姓名
  - `write_log()` 内部自动调用解析，所有日志写入时统一转为显示名称，无需调用方手动处理

- **[修复] 合同操作人字段对齐**
  - 表头从「操作人」改为「**最后操作人**」
  - 合同创建/编辑/删除时，`operator` 字段自动解析为显示名称后存入 MongoDB
  - 删除、批量下载接口新增 `operator` 参数，记录实际操作人身份

- **[修复] 管理员操作日志溯源**
  - `auth_service.py` / `settings_service.py` 全部 CRUD 函数改为通过 `verify_admin_token()` 获取实际操作管理员
  - 日志中不再出现硬编码 `admin`，而是显示具体是哪个管理员执行的操作

- **[修复] 操作日志 Tab 渲染延迟**
  - 新增 `watch(activeTab)` 监听，切换到「操作日志」tab 时立即调用 `fetchLogs()` 同步刷新

- **[新增] 主页系统版本信息**
  - `ContractManager.vue` 底端新增版本信息栏：`© 2026 鸿瑞办公 · 数字化工程部 系统版本：v1.4.7`

- **影响文件**：`database.py`、`contract_service.py`、`settings_service.py`、`auth_service.py`、`contracts.py`、`settings.py`、`contractManager.js`、`systemSettings.js`、`ContractManager.vue`

---

### v1.4.6 (2026-06-29)
**🔧 开发体验优化 & 框架兼容性修复**

- **[新增] TypeScript/JS 项目配置文件**
  - 新建 `jsconfig.json`，明确设置 `checkJs: false`，消除 IDE 对 JS 文件的隐式类型检查警告（114 条）
  - 配置 `moduleResolution: "bundler"` 与 Vite 构建保持一致

- **[兼容性修复] Vue 3.5 + Volar 适配**
  - 将 `onMounted` 从 composable (`systemSettings.js`) 移至组件 (`SystemSettings.vue`) 顶层调用
  - 登录页使用 `useTemplateRef('loginRef')` 替代已废弃的 `ref(null)` 模式

- **[BUG FIX] 后端认证逻辑修复（3 项）**
  - `LogoutData` 中 `token` 和 `username` 改为 Optional，支持访客退出不传参
  - `logout_user` 增加访客判断：无用户名时直接返回成功，不查询数据库
  - `set_user_role` 增加超级管理员保护：禁止修改 `admin` 账号的角色

- **影响文件**：`jsconfig.json`(新)、`systemSettings.js`、`SystemSettings.vue`、`login.vue`、`auth_service.py`、`auth.py`

---

### v1.4.5 (2026-06-27)
**🔧 数据库连接统一 & 前后端联动修复**

- **[架构重构] MongoDB 连接统一管理**
  - 新建 `database.py` 共享连接模块，auth / contracts / settings 三个路由共用同一连接
  - 通过 `USE_PRODUCTION = True/False` 一键切换测试/生产环境
  - 支持环境变量 `MONGO_URL` 覆盖默认连接串

- **[新增] 登录注册界面**
  - 新增 `Register.vue` 用户自助注册页面
  - 注册后状态为 `pending`，管理员审核通过后方可登录
  - 管理员可在系统设置中审批、拒绝、删除用户

- **[BUG FIX] 系统设置与合同管理联动修复（5 项）**
  - **默认显示字段同步**：管理员修改默认字段后，所有用户打开合同列表自动同步
  - **访客数据限制动态读取**：`guest_data_limit` 从 MongoDB settings 实时读取，不再硬编码为 2
  - **统计图表显隐**：`show_dashboard_charts` 配置实时控制看板图表显示
  - **大额合同高亮**：`big_amount_threshold` 超过阈值的合同金额标红加粗
  - **合同编号前缀**：`contract_id_prefix` 动态控制新建合同编号前缀

- **[BUG FIX] 操作日志持久化 & 全面覆盖**
  - 操作日志从 localStorage 改为实时写入 MongoDB `system_logs` 集合
  - `write_log()` 提取到 `database.py` 共享模块，三个路由统一调用
  - **新增日志覆盖**：合同创建/编辑/删除/批量下载 + 用户登录/注册/审批/删除/禁用/权限变更
  - 系统启动、配置变更、密码修改、字段更新全部记录

- **[新增] 维护模式**：开启后禁用合同录入/编辑/删除按钮，页面显示维护模式标签

- **影响文件**：`database.py`(新)、`settings.py`、`contracts.py`、`auth.py`、`ContractManager.vue`、`SystemSettings.vue`

---

### v1.2.3-beta (2026-06-02)
**💡 核心架构升级与性能优化**

- **[新增] 真·后端分页懒加载**：重构 FastAPI + MongoDB 吞吐逻辑，采用底层 `.skip().limit()` 动态切片
- **[数据解耦] 大盘统计独立化**：引入全量数据源，与表格分页数据完全解耦
- **[体验优化] 稳定图表重绘动画**：重写 Chart.js 更新逻辑，避免翻页时图表被重新绘制

**🐛 严重 Bug 修复**
- **[修复] 清理多余标签报错**：剔除 HTML 模板中冗余的空表格标签，修正 `initPageData` 引用错误
- **[修复] 跨域问题**：后端全局 CORS 配置缺失导致的前端请求拦截

---

### 📝 2026 年 6 月 5 日
- ✅ **【BUG FIX】搜索结果不显示问题**
  - **根本原因**：`displayedTableData` 计算属性对后端已过滤的数据进行了二次前端过滤
  - **修复方案**：移除前端重复过滤逻辑，直接返回后端过滤后的数据

---

### 📝 历史版本摘要

| 日期 | 版本 | 关键变更 |
|------|------|----------|
| 2026-06-13 | — | 修复文件下载和批量下载错误；修复文件存储异常，指定 NAS 固定存储路径 |
| 2026-06-12 | — | 修复看板渲染逻辑，看板数据轻量获取避免影响分页；MongoDB 改为 Docker 容器地址 |
| 2026-06-11 | — | 新增合同组合筛选功能（7 维度）；新增批量下载功能；contractId 替换 contractNo |
| 2026-06-05 | — | 修复大看板数据渲染与主页懒加载；新增后端 API 文档；增强退出功能 |
| 2026-05-19 | — | 修复跨域问题；增加企业 logo；登录页新增版本号 |
| 2026-05-18 | — | Docker 前后端容器构建分离；修复网络连接类型配置 |
| 2026-05-15 | — | Docker 支持；默认管理员密码修改功能；密码修改提示 |
| 2026-05-07 | v0.4 | 数据库联动；增删改查逻辑；文件上传逻辑实现 |
| 2026-04-30 | v0.3 | 登录退出逻辑；MongoDB 连接；实际 auth 流程 |
| 2026-04-23 | v0.2 | API 接口对接；部分功能动态更新 |

---

*最后更新：2026年6月29日*
