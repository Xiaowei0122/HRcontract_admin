# HR合同管理系统 - API 接口文档

**系统名称**: 鸿瑞办公后端系统  
**API 基础地址**: `http://localhost:9080`  
**文档更新时间**: 2026-06-05  
**API 版本**: v1.0

---

## 目录
1. [认证管理](#认证管理)
2. [合同管理](#合同管理)
3. [系统设置](#系统设置)
4. [全局说明](#全局说明)

---

## 认证管理

### 1. 用户登录

**接口地址**: `POST /api/login`

**功能说明**: 用户登录，验证用户名和密码，返回 Token 和用户信息

**请求体**:
```json
{
  "username": "admin",
  "password": "admin"
}
```

**请求参数说明**:
| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| username | string | ✅ | 用户名 |
| password | string | ✅ | 密码（SHA256 加密存储） |

**成功响应** (200):
```json
{
  "status": "success",
  "userRole": "admin",
  "realName": "管理员",
  "isGuest": false,
  "token": "hr_token_xxx...",
  "lastLogin": "2026-06-05 10:30:45",
  "isDefaultPassword": false
}
```

**响应字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 请求状态：success / error |
| userRole | string | 用户角色：admin（管理员） |
| realName | string | 用户真实姓名 |
| isGuest | boolean | 是否访客模式 |
| token | string | 用于后续请求的认证令牌 |
| lastLogin | string | 最后登录时间（格式：YYYY-MM-DD HH:MM:SS） |
| isDefaultPassword | boolean | 是否使用默认密码 |

**失败响应** (401):
```json
{
  "detail": "账号或密码错误"
}
```

---

### 2. 用户退出登录

**接口地址**: `POST /api/logout`

**功能说明**: 用户退出登录，清除服务器端的 Token

**请求体**:
```json
{
  "username": "admin",
  "token": "hr_token_xxx..."
}
```

**请求参数说明**:
| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| username | string | ✅ | 用户名 |
| token | string | ✅ | 登录时返回的 Token |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "已从服务器安全登出"
}
```

---

### 3. 修改密码

**接口地址**: `POST /api/change-password`

**功能说明**: 用户修改自己的密码

**请求体**:
```json
{
  "username": "admin",
  "oldPassword": "admin",
  "newPassword": "newpassword123"
}
```

**请求参数说明**:
| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| username | string | ✅ | 用户名 |
| oldPassword | string | ✅ | 原密码 |
| newPassword | string | ✅ | 新密码 |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "密码修改成功"
}
```

**失败响应** (401):
```json
{
  "detail": "原密码错误"
}
```

---

### 4. 访客模式

**接口地址**: `GET /api/guest`

**功能说明**: 无需登录即可预览最近 2 条合同信息

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
      "contractId": "HT202606051030123",
      "name": "年度合作合同",
      "contractNo": "HT-2026-001",
      "amount": 50000.00,
      "status": "已签署",
      "customer": "ABC科技有限公司",
      "createTime": "2026-06-05 10:30:45"
    },
    {
      "_id": "507f1f77bcf86cd799439012",
      "contractId": "HT202606051031456",
      "name": "服务采购合同",
      "contractNo": "HT-2026-002",
      "amount": 30000.00,
      "status": "草稿",
      "customer": "XYZ企业",
      "createTime": "2026-06-04 14:22:10"
    }
  ]
}
```

---

## 合同管理

### 1. 获取合同列表

**接口地址**: `GET /api/contracts`

**功能说明**: 获取合同列表，支持分页，不同角色权限不同

**请求参数** (Query String):
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| role | string | ❌ | admin | 用户角色：admin（管理员）、guest（访客） |
| page | integer | ❌ | 1 | 页码，从 1 开始 |
| size | integer | ❌ | 10 | 每页显示条数（支持 20、50、100 等） |

**示例请求**:
```
GET /api/contracts?role=admin&page=1&size=10
```

**成功响应** (200):

*管理员角色*:
```json
{
  "list": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "contractId": "HT202606051030123",
      "name": "年度合作合同",
      "contractNo": "HT-2026-001",
      "category": "采购合同",
      "amount": 50000.00,
      "status": "已签署",
      "customer": "ABC科技有限公司",
      "customerType": "企业",
      "contractType": "买卖合同",
      "contactPerson": "张三",
      "contactPhone": "13800138000",
      "signDate": "2026-06-01",
      "servicePeriod": "2026-06-01 至 2026-12-31",
      "remark": "重点客户，需要重点跟进",
      "fileUrl": "/api/contracts/file/20260605103000_contract.pdf",
      "fileName": "contract.pdf",
      "createTime": "2026-06-05 10:30:45",
      "updateTime": "2026-06-05 10:30:45",
      "operator": "admin",
      "isDeleted": false
    }
  ],
  "total": 25
}
```

*访客角色*:
```json
{
  "list": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "contractId": "HT202606051030123",
      "name": "年度合作合同",
      "contractNo": "HT-2026-001",
      "amount": 50000.00,
      "status": "已签署",
      "customer": "ABC科技有限公司",
      "createTime": "2026-06-05 10:30:45"
    }
  ],
  "total": 2
}
```

**响应字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| list | array | 合同列表数据 |
| total | integer | 符合条件的合同总数 |

---

### 2. 上传合同

**接口地址**: `POST /api/contracts/upload`

**功能说明**: 上传新合同，支持附件文件

**请求方式**: `multipart/form-data`

**请求参数**:
| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | string | ✅ | 合同名称 |
| contractNo | string | ✅ | 合同编号 |
| category | string | ❌ | 合同类别 |
| amount | number | ❌ | 合同金额（默认 0.0） |
| status | string | ❌ | 合同状态（默认"草稿"） |
| customer | string | ❌ | 合作方名称 |
| customerType | string | ❌ | 合作方类型 |
| contractType | string | ❌ | 合同类型 |
| contactPerson | string | ❌ | 联系人 |
| contactPhone | string | ❌ | 联系电话 |
| signDate | string | ❌ | 签署日期（格式：YYYY-MM-DD） |
| servicePeriod | string | ❌ | 服务期限 |
| remark | string | ❌ | 备注 |
| operator | string | ❌ | 操作人（默认"admin"） |
| file | file | ❌ | 附件文件 |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "同步成功",
  "contractId": "HT202606051030123",
  "db_id": "507f1f77bcf86cd799439011"
}
```

