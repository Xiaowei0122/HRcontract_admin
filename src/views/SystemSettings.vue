<template>
  <div class="system-wrapper">
    <div class="top-bar">
      <div class="left">
        <el-icon class="back-icon" @click="$router.push('/')"><ArrowLeft /></el-icon>
        <h2 class="title">系统管理中心</h2>
        <el-tag type="danger" effect="dark" size="small" class="admin-tag">仅管理员可用</el-tag>
      </div>
      <div class="right">
        <el-button @click="$router.push('/')" plain>返回合同管理</el-button>
      </div>
    </div>

    <div class="main-content">
      <el-card class="settings-card" shadow="never">
        <el-tabs v-model="activeTab" class="custom-tabs">

          <!-- ═══════════════ 参数配置 Tab ═══════════════ -->
          <el-tab-pane label="参数配置" name="config">
            <div class="config-section">

              <!-- ── 权限与预览控制 ── -->
              <h3 class="section-title">权限与预览控制</h3>
              <el-form label-width="180px" label-position="left">
                <el-form-item label="访客可见合同条数">
                  <div class="input-with-tip">
                    <el-input-number
                      v-model="configForm.guest_data_limit"
                      :min="0" :max="100"
                      @change="saveConfig('guest_data_limit', configForm.guest_data_limit)"
                    />
                    <span class="tip-text">设为 0 则访客完全不可见。</span>
                  </div>
                </el-form-item>

                <el-form-item label="系统维护模式">
                  <el-switch
                    v-model="configForm.maintenance_mode"
                    active-text="开启" inactive-text="关闭"
                    @change="saveConfig('maintenance_mode', configForm.maintenance_mode)"
                  />
                  <span class="tip-text" style="margin-left:10px">开启后所有用户无法录入/编辑合同。</span>
                </el-form-item>

                <el-form-item label="允许访客上传合同">
                  <el-switch
                    v-model="configForm.allow_guest_upload"
                    active-text="允许" inactive-text="禁止"
                    @change="saveConfig('allow_guest_upload', configForm.allow_guest_upload)"
                  />
                  <span class="tip-text" style="margin-left:10px">控制访客模式是否允许提交新合同。</span>
                </el-form-item>

                <el-form-item label="访客全部开放">
                  <el-switch
                    v-model="configForm.guest_full_access"
                    active-text="开启" inactive-text="关闭"
                    @change="saveConfig('guest_full_access', configForm.guest_full_access)"
                  />
                  <span class="tip-text" style="margin-left:10px">开启后访客可查看全部合同数据（只读），无需登录。</span>
                </el-form-item>

                <el-divider />

                <!-- ── 显示与字段管理 ── -->
                <h3 class="section-title">显示与字段管理</h3>

                <el-form-item label="显示统计图表">
                  <el-switch
                    v-model="configForm.show_dashboard_charts"
                    @change="saveConfig('show_dashboard_charts', configForm.show_dashboard_charts)"
                  />
                  <span class="tip-text" style="margin-left:10px">控制合同管理页顶部饼图的可见性。</span>
                </el-form-item>

                <el-form-item label="大额合同阈值 (万)">
                  <div class="input-with-tip">
                    <el-input-number
                      v-model="configForm.big_amount_threshold"
                      :min="0" :step="10"
                      @change="saveConfig('big_amount_threshold', configForm.big_amount_threshold)"
                    />
                    <span class="tip-text">金额超过此标准的合同将在列表中高亮显示。</span>
                  </div>
                </el-form-item>

                <el-form-item label="默认显示字段">
                  <div class="field-manager">
                    <div class="field-tip">
                      <el-icon><InfoFilled /></el-icon>
                      勾选后，所有用户首次进入合同列表页时默认显示这些列。用户仍可在列表页自行调整。
                    </div>
                    <el-checkbox-group
                      v-model="configForm.default_visible_fields"
                      @change="saveDefaultFields"
                      class="field-check-group"
                    >
                      <el-checkbox
                        v-for="f in availableFields"
                        :key="f.key"
                        :label="f.key"
                        :value="f.key"
                        class="field-check-item"
                      >
                        {{ f.label }}
                      </el-checkbox>
                    </el-checkbox-group>
                  </div>
                </el-form-item>

                <el-divider />

                <!-- ── 文件上传控制 ── -->
                <h3 class="section-title">文件上传控制</h3>

                <el-form-item label="最大上传文件大小">
                  <div class="input-with-tip">
                    <el-input-number
                      v-model="configForm.max_upload_size_mb"
                      :min="1" :max="500" :step="5"
                      @change="saveConfig('max_upload_size_mb', configForm.max_upload_size_mb)"
                    />
                    <span class="tip-text">MB（{{ configForm.max_upload_size_mb }} MB），超出将拒绝上传。</span>
                  </div>
                </el-form-item>

                <el-form-item label="允许的文件类型">
                  <el-input
                    v-model="configForm.allowed_file_types"
                    style="width:360px"
                    placeholder="如 pdf,doc,docx,xls,xlsx"
                    @blur="saveConfig('allowed_file_types', configForm.allowed_file_types)"
                  />
                  <span class="tip-text" style="margin-left:10px">逗号分隔，不含空格。</span>
                </el-form-item>

                <el-divider />

                <!-- ── 安全与合同编号 ── -->
                <h3 class="section-title">安全与合同编号</h3>

                <el-form-item label="合同编号前缀">
                  <div class="input-with-tip">
                    <el-input
                      v-model="configForm.contract_id_prefix"
                      style="width:120px"
                      maxlength="6"
                      @blur="saveConfig('contract_id_prefix', configForm.contract_id_prefix)"
                    />
                    <span class="tip-text">新建合同时自动生成的编号前缀，如「HT20260627...」。</span>
                  </div>
                </el-form-item>

                <el-form-item label="闲置超时登出">
                  <div class="input-with-tip">
                    <el-input-number
                      v-model="configForm.session_timeout_minutes"
                      :min="0" :max="1440" :step="5"
                      @change="saveConfig('session_timeout_minutes', configForm.session_timeout_minutes)"
                    />
                    <span class="tip-text">分钟（0 = 不限），闲置超过此时长自动退回登录页。</span>
                  </div>
                </el-form-item>

                <el-form-item label="日志保留天数">
                  <el-select
                    v-model="configForm.log_retention_days"
                    style="width:120px"
                    @change="saveConfig('log_retention_days', configForm.log_retention_days)"
                  >
                    <el-option label="7天" :value="7" />
                    <el-option label="30天" :value="30" />
                    <el-option label="90天" :value="90" />
                    <el-option label="永久" :value="0" />
                  </el-select>
                </el-form-item>

                <el-form-item label="管理员密码修改">
                  <el-button type="primary" :icon="Lock" @click="showPasswordDialog = true">修改密码</el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-tab-pane>

          <!-- ═══════════════ 用户管理 Tab ═══════════════ -->
          <el-tab-pane label="用户管理" name="users">
            <div style="margin-bottom: 16px;">
              <el-radio-group v-model="userStatusFilter" @change="fetchUsers" size="small">
                <el-radio-button label="">全部</el-radio-button>
                <el-radio-button label="pending">待审核</el-radio-button>
                <el-radio-button label="active">已通过</el-radio-button>
                <el-radio-button label="rejected">已拒绝</el-radio-button>
              </el-radio-group>
            </div>
            <el-table :data="userList" border style="width: 100%" v-loading="userLoading">
              <el-table-column prop="username" label="用户名" width="140" />
              <el-table-column prop="realName" label="真实姓名" width="100" />
              <el-table-column prop="role" label="角色" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.role === 'admin' ? 'danger' : ''" effect="plain" size="small">
                    {{ row.role === 'admin' ? '管理员' : '用户' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="90">
                <template #default="{ row }">
                  <el-tag :type="statusTagType(row.status)" effect="plain" size="small">
                    {{ statusLabel(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="department" label="部门" width="120" />
              <el-table-column prop="phone" label="手机号" width="130" />
              <el-table-column prop="registerTime" label="注册时间" width="160" />
              <el-table-column prop="lastLogin" label="最后登录" width="160" />
              <el-table-column label="操作" width="240" fixed="right">
                <template #default="{ row }">
                  <template v-if="row.status === 'pending'">
                    <el-button link type="success" size="small" @click="handleApprove(row.username, 'approve')">通过</el-button>
                    <el-button link type="danger" size="small" @click="handleApprove(row.username, 'reject')">拒绝</el-button>
                  </template>
                  <template v-else-if="row.role !== 'admin'">
                    <el-button link type="primary" size="small" @click="handleSetRole(row)">权限设置</el-button>
                    <el-button v-if="row.status !== 'disabled'" link type="warning" size="small" @click="handleToggleStatus(row.username, 'disable')">禁用</el-button>
                    <el-button v-else link type="success" size="small" @click="handleToggleStatus(row.username, 'enable')">启用</el-button>
                    <el-button link type="danger" size="small" @click="handleDeleteUser(row.username)">删除</el-button>
                  </template>
                  <span v-else style="color: #c0c4cc; font-size: 12px;">—</span>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- ═══════════════ 操作日志 Tab ═══════════════ -->
          <el-tab-pane label="操作日志" name="logs">
            <div class="log-container">
              <el-timeline v-if="logs.length > 0">
                <el-timeline-item
                  v-for="(log, index) in logs"
                  :key="index"
                  :timestamp="log.time"
                  :type="log.type || 'info'"
                  hollow
                >
                  <span class="log-user">{{ log.user }}</span>
                  <span class="log-action">{{ log.action }}</span>
                </el-timeline-item>
              </el-timeline>
              <el-empty v-else description="暂无操作日志" />
            </div>
          </el-tab-pane>

        </el-tabs>
      </el-card>
    </div>

    <!-- ═══════════════ 修改密码对话框 ═══════════════ -->
    <el-dialog v-model="showPasswordDialog" title="修改管理员密码" width="420px" :close-on-click-modal="false">
      <el-form :model="pwdForm" label-position="top">
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.newPassword" type="password" placeholder="请输入新密码（至少6位）" show-password />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="pwdForm.confirmPassword" type="password" placeholder="请再次输入新密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" @click="handlePasswordUpdate" :loading="pwdLoading">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, onMounted, ref } from 'vue'
import { ArrowLeft, Lock, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeTab = ref('config')
const showPasswordDialog = ref(false)
const pwdLoading = ref(false)
const pwdForm = reactive({
  newPassword: '',
  confirmPassword: '',
})

// ── 可用字段列表（从后端获取）──
const availableFields = ref([])

// ── 系统配置表单：补全所有后端定义的 key ──
const configForm = reactive({
  // 权限与预览控制
  guest_data_limit: 2,
  maintenance_mode: false,
  allow_guest_upload: false,
  guest_full_access: false,
  // 业务预警与显示
  show_dashboard_charts: true,
  big_amount_threshold: 100,
  default_visible_fields: [],
  // 文件上传控制
  max_upload_size_mb: 50,
  allowed_file_types: 'pdf,doc,docx,xls,xlsx,jpg,png',
  // 安全与合同编号
  session_timeout_minutes: 0,
  contract_id_prefix: 'HT',
  log_retention_days: 30,
})

// ── 用户管理状态 ──
const userList = ref([])
const userStatusFilter = ref('pending')
const userLoading = ref(false)

const statusTagType = (status) => {
  return { pending: 'warning', active: 'success', rejected: 'danger', disabled: 'info' }[status || 'active'] || 'info'
}
const statusLabel = (status) => {
  return { pending: '待审核', active: '已通过', rejected: '已拒绝', disabled: '已禁用' }[status || 'active'] || '已通过'
}

// ── 操作日志 ──
const logs = ref([])

// ═════════════════════════════════════════════════════════════
//  初始化
// ═════════════════════════════════════════════════════════════
const fetchInitialData = async () => {
  try {
    // 并发拉取：系统配置 + 可用字段 + 操作日志
    const [configRes, fieldsRes, logRes] = await Promise.all([
      fetch('http://localhost:9080/api/settings/'),
      fetch('http://localhost:9080/api/settings/fields'),
      fetch('http://localhost:9080/api/settings/logs'),
    ])

    if (configRes.ok) {
      const data = await configRes.json()
      // 过滤掉后端内部字段 _id，避免污染 configForm
      delete data._id
      Object.assign(configForm, data)
      console.log('✅ 系统配置已加载:', Object.keys(data).length, '项')
    } else {
      console.error('❌ 系统配置加载失败:', configRes.status)
    }

    if (fieldsRes.ok) {
      const data = await fieldsRes.json()
      availableFields.value = data.availableFields || []
      console.log('✅ 可用字段已加载:', availableFields.value.length, '个')
    }

    if (logRes.ok) {
      const logData = await logRes.json()
      logs.value = Array.isArray(logData) ? logData : []
      console.log('✅ 操作日志已加载:', logs.value.length, '条')
    } else {
      console.error('❌ 操作日志加载失败:', logRes.status)
      logs.value = []
    }
  } catch (err) {
    console.error('❌ 系统设置初始化失败:', err)
    ElMessage.error('系统设置初始化失败，请检查后端服务')
  }
}

onMounted(() => {
  fetchInitialData()
  fetchUsers()
})

// ═════════════════════════════════════════════════════════════
//  配置保存
// ═════════════════════════════════════════════════════════════
const saveConfig = async (key, value) => {
  try {
    const response = await fetch('http://localhost:9080/api/settings/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, value }),
    })

    if (response.ok) {
      ElMessage({ message: '系统配置已实时生效', type: 'success', plain: true })
      // 刷新日志
      const logRes = await fetch('http://localhost:9080/api/settings/logs')
      if (logRes.ok) logs.value = await logRes.json()
    } else {
      const err = await response.json()
      ElMessage.error(err.detail || '配置更新失败')
    }
  } catch (err) {
    ElMessage.error('无法同步至服务器，请检查后端网络')
  }
}

// 默认显示字段用专用接口（数组值）
const saveDefaultFields = async () => {
  try {
    const response = await fetch('http://localhost:9080/api/settings/default-fields', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fields: configForm.default_visible_fields }),
    })

    if (response.ok) {
      ElMessage({ message: '默认显示字段已更新', type: 'success', plain: true })
      const logRes = await fetch('http://localhost:9080/api/settings/logs')
      if (logRes.ok) logs.value = await logRes.json()
    } else {
      const err = await response.json()
      ElMessage.error(err.detail || '字段更新失败')
    }
  } catch (err) {
    ElMessage.error('无法同步至服务器')
  }
}

// ═════════════════════════════════════════════════════════════
//  用户管理方法（保持不变）
// ═════════════════════════════════════════════════════════════
const fetchUsers = async () => {
  const token = localStorage.getItem('token')
  if (!token) return
  userLoading.value = true
  try {
    const res = await fetch('http://localhost:9080/api/admin/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, status: userStatusFilter.value }),
    })
    if (res.ok) {
      const data = await res.json()
      userList.value = data.users || []
    } else if (res.status === 403) {
      ElMessage.error('管理员权限验证失败，请重新登录')
    } else {
      const err = await res.json()
      ElMessage.error(err.detail || '获取用户列表失败')
    }
  } catch (e) {
    ElMessage.error('无法连接后端，获取用户列表失败')
  } finally {
    userLoading.value = false
  }
}

const handleApprove = async (username, action) => {
  const token = localStorage.getItem('token')
  const label = action === 'approve' ? '通过' : '拒绝'
  try {
    await ElMessageBox.confirm(
      `确认${label}用户「${username}」的注册申请？`,
      '审批确认',
      { confirmButtonText: `确认${label}`, cancelButtonText: '取消', type: 'warning' },
    )
    const res = await fetch('http://localhost:9080/api/admin/approve-user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, username, action }),
    })
    if (res.ok) {
      ElMessage.success(`已${label}`)
      fetchUsers()
    } else {
      const err = await res.json()
      ElMessage.error(err.detail || '操作失败')
    }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('审批操作失败')
  }
}

