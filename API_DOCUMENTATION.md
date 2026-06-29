# 鸿瑞办公合同管理系统 — API 接口文档

**API 基础地址**: `http://localhost:9080`  
**文档版本**: v2.0  
**最后更新**: 2026-06-29  
**接口总数**: 29 个端点

---

## 目录

- [1. 认证管理](#1-认证管理)（10 个端点）
- [2. 合同管理](#2-合同管理)（7 个端点）
- [3. 系统设置](#3-系统设置)（12 个端点）
- [附录 A：合同数据结构](#附录-a合同数据结构)
- [附录 B：用户数据结构](#附录-b用户数据结构)
- [附录 C：全局说明](#附录-c全局说明)

---

## 1. 认证管理

**模块路径前缀**: `/api`  
**Swagger 标签**: `认证管理`

### 1.1 用户登录

**接口**: `POST /api/login`

**功能说明**: 验证用户名和密码，返回动态 Token 和用户信息。首次使用默认密码登录会返回 `isDefaultPassword: true`。

**请求体** (JSON):
```json
{
  "username": "admin",
  "password": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| username | string | ✅ | 用户名 |
| password | string | ✅ | SHA256 哈希后的密码 |

**成功响应** (200):
```json
{
  "status": "success",
  "userRole": "admin",
  "realName": "管理员",
  "isGuest": false,
  "token": "hr_token_abc123...",
  "lastLogin": "2026-06-29 10:30:45",
  "isDefaultPassword": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | `success` / `error` |
| userRole | string | `admin` / `user` / `viewer` |
| realName | string | 用户真实姓名 |
| isGuest | boolean | 固定为 `false` |
| token | string | 32 位随机动态令牌（`hr_token_` 前缀） |
| lastLogin | string | 本次登录时间（YYYY-MM-DD HH:MM:SS） |
| isDefaultPassword | boolean | 是否使用默认密码（`true` 时前端弹修改密码窗） |

**错误响应**:

| 状态码 | detail | 触发条件 |
|--------|--------|----------|
| 401 | `账号或密码错误` | 用户名或密码不匹配 |
| 403 | `您的账号正在等待管理员审核` | 用户状态为 `pending` |
| 403 | `您的账号注册申请已被拒绝` | 用户状态为 `rejected` |
| 403 | `您的账号已被管理员禁用` | 用户状态为 `disabled` |

---

### 1.2 用户退出登录

**接口**: `POST /api/logout`

**功能说明**: 清除服务端的用户 Token，执行安全退出。

**请求体** (JSON):
```json
{
  "username": "admin",
  "token": "hr_token_abc123..."
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| username | string | ❌ | 用户名（访客退出可省略） |
| token | string | ❌ | 登录令牌（访客退出可省略） |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "已从服务器安全登出"
}
```

> **注意**: 访客模式退出时 `username` 和 `token` 均为空，后端直接返回成功，不操作数据库。

---

### 1.3 修改密码

**接口**: `POST /api/change-password`

**功能说明**: 用户修改自己的登录密码，密码使用 SHA256 哈希传输。

**请求体** (JSON):
```json
{
  "username": "admin",
  "oldPassword": "8c6976e5...",
  "newPassword": "a665a459..."
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| username | string | ✅ | 用户名 |
| oldPassword | string | ✅ | 原密码（SHA256 哈希） |
| newPassword | string | ✅ | 新密码（SHA256 哈希，≥6 位） |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "密码修改成功"
}
```

**错误响应** (401):
```json
{
  "detail": "原密码错误"
}
```

---

### 1.4 访客模式

**接口**: `GET /api/guest`

**功能说明**: 无需认证即可预览最近 N 条合同数据（N 由系统配置 `guest_data_limit` 动态控制）。

**请求参数**: 无

**成功响应** (200):
```json
{
  "status": "success",
  "userRole": "guest",
  "isGuest": true,
  "message": "访客模式：仅可预览数据，无法进行编辑或管理操作",
  "previewData": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "contractId": "HT20260629103012",
      "name": "年度合作合同",
      "contractNo": "HT-2026-001",
      "amount": 50000.00,
      "status": "已签署",
      "customer": "ABC科技有限公司",
      "createTime": "2026-06-29 10:30:45"
    }
  ]
}
```

---

### 1.5 用户注册

**接口**: `POST /api/register`

**功能说明**: 自助注册新用户账号，注册后状态为 `pending`，需管理员审核通过后方可登录。

**请求体** (JSON):
```json
{
  "username": "zhangsan",
  "password": "a665a459...",
  "realName": "张三",
  "email": "zhangsan@example.com",
  "phone": "13800138000",
  "department": "销售部"
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| username | string | ✅ | 用户名（不可重复） |
| password | string | ✅ | SHA256 哈希密码（≥6 位） |
| realName | string | ✅ | 真实姓名 |
| email | string | ❌ | 邮箱 |
| phone | string | ❌ | 电话号码 |
| department | string | ❌ | 所属部门 |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "注册成功，请等待管理员审核通过后登录"
}
```

**错误响应**:

| 状态码 | detail | 说明 |
|--------|--------|------|
| 400 | `密码长度不能少于6位` | 密码过短 |
| 409 | `该用户名已被注册` | 用户名已存在 |

---

### 1.6 管理员查询用户列表

**接口**: `POST /api/admin/users`

**功能说明**: 管理员查看所有用户，可按状态筛选。

**请求体** (JSON):
```json
{
  "token": "hr_token_abc123...",
  "status": "pending"
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| token | string | ✅ | 管理员 Token（用于权限验证） |
| status | string | ❌ | 筛选状态：`pending` / `active` / `rejected` / `disabled`。不传则返回全部 |

**成功响应** (200):
```json
{
  "status": "success",
  "users": [
    {
      "username": "zhangsan",
      "role": "user",
      "status": "pending",
      "realName": "张三",
      "email": "zhangsan@example.com",
      "phone": "13800138000",
      "department": "销售部",
      "registerTime": "2026-06-29 09:15:00",
      "lastLogin": "",
      "createTime": "2026-06-29 09:15:00",
      "isDisable": false,
      "currentToken": ""
    }
  ]
}
```

**错误响应** (403):
```json
{
  "detail": "无管理员权限或令牌已过期"
}
```

---

### 1.7 管理员审批用户

**接口**: `POST /api/admin/approve-user`

**功能说明**: 管理员审核通过或拒绝用户的注册申请。

**请求体** (JSON):
```json
{
  "username": "zhangsan",
  "action": "approve",
  "token": "hr_token_abc123..."
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| username | string | ✅ | 目标用户名 |
| action | string | ✅ | `"approve"` 通过 / `"reject"` 拒绝 |
| token | string | ✅ | 管理员 Token |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "用户 zhangsan 的注册申请已通过"
}
```

**错误响应**:

| 状态码 | detail | 说明 |
|--------|--------|------|
| 400 | `不能审批管理员账号` | 目标为 admin |
| 400 | `该用户当前状态不允许此操作` | 用户状态不是 pending |
| 404 | `用户不存在` | 用户名不存在 |

---

### 1.8 管理员删除用户

**接口**: `POST /api/admin/delete-user`

**功能说明**: 管理员删除用户（不可删除超级管理员 admin）。

**请求体** (JSON):
```json
{
  "username": "zhangsan",
  "token": "hr_token_abc123..."
}
```

**成功响应** (200):
```json
{
  "status": "success",
  "message": "用户 zhangsan 已删除"
}
```

---

### 1.9 管理员禁用/启用用户

**接口**: `POST /api/admin/toggle-user-status`

**功能说明**: 管理员禁用或启用用户账号（不可操作 admin 账号）。

**请求体** (JSON):
```json
{
  "username": "zhangsan",
  "action": "disable",
  "token": "hr_token_abc123..."
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| username | string | ✅ | 目标用户名 |
| action | string | ✅ | `"disable"` 禁用 / `"enable"` 启用 |
| token | string | ✅ | 管理员 Token |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "用户 zhangsan 已禁用"
}
```

---

### 1.10 管理员设置用户角色

**接口**: `POST /api/admin/set-user-role`

**功能说明**: 管理员修改用户的角色（不可修改 admin 自己的角色）。

**请求体** (JSON):
```json
{
  "username": "zhangsan",
  "role": "viewer",
  "token": "hr_token_abc123..."
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| username | string | ✅ | 目标用户名 |
| role | string | ✅ | 新角色：`admin` / `user` / `viewer` |
| token | string | ✅ | 管理员 Token |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "用户 zhangsan 的角色已设为查看者"
}
```

---

## 2. 合同管理

**模块路径前缀**: `/api`  
**Swagger 标签**: `合同管理`

### 2.1 获取看板统计数据

**接口**: `GET /api/contracts/dashboard-stats`

**功能说明**: 获取合同总量、总金额、已签署数、待处理数等统计指标（轻量接口，不返回列表数据）。

**请求参数** (Query String — 全部可选):

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| role | string | — | 用户角色，访客时限制统计范围 |
| keyword | string | — | 模糊搜索（名称/编号/客户） |
| category | string | — | 按产品类别筛选 |
| contractType | string | — | 按合同类型筛选 |
| customerType | string | — | 按客户类型筛选 |
| status | string | — | 按状态筛选 |
| minAmount | number | — | 金额下限 |
| maxAmount | number | — | 金额上限 |

**成功响应** (200):
```json
{
  "totalCount": 128,
  "totalAmount": 5600000.00,
  "signedCount": 85,
  "pendingCount": 12,
  "draftCount": 20,
  "terminatedCount": 3,
  "expiredCount": 8
}
```

---

### 2.2 获取合同列表（分页 + 筛选）

**接口**: `GET /api/contracts`

**功能说明**: 分页获取合同列表，支持 7 个维度的组合筛选。访客返回受限条数。

**请求参数** (Query String):

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| role | string | — | `admin` / `user` / `viewer` / `guest` |
| page | integer | 1 | 页码（从 1 开始） |
| size | integer | 100 | 每页条数 |
| keyword | string | — | 模糊搜索（名称/编号/客户） |
| category | string | — | 产品类别 |
| contractType | string | — | 合同类型 |
| customerType | string | — | 客户类型 |
| status | string | — | 合同状态 |
| minAmount | number | — | 金额下限 |
| maxAmount | number | — | 金额上限 |

**示例请求**:
```
GET /api/contracts?role=admin&page=1&size=20&status=已签署&category=计算机设备
```

**成功响应** (200):
```json
{
  "list": [
    {
      "_id": "649ab123...",
      "contractId": "HT20260629103012",
      "name": "年度合作合同",
      "contractNo": "HT-2026-001",
      "category": "计算机设备",
      "contractType": "采购合同",
      "customerType": "高校",
      "signingCompany": "鸿瑞办公",
      "customer": "华南理工大学",
      "contactPerson": "张教授",
      "contactPhone": "13800138000",
      "signDate": "2026-06-01",
      "servicePeriod": "2026-06-01 ~ 2027-05-31",
      "amount": 128.50,
      "status": "已签署",
      "remark": "备注信息",
      "fileUrl": "/api/contracts/download-by-id/HT20260629103012",
      "fileName": "采购合同.docx",
      "filePath": "\\192.168.1.111\\contracts\\20260629103012_采购合同.docx",
      "createTime": "2026-06-29 10:30:45",
      "updateTime": "2026-06-29 10:30:45",
      "operator": "admin",
      "isDeleted": false
    }
  ],
  "total": 128
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| list | array | 当前页合同数据 |
| total | integer | 符合条件的合同总数 |

---

### 2.3 上传合同（新建）

**接口**: `POST /api/contracts/upload`

**功能说明**: 新建合同并上传附件文件。支持自定义字段（JSON 字符串）一并提交。

**请求方式**: `multipart/form-data`

**请求参数**:

| 字段 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| contractId | string | ✅ | — | 合同唯一标识（如 `HT20260629103012`） |
| name | string | ✅ | — | 合同名称 |
| contractNo | string | ✅ | — | 合同编号 |
| category | string | ❌ | — | 产品类别 |
| amount | number | ❌ | 0.0 | 合同金额（万元） |
| status | string | ❌ | `"草稿"` | 合同状态 |
| customer | string | ❌ | — | 客户名称 |
| customerType | string | ❌ | — | 客户类型 |
| contractType | string | ❌ | — | 合同类型 |
| signingCompany | string | ❌ | — | 签署公司 |
| contactPerson | string | ❌ | — | 联系人 |
| contactPhone | string | ❌ | — | 联系电话 |
| signDate | string | ❌ | — | 签订日期（YYYY-MM-DD） |
| servicePeriod | string | ❌ | — | 服务期限 |
| remark | string | ❌ | — | 备注 |
| operator | string | ❌ | `"admin"` | 操作人 |
| customFields | string | ❌ | — | 自定义字段（JSON 字符串） |
| file | file | ❌ | — | 合同附件文件 |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "合同同步成功",
  "contractId": "HT20260629103012",
  "db_id": "649ab123..."
}
```

**失败响应** (500):
```json
{
  "status": "error",
  "message": "具体的错误信息"
}
```

---

### 2.4 更新合同

**接口**: `PUT /api/contracts/{contract_id}`

**功能说明**: 更新指定合同信息，可选替换附件文件。`contract_id` 为业务键 `contractId`（非 MongoDB `_id`）。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| contract_id | string | 合同业务 ID（如 `HT20260629103012`） |

**请求方式**: `multipart/form-data`

**请求参数** (除 `name` 和 `amount` 外全部可选):

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | string | ✅ | 合同名称 |
| amount | number | ✅ | 合同金额 |
| contractId | string | ❌ | 新的合同 ID |
| contractNo | string | ❌ | 合同编号 |
| category | string | ❌ | 产品类别 |
| status | string | ❌ | 合同状态 |
| customer | string | ❌ | 客户名称 |
| customerType | string | ❌ | 客户类型 |
| contractType | string | ❌ | 合同类型 |
| signingCompany | string | ❌ | 签署公司 |
| contactPerson | string | ❌ | 联系人 |
| contactPhone | string | ❌ | 联系电话 |
| signDate | string | ❌ | 签订日期 |
| servicePeriod | string | ❌ | 服务期限 |
| remark | string | ❌ | 备注 |
| operator | string | ❌ | 操作人 |
| customFields | string | ❌ | 自定义字段（JSON 字符串） |
| file | file | ❌ | 新附件文件（替换原有） |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "合同资料已更新"
}
```

**错误响应**:

| 状态码 | detail | 说明 |
|--------|--------|------|
| 404 | `数据库中未找到该记录` | contract_id 不存在 |
| 400 | `未检测到任何修改内容` | 请求体无变更字段 |

---

### 2.5 删除合同（逻辑删除）

**接口**: `DELETE /api/contracts/{contract_id}`

**功能说明**: 逻辑删除合同（标记 `isDeleted: true`），数据保留在数据库中。`contract_id` 为业务键。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| contract_id | string | 合同业务 ID |

**成功响应** (200):
```json
{
  "message": "删除成功"
}
```

**错误响应** (404):
```json
{
  "detail": "未找到对应的合同记录"
}
```

---

### 2.6 批量下载合同附件

**接口**: `GET /api/contracts/batch-download`

**功能说明**: 根据多个合同 ID 批量打包下载合同附件，返回 ZIP 压缩包。

**请求参数** (Query String):

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| contract_ids | string[] | ✅ | 合同 ID 列表，可重复传参 |

**示例请求**:
```
GET /api/contracts/batch-download?contract_ids=HT20260601001&contract_ids=HT20260601002&contract_ids=HT20260601003
```

**成功响应** (200):
- Content-Type: `application/zip`
- Content-Disposition: `attachment; filename="contracts_batch_20260629_103045.zip"`
- 返回 ZIP 二进制文件流

---

### 2.7 单个合同附件下载

**接口**: `GET /api/contracts/download-by-id/{contract_id}`

**功能说明**: 通过合同业务 ID 直接下载该合同的附件文件。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| contract_id | string | 合同业务 ID |

**成功响应** (200):
- Content-Disposition: `attachment; filename="合同文件名.docx"`
- 返回文件二进制流

**错误响应** (404):
```json
{
  "detail": "未找到合同记录或无附件"
}
```

---

## 3. 系统设置

**模块路径前缀**: `/api/settings`  
**Swagger 标签**: `系统设置`

### 3.1 获取全部系统配置

**接口**: `GET /api/settings/`

**功能说明**: 获取当前系统的所有配置项。

**请求参数**: 无

**成功响应** (200):
```json
{
  "guest_data_limit": 2,
  "maintenance_mode": false,
  "allow_guest_upload": false,
  "guest_full_access": false,
  "show_dashboard_charts": true,
  "big_amount_threshold": 100,
  "default_visible_fields": ["name","contractId","category","amount","status","customer","signDate"],
  "max_upload_size_mb": 50,
  "allowed_file_types": [".pdf",".doc",".docx",".xls",".xlsx",".jpg",".png",".zip"],
  "session_timeout_minutes": 480,
  "contract_id_prefix": "HT",
  "log_retention_days": 90,
  "allow_user_delete": false,
  "custom_fields": []
}
```

> 详细配置项说明见 [README.md — 系统配置项](README.md#-系统配置项)

---

### 3.2 获取可用字段列表

**接口**: `GET /api/settings/fields`

**功能说明**: 获取所有合同可用字段列表（17 个基础字段 + 自定义字段）。

**成功响应** (200):
```json
{
  "fields": [
    { "key": "contractId", "label": "合同ID" },
    { "key": "name", "label": "合同名称" },
    { "key": "contractType", "label": "合同类型" },
    { "key": "category", "label": "产品类别" },
    { "key": "customerType", "label": "客户类别" },
    { "key": "customer", "label": "客户名称" },
    { "key": "signingCompany", "label": "签署公司" },
    { "key": "contactPerson", "label": "联系人" },
    { "key": "contactPhone", "label": "联系电话" },
    { "key": "servicePeriod", "label": "服务期限" },
    { "key": "signDate", "label": "签订日期" },
    { "key": "amount", "label": "合同金额(元)" },
    { "key": "status", "label": "状态" },
    { "key": "remark", "label": "备注" },
    { "key": "createTime", "label": "创建时间" },
    { "key": "updateTime", "label": "更新时间" },
    { "key": "contractNo", "label": "合同编号" },
    { "key": "operator", "label": "操作人" }
  ]
}
```

---

### 3.3 获取默认可见字段

**接口**: `GET /api/settings/default-fields`

**功能说明**: 获取当前配置的合同列表默认显示字段。

**成功响应** (200):
```json
{
  "default_visible_fields": ["name","contractId","category","amount","status","customer","signDate"]
}
```

---

### 3.4 设置默认可见字段

**接口**: `POST /api/settings/default-fields`

**功能说明**: 管理员设置合同列表默认显示字段，所有用户打开列表时自动应用。

**请求体** (JSON):
```json
{
  "fields": ["name","contractId","category","amount","status","customer","signDate","operator"]
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| fields | string[] | ✅ | 默认可见字段的 key 数组 |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "默认可见字段已更新"
}
```

---

### 3.5 更新单个系统配置项

**接口**: `POST /api/settings/update`

**功能说明**: 动态更新单个配置项，实时生效，无需重启后端。

**请求体** (JSON):
```json
{
  "key": "guest_data_limit",
  "value": 5
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| key | string | ✅ | 配置项名称 |
| value | any | ✅ | 配置项的新值（类型应匹配配置项定义） |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "已更新 guest_data_limit"
}
```

**错误响应** (400):
```json
{
  "detail": "未定义的配置项"
}
```

---

### 3.6 获取操作日志

**接口**: `GET /api/settings/logs`

**功能说明**: 分页获取系统操作日志，按时间倒序排列。

**请求参数** (Query String):

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码（从 1 开始） |
| pageSize | integer | 20 | 每页条数（最大 100） |

**示例请求**:
```
GET /api/settings/logs?page=1&pageSize=20
```

**成功响应** (200):
```json
{
  "logs": [
    {
      "time": "2026-06-29 15:30:45",
      "user": "admin",
      "action": "修改配置 guest_data_limit 为 5",
      "type": "warning"
    },
    {
      "time": "2026-06-29 14:22:10",
      "user": "admin",
      "action": "登录了系统",
      "type": "info"
    }
  ],
  "total": 256,
  "page": 1,
  "pageSize": 20
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| logs | array | 当前页日志条目 |
| total | integer | 日志总数 |
| page | integer | 当前页码 |
| pageSize | integer | 每页条数 |

**日志类型说明**:

| type | 含义 | 示例场景 |
|------|------|----------|
| `info` | 常规操作 | 用户登录、注册申请 |
| `warning` | 敏感操作 | 配置变更、用户删除、权限修改 |

---

### 3.7 修改管理员密码

**接口**: `POST /api/settings/update_password`

**功能说明**: 通过系统设置面板修改管理员密码。

**请求体** (JSON):
```json
{
  "username": "admin",
  "oldPassword": "8c6976e5...",
  "newPassword": "a665a459..."
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| username | string | ✅ | 用户名 |
| oldPassword | string | ✅ | 原密码（SHA256 哈希） |
| newPassword | string | ✅ | 新密码（SHA256 哈希） |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "密码修改成功"
}
```

---

### 3.8 字段定义管理

#### 3.8.1 获取字段定义列表

**接口**: `GET /api/settings/field-definitions`

**功能说明**: 获取所有字段定义（17 个基础字段 + 管理员创建的自定义字段），供字段管理页使用。

**成功响应** (200):
```json
{
  "fields": [
    { "key": "contractId", "label": "合同ID", "type": "text", "isCustom": false, "isRequired": true },
    { "key": "custom_field_1", "label": "项目编号", "type": "text", "isCustom": true, "isRequired": false }
  ]
}
```

#### 3.8.2 新增自定义字段

**接口**: `POST /api/settings/custom-fields`

**请求体** (JSON):
```json
{
  "key": "project_code",
  "label": "项目编号",
  "type": "text",
  "isRequired": false,
  "options": []
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| key | string | ✅ | 字段键名（英文，唯一） |
| label | string | ✅ | 字段显示名称 |
| type | string | ✅ | 字段类型：`text` / `number` / `date` / `select` |
| isRequired | boolean | ❌ | 是否必填 |
| options | array | ❌ | 选项列表（type 为 `select` 时使用） |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "自定义字段已添加"
}
```

#### 3.8.3 修改自定义字段

**接口**: `PUT /api/settings/custom-fields/{field_key}`

**功能说明**: 修改已创建的自定义字段属性。

#### 3.8.4 删除自定义字段

**接口**: `DELETE /api/settings/custom-fields/{field_key}`

**请求参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| field_key | path | ✅ | 字段键名 |
| token | query | ✅ | 管理员 Token |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "自定义字段已删除"
}
```

> **注意**: 基础字段（17 个内置字段）不可删除。

---

### 3.9 产品类别管理

#### 3.9.1 获取产品类别列表

**接口**: `GET /api/settings/categories`

**成功响应** (200):
```json
{
  "categories": [
    {"name": "计算机设备", "color": "#3b82f6"},
    {"name": "办公用品", "color": "#10b981"},
    {"name": "电子产品", "color": "#f59e0b"}
  ]
}
```

#### 3.9.2 新增产品类别

**接口**: `POST /api/settings/categories`

**请求体** (JSON):
```json
{
  "name": "安防监控",
  "color": "#06b6d4"
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | string | ✅ | 类别名称（不可重复） |
| color | string | ❌ | 十六进制颜色值（自动分配） |

#### 3.9.3 修改产品类别

**接口**: `PUT /api/settings/categories/{cat_index}`

**功能说明**: 修改指定索引的产品类别名称或颜色。

#### 3.9.4 删除产品类别

**接口**: `DELETE /api/settings/categories/{cat_index}`

**请求参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| cat_index | path | ✅ | 类别索引 |
| token | query | ✅ | 管理员 Token |

---

### 3.10 签署公司管理

#### 3.10.1 获取签署公司列表

**接口**: `GET /api/settings/signing-companies`

**成功响应** (200):
```json
{
  "companies": ["鸿瑞办公", "政通慧采", "众冠供应链"]
}
```

#### 3.10.2 新增签署公司

**接口**: `POST /api/settings/signing-companies`

**请求体** (JSON):
```json
{
  "name": "新设子公司"
}
```

#### 3.10.3 修改签署公司

**接口**: `PUT /api/settings/signing-companies/{company_index}`

#### 3.10.4 删除签署公司

**接口**: `DELETE /api/settings/signing-companies/{company_index}`

**请求参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| company_index | path | ✅ | 公司索引 |
| token | query | ✅ | 管理员 Token |

---

## 附录 A：合同数据结构

### MongoDB 文档结构

```json
{
  "_id": "ObjectId(...)",
  "contractId": "HT20260629103012",
  "name": "年度合作合同",
  "contractNo": "HT-2026-001",
  "category": "计算机设备",
  "contractType": "采购合同",
  "customerType": "高校",
  "signingCompany": "鸿瑞办公",
  "customer": "华南理工大学",
  "contactPerson": "张教授",
  "contactPhone": "13800138000",
  "servicePeriod": "2026-06-01 ~ 2027-05-31",
  "signDate": "2026-06-01",
  "amount": 128.50,
  "status": "已签署",
  "remark": "备注信息",
  "fileUrl": "/api/contracts/download-by-id/HT20260629103012",
  "fileName": "采购合同.docx",
  "filePath": "\\192.168.1.111\\contracts\\20260629103012_采购合同.docx",
  "createTime": "2026-06-29 10:30:45",
  "updateTime": "2026-06-29 10:30:45",
  "creator": "admin",
  "operator": "admin",
  "isDeleted": false
}
```

### 合同状态枚举

| 状态值 | 说明 |
|--------|------|
| `草稿` | 合同草稿，尚未签署 |
| `已签署` | 已完成签署 |
| `待处理` | 等待处理 |
| `已到期` | 合同已过期 |
| `已终止` | 合同被终止 |

---

## 附录 B：用户数据结构

### MongoDB 文档结构

```json
{
  "_id": "ObjectId(...)",
  "username": "admin",
  "password": "8c6976e5...(SHA256)",
  "role": "admin",
  "status": "active",
  "realName": "管理员",
  "email": "admin@example.com",
  "phone": "13800138000",
  "department": "数字化工程部",
  "registerTime": "2026-06-01 09:00:00",
  "lastLogin": "2026-06-29 10:30:45",
  "current_token": "hr_token_abc123...",
  "is_default_password": false
}
```

### 用户状态枚举

| 状态值 | 说明 |
|--------|------|
| `active` | 正常可用 |
| `pending` | 等待管理员审核 |
| `rejected` | 注册被拒绝 |
| `disabled` | 被管理员禁用 |

### 角色枚举

| 角色 | 值 | 权限说明 |
|------|------|----------|
| 管理员 | `admin` | 全部权限（系统设置、用户管理、合同CRUD） |
| 普通用户 | `user` | 合同CRUD（删除权限可配置） |
| 查看者 | `viewer` | 只读查看 + 下载 |
| 访客 | `guest` | 仅预览 N 条数据（N 可配置） |

---

## 附录 C：全局说明

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败（账号密码错误） |
| 403 | 权限不足（Token 无效/过期/非管理员） |
| 404 | 资源未找到 |
| 409 | 资源冲突（如用户名重复） |
| 500 | 服务器内部错误 |

### 时间格式

所有时间戳统一格式：`YYYY-MM-DD HH:MM:SS`  
示例：`2026-06-29 10:30:45`

### 密码安全

- 传输层：密码使用 **SHA256 哈希** 后传输
- 存储层：MongoDB 中存储 SHA256 哈希值
- 默认密码检测：登录时自动检测，提醒用户修改

### 跨域配置

后端已启用全局 CORS：
```python
allow_origins=["*"]
allow_methods=["*"]
allow_headers=["*"]
```
生产环境建议在 `src/api/main.py` 中限制 `allow_origins` 为前端实际地址。

### 数据库连接

项目使用共享连接模块 `database.py`，所有路由共用同一个 MongoDB 连接：
```python
# 切换环境
USE_PRODUCTION = False   # 测试
USE_PRODUCTION = True    # 生产

# 或环境变量覆盖
MONGO_URL = os.getenv("MONGO_URL", ...)
```

### Swagger 交互式文档

开发环境可直接访问以下地址进行 API 调试：
- **Swagger UI**：http://localhost:9080/docs
- **ReDoc**：http://localhost:9080/redoc

---

*文档版本: v2.0 · 最后更新: 2026-06-29*