**响应字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 请求状态 |
| message | string | 响应信息 |
| contractId | string | 系统自动生成的合同 ID（格式：HT + YYYYMMDDHHMMSS + 毫秒） |
| db_id | string | MongoDB 数据库 ID |

**失败响应** (500):
```json
{
  "status": "error",
  "message": "具体的错误信息"
}
```

---

### 3. 更新合同

**接口地址**: `PUT /api/contracts/{db_id}`

**功能说明**: 更新现有合同信息，支持重新上传附件

**请求方式**: `multipart/form-data`

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| db_id | string | MongoDB 数据库 ID（查询时返回的 _id） |

**请求参数** (全部可选):
| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 合同名称 |
| contractNo | string | 合同编号 |
| category | string | 合同类别 |
| amount | number | 合同金额 |
| status | string | 合同状态 |
| customer | string | 合作方名称 |
| customerType | string | 合作方类型 |
| contractType | string | 合同类型 |
| contactPerson | string | 联系人 |
| contactPhone | string | 联系电话 |
| signDate | string | 签署日期 |
| servicePeriod | string | 服务期限 |
| remark | string | 备注 |
| operator | string | 操作人 |
| file | file | 新的附件文件 |

**示例请求**:
```
PUT /api/contracts/507f1f77bcf86cd799439011
Content-Type: multipart/form-data

name=更新后的合同名称
status=已签署
amount=60000
```

**成功响应** (200):
```json
{
  "status": "success",
  "message": "合同资料已更新"
}
```

**失败响应**:

*未找到记录 (404)*:
```json
{
  "detail": "数据库中未找到该记录"
}
```

*无修改内容 (400)*:
```json
{
  "detail": "未检测到任何修改内容"
}
```

*数据库错误 (500)*:
```json
{
  "detail": "数据库同步失败: 具体错误信息"
}
```

---

### 4. 删除合同

**接口地址**: `DELETE /api/contracts/{contract_id}`

**功能说明**: 逻辑删除合同（数据保留在数据库，前端不显示）

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| contract_id | string | MongoDB 数据库 ID |

**示例请求**:
```
DELETE /api/contracts/507f1f77bcf86cd799439011
```

**成功响应** (200):
```json
{
  "message": "删除成功"
}
```

**失败响应** (404):
```json
{
  "detail": "未找到对应的合同记录"
}
```

**失败响应** (500):
```json
{
  "detail": "具体的错误信息"
}
```

---

### 5. 下载文件

**接口地址**: `GET /api/contracts/file/{file_name}`

**功能说明**: 下载合同附件文件

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| file_name | string | 文件名称（上传时系统自动生成） |

**示例请求**:
```
GET /api/contracts/file/20260605103000_contract.pdf
```

**成功响应** (200):
- 返回二进制文件内容
- Content-Type: `application/octet-stream`
- 自动下载文件

**失败响应** (404):
```json
{
  "detail": "文件未找到"
}
```

---

## 系统设置

### 1. 获取所有系统配置

**接口地址**: `GET /api/settings/`

**功能说明**: 获取当前系统的所有配置项

**请求参数**: 无

**成功响应** (200):
```json
{
  "guest_data_limit": 2,
  "maintenance_mode": false,
  "allow_guest_upload": false
}
```