const handleDeleteUser = async (username) => {
  const token = localStorage.getItem('token')
  try {
    await ElMessageBox.confirm(
      `确定要删除用户「${username}」吗？此操作不可恢复。`,
      '删除确认',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'error' },
    )
    const res = await fetch('http://localhost:9080/api/admin/delete-user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, username }),
    })
    if (res.ok) {
      ElMessage.success(`用户 ${username} 已删除`)
      fetchUsers()
    } else {
      const err = await res.json()
      ElMessage.error(err.detail || '删除失败')
    }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除操作失败')
  }
}

const handleToggleStatus = async (username, action) => {
  const token = localStorage.getItem('token')
  const label = action === 'disable' ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确认${label}用户「${username}」？`,
      '操作确认',
      { confirmButtonText: `确认${label}`, cancelButtonText: '取消', type: 'warning' },
    )
    const res = await fetch('http://localhost:9080/api/admin/toggle-user-status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, username, action }),
    })
    if (res.ok) {
      ElMessage.success(`已${label}`)
      fetchUsers()
    } else {
      const err = await res.json()
      ElMessage.error(err.detail || '操作失败')
    }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(`${label}操作失败`)
  }
}

const handleSetRole = async (row) => {
  const token = localStorage.getItem('token')
  const currentRole = row.role
  const newRole = currentRole === 'admin' ? 'user' : 'admin'
  const roleLabel = newRole === 'admin' ? '管理员' : '普通用户'
  try {
    await ElMessageBox.confirm(
      `确认将用户「${row.username}」的角色从「${currentRole === 'admin' ? '管理员' : '普通用户'}」改为「${roleLabel}」？`,
      '权限设置',
      { confirmButtonText: '确认更改', cancelButtonText: '取消', type: 'warning' },
    )
    const res = await fetch('http://localhost:9080/api/admin/set-user-role', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, username: row.username, role: newRole }),
    })
    if (res.ok) {
      ElMessage.success(`用户 ${row.username} 已设为${roleLabel}`)
      fetchUsers()
    } else {
      const err = await res.json()
      ElMessage.error(err.detail || '操作失败')
    }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('权限设置失败')
  }
}

// 密码修改逻辑
// 密码修改逻辑
const handlePasswordUpdate = async () => {
  if (!pwdForm.newPassword || !pwdForm.confirmPassword) {
    return ElMessage.warning('请填写新密码')
  }
  if (pwdForm.newPassword !== pwdForm.confirmPassword) {
    return ElMessage.error('两次密码输入不一致')
  }
  if (pwdForm.newPassword.length < 6) {
    return ElMessage.warning('密码长度不能少于6位')
  }

  pwdLoading.value = true
  try {
    const response = await fetch('http://localhost:9080/api/settings/update_password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_password: pwdForm.newPassword }),
    })
    const res = await response.json()
    if (response.ok) {
      ElMessage.success('管理员密码已修改，请妥善保管')
      showPasswordDialog.value = false
      pwdForm.newPassword = ''
      pwdForm.confirmPassword = ''
    } else {
      ElMessage.error(res.detail || '密码修改失败')
    }
  } catch (err) {
    ElMessage.error('无法连接服务器，请检查后端网络')
  } finally {
    pwdLoading.value = false
  }
}
</script>

<style scoped>
.system-wrapper {
  background-color: #f5f7fa;
  min-height: 100vh;
}

.top-bar {
  background: #fff;
  padding: 0 40px;
  height: 64px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #dcdfe6;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.top-bar .left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.back-icon {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
  transition: color 0.3s;
}
.back-icon:hover { color: #409eff; }

.title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.main-content {
  padding: 30px 40px;
}

.settings-card {
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #606266;
  margin: 25px 0 20px 0;
  padding-left: 10px;
  border-left: 4px solid #409eff;
}

.input-with-tip {
  display: flex;
  flex-direction: column;
}

.tip-text {
  font-size: 12px;
  color: #909399;
  line-height: 2;
}

/* ── 字段管理 ── */
.field-manager {
  width: 100%;
}

.field-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f0f7ff;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.field-check-group {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px 12px;
}

.field-check-item {
  margin-right: 0 !important;
  padding: 4px 8px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  transition: all 0.2s;
  font-size: 13px;
}

.field-check-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

/* ── 日志样式 ── */
.log-container {
  padding: 20px 10px;
}
.log-user {
  font-weight: bold;
  margin-right: 10px;
  color: #409eff;
}
.log-action {
  color: #606266;
}

/* ── 覆盖 Element Tabs 样式 ── */
:deep(.el-tabs__item) {
  font-size: 15px;
  height: 50px;
}

@media (max-width: 1200px) {
  .field-check-group {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .field-check-group {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