**配置项说明**:
| 配置项 | 类型 | 说明 |
|--------|------|------|
| guest_data_limit | integer | 访客可预览的合同条数（默认 2） |
| maintenance_mode | boolean | 系统维护模式（true=维护中，false=正常） |
| allow_guest_upload | boolean | 是否允许访客录入合同（true=允许，false=禁止） |

---

### 2. 更新系统配置

**接口地址**: `POST /api/settings/update`

**功能说明**: 动态更新系统配置，无需重启后端

**请求体**:
```json
{
  "key": "guest_data_limit",
  "value": 5
}
```

**请求参数说明**:
| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| key | string | ✅ | 配置项名称 |
| value | any | ✅ | 配置项的新值（类型应与配置项对应） |

**成功响应** (200):
```json
{
  "status": "success",
  "message": "已更新 guest_data_limit"
}
```

**失败响应** (400):
```json
{
  "detail": "未定义的配置项"
}
```

---

### 3. 获取系统操作日志

**接口地址**: `GET /api/settings/logs`

**功能说明**: 获取最近 20 条系统操作日志

**请求参数**: 无

**成功响应** (200):
```json
[
  {
    "time": "2026-06-05 15:30:45",
    "user": "admin",
    "action": "修改配置 maintenance_mode 为 False",
    "type": "warning"
  },
  {
    "time": "2026-06-05 14:22:10",
    "user": "admin",
    "action": "修改配置 guest_data_limit 为 5",
    "type": "warning"
  },
  {
    "time": "2026-04-23 18:00:00",
    "user": "admin",
    "action": "系统初始化完成",
    "type": "info"
  }
]
```

**日志字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| time | string | 操作时间（格式：YYYY-MM-DD HH:MM:SS） |
| user | string | 操作用户 |
| action | string | 操作描述 |
| type | string | 日志类型：info（信息）、warning（警告） |

---

## 全局说明

### 数据库连接

**MongoDB 配置**:
```python
# 测试环境
MONGO_DETAILS = "mongodb://admin:Hr85550780@192.168.1.111:32771/?authSource=admin" 或根据实际编写环境修改

# 生产环境
MONGO_DETAILS = "mongodb://admin:Hr85550780@mongo-1:27017/?authSource=admin"
```

**数据库名**: `HRcontract`  
**集合列表**:
- `user` - 用户账户信息
- `contract` - 合同信息

### 文件存储

**上传目录**（环境变量）:
```python
# 测试环境
UPLOAD_DIR = Path(r"\\192.168.1.111\HR_NAS\contracts") 或根据实际编写环境修改

# 生产环境
UPLOAD_DIR = Path("/contracts")
```

**文件命名规则**: `YYYYMMDDHHMMSS_原始文件名`

### 权限控制

| 角色 | 查看权限 | 编辑权限 | 删除权限 |
|------|---------|---------|---------|
| admin（管理员） | ✅ 全部 | ✅ 是 | ✅ 是 |
| guest（访客） | ✅ 仅 2 条 | ❌ 否 | ❌ 否 |

### 时间格式

所有时间戳统一采用格式: `YYYY-MM-DD HH:MM:SS`

示例: `2026-06-05 10:30:45`

### 错误处理

**HTTP 状态码说明**:
| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败（账号密码错误） |
| 404 | 资源未找到 |
| 500 | 服务器内部错误 |

### 跨域配置

后端已启用全局 CORS 配置，支持所有来源、方法和请求头。

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 默认管理员账户

**初始账户**:
- 用户名: `admin`
- 密码: `admin`

**重要**: 首次登录后应立即修改默认密码，以确保系统安全。

### 密码存储

所有密码采用 SHA256 哈希算法存储，密码在传输时应使用 HTTPS 加密。

---

## 附录：合同数据结构

```json
{
  "_id": "MongoDB ObjectId",
  "contractId": "HT202606051030123",
  "name": "合同名称",
  "contractNo": "HT-2026-001",
  "category": "采购合同",
  "amount": 50000.00,
  "status": "已签署",
  "customer": "客户名称",
  "customerType": "企业",
  "contractType": "买卖合同",
  "contactPerson": "联系人",
  "contactPhone": "13800138000",
  "signDate": "2026-06-01",
  "servicePeriod": "2026-06-01 至 2026-12-31",
  "remark": "备注信息",
  "fileUrl": "/api/contracts/file/20260605103000_contract.pdf",
  "fileName": "contract.pdf",
  "filePath": "/contracts/20260605103000_contract.pdf",
  "createTime": "2026-06-05 10:30:45",
  "updateTime": "2026-06-05 10:30:45",
  "operator": "admin",
  "isDeleted": false
}
```

---

**文档版本**: 1.0  
**最后更新**: 2026-06-05  
**维护人**: 开发团队
