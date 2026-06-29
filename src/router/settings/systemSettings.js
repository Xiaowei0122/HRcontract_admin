import { reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

export function useSystemSettings() {
  const activeTab = ref('config')
  const showPasswordDialog = ref(false)
  const pwdLoading = ref(false)
  const pwdForm = reactive({
    newPassword: '',
    confirmPassword: '',
  })

  // ── 可用字段列表（从后端获取）──
  const availableFields = ref([])

  // ── 字段管理 ──
  const fieldDefinitions = ref([])       // 所有字段定义（基础 + 自定义）
  const baseFieldKeys = ref([])          // 基础字段 key 列表（不可删除）
  const showFieldDialog = ref(false)     // 新增/编辑字段弹窗
  const fieldForm = reactive({ key: '', label: '', fieldType: 'text', isEdit: false })
  const fieldTypeOptions = [
    { value: 'text', label: '文本' },
    { value: 'number', label: '数字' },
    { value: 'date', label: '日期' },
    { value: 'select', label: '下拉选择' },
  ]

  // ── 产品类别管理 ──
  const categories = ref([])             // 产品类别列表
  const categoryColors = ref({})         // 类别颜色映射
  const showCatDialog = ref(false)       // 新增/编辑类别弹窗
  const catForm = reactive({ name: '', index: -1, isEdit: false })

  // ── 签署公司管理 ──
  const signingCompanies = ref([])       // 签署公司列表
  const showSignCompanyDialog = ref(false)
  const signCompanyForm = reactive({ name: '', index: -1, isEdit: false })

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
    // 权限控制
    allow_user_delete: false,
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

  // ── 角色辅助函数 ──
  const roleTagType = (role) => {
    return { admin: 'danger', user: 'success', viewer: 'warning' }[role] || 'info'
  }
  const roleLabel = (role) => {
    return { admin: '管理员', user: '普通用户', viewer: '查看者' }[role] || role
  }
  const roleOptions = [
    { value: 'admin', label: '管理员 — 全部权限' },
    { value: 'user', label: '普通用户 — 可管理合同' },
    { value: 'viewer', label: '查看者 — 仅查看下载' },
  ]

  // ── 角色设置对话框 ──
  const showRoleDialog = ref(false)
  const roleTargetUser = ref(null)
  const selectedRole = ref('')

  // ── 操作日志 ──
  const logs = ref([])
  const logFilter = ref('all')
  const filteredLogs = ref([])
  const logPage = ref(1)
  const logPageSize = ref(20)
  const logTotal = ref(0)

  // 根据日志内容自动归类
  const getLogCategory = (log) => {
    const action = log.action || ''
    const user = log.user || ''
    if (user === 'system') return 'system'
    if (action.includes('合同') || action.includes('附件') || action.includes('导出')) return 'contract'
    if (action.includes('用户') || action.includes('注册') || action.includes('登录') || action.includes('密码') || action.includes('角色') || action.includes('禁用') || action.includes('启用') || action.includes('删除') && action.includes('用户')) return 'user'
    if (action.includes('配置') || action.includes('设置') || action.includes('字段') || action.includes('系统')) return 'settings'
    return 'system'
  }

  const getLogCategoryLabel = (log) => {
    const map = { contract: '合同操作', user: '用户管理', settings: '系统设置', system: '系统事件' }
    return map[getLogCategory(log)] || '系统事件'
  }

  const getLogTagType = (log) => {
    const map = { contract: 'primary', user: 'warning', settings: 'success', system: 'info' }
    return map[getLogCategory(log)] || 'info'
  }

  const getLogColor = (log) => {
    const map = { contract: '#409eff', user: '#e6a23c', settings: '#67c23a', system: '#909399' }
    return map[getLogCategory(log)] || '#909399'
  }

  const applyLogFilter = () => {
    if (logFilter.value === 'all') {
      filteredLogs.value = logs.value
    } else {
      filteredLogs.value = logs.value.filter(log => getLogCategory(log) === logFilter.value)
    }
  }

  // 分页加载日志
  const fetchLogs = async () => {
    try {
      const res = await fetch(
        `http://localhost:9080/api/settings/logs?page=${logPage.value}&pageSize=${logPageSize.value}`
      )
      if (res.ok) {
        const data = await res.json()
        logs.value = data.logs || []
        logTotal.value = data.total || 0
        applyLogFilter()
        console.log('✅ 操作日志已加载:', logs.value.length, '条 / 共', logTotal.value, '条')
      } else {
        console.error('❌ 操作日志加载失败:', res.status)
        logs.value = []
        filteredLogs.value = []
      }
    } catch (err) {
      console.error('❌ 获取日志失败:', err)
    }
  }

  const handleLogPageChange = (page) => {
    logPage.value = page
    fetchLogs()
  }

  const handleLogSizeChange = (size) => {
    logPageSize.value = size
    logPage.value = 1
    fetchLogs()
  }

  // ═════════════════════════════════════════════════════════════
  //  字段管理方法
  // ═════════════════════════════════════════════════════════════

  const fetchFieldDefinitions = async () => {
    try {
      const res = await fetch('http://localhost:9080/api/settings/field-definitions')
      if (res.ok) {
        const data = await res.json()
        fieldDefinitions.value = data.fields || []
        baseFieldKeys.value = data.baseFieldKeys || []
        console.log('✅ 字段定义已加载:', fieldDefinitions.value.length, '个')
      }
    } catch (e) { console.error('加载字段定义失败:', e) }
  }

  const openAddFieldDialog = () => {
    fieldForm.key = ''
    fieldForm.label = ''
    fieldForm.fieldType = 'text'
    fieldForm.isEdit = false
    showFieldDialog.value = true
  }

  const openEditFieldDialog = (field) => {
    fieldForm.key = field.key
    fieldForm.label = field.label
    fieldForm.fieldType = field.fieldType || 'text'
    fieldForm.isEdit = true
    showFieldDialog.value = true
  }

  const handleSaveField = async () => {
    if (!fieldForm.label.trim()) {
      ElMessage.warning('请输入字段显示名称')
      return
    }
    // 新增时必须校验字段标识
    if (!fieldForm.isEdit) {
      if (!fieldForm.key.trim()) {
        ElMessage.warning('请输入字段标识（英文）')
        return
      }
      if (!/^[a-zA-Z][a-zA-Z0-9_]*$/.test(fieldForm.key.trim())) {
        ElMessage.warning('字段标识必须以英文字母开头，只能包含英文字母、数字和下划线')
        return
      }
    }
    try {
      const body = { label: fieldForm.label, fieldType: fieldForm.fieldType, token: localStorage.getItem('token') }
      if (!fieldForm.isEdit) {
        body.key = fieldForm.key.trim()
      }
      let res
      if (fieldForm.isEdit) {
        res = await fetch(`http://localhost:9080/api/settings/custom-fields/${fieldForm.key}`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
        })
      } else {
        res = await fetch('http://localhost:9080/api/settings/custom-fields', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
        })
      }
      if (res.ok) {
        ElMessage.success(fieldForm.isEdit ? '字段已更新' : '自定义字段已新增')
        showFieldDialog.value = false
        await fetchFieldDefinitions()
        // 同步刷新 availableFields
        const fRes = await fetch('http://localhost:9080/api/settings/fields')
        if (fRes.ok) {
          const data = await fRes.json()
          availableFields.value = data.availableFields || []
        }
      } else {
        const err = await res.json()
        ElMessage.error(err.detail || '操作失败')
      }
    } catch (e) { ElMessage.error('网络请求失败') }
  }

  const handleDeleteField = async (field) => {
    if (!field.isCustom) {
      ElMessage.warning('基础字段不可删除')
      return
    }
    try {
      await ElMessageBox.confirm(`确定删除自定义字段「${field.label}」？`, '删除确认', {
        confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'error',
      })
      const res = await fetch(`http://localhost:9080/api/settings/custom-fields/${field.key}?token=${encodeURIComponent(localStorage.getItem('token'))}`, { method: 'DELETE' })
      if (res.ok) {
        ElMessage.success('字段已删除')
        await fetchFieldDefinitions()
        const fRes = await fetch('http://localhost:9080/api/settings/fields')
        if (fRes.ok) {
          const data = await fRes.json()
          availableFields.value = data.availableFields || []
        }
      } else {
        const err = await res.json()
        ElMessage.error(err.detail || '删除失败')
      }
    } catch (e) { if (e !== 'cancel') ElMessage.error('删除操作失败') }
  }

  // ═════════════════════════════════════════════════════════════
  //  产品类别管理方法
  // ═════════════════════════════════════════════════════════════

  const fetchCategories = async () => {
    try {
      const res = await fetch('http://localhost:9080/api/settings/categories')
      if (res.ok) {
        const data = await res.json()
        categories.value = data.categories || []
        categoryColors.value = data.categoryColors || {}
        console.log('✅ 产品类别已加载:', categories.value.length, '个')
      }
    } catch (e) { console.error('加载类别失败:', e) }
  }

  const openAddCatDialog = () => {
    catForm.name = ''
    catForm.index = -1
    catForm.isEdit = false
    showCatDialog.value = true
  }

  const openEditCatDialog = (index) => {
    catForm.name = categories.value[index]
    catForm.index = index
    catForm.isEdit = true
    showCatDialog.value = true
  }

  const handleSaveCategory = async () => {
    if (!catForm.name.trim()) {
      ElMessage.warning('请输入类别名称')
      return
    }
    try {
      const body = { name: catForm.name.trim(), token: localStorage.getItem('token') }
      let res
      if (catForm.isEdit) {
        res = await fetch(`http://localhost:9080/api/settings/categories/${catForm.index}`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
        })
      } else {
        res = await fetch('http://localhost:9080/api/settings/categories', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
        })
      }
      if (res.ok) {
        const data = await res.json()
        categories.value = data.categories || []
        categoryColors.value = data.categoryColors || {}
        ElMessage.success(catForm.isEdit ? '类别已更新' : '类别已新增')
        showCatDialog.value = false
      } else {
        const err = await res.json()
        ElMessage.error(err.detail || '操作失败')
      }
    } catch (e) { ElMessage.error('网络请求失败') }
  }

  const handleDeleteCategory = async (index) => {
    const name = categories.value[index]
    try {
      await ElMessageBox.confirm(`确定删除产品类别「${name}」？`, '删除确认', {
        confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'error',
      })
      const res = await fetch(`http://localhost:9080/api/settings/categories/${index}?token=${encodeURIComponent(localStorage.getItem('token'))}`, { method: 'DELETE' })
      if (res.ok) {
        const data = await res.json()
        categories.value = data.categories || []
        categoryColors.value = data.categoryColors || {}
        ElMessage.success('类别已删除')
      } else {
        const err = await res.json()
        ElMessage.error(err.detail || '删除失败')
      }
    } catch (e) { if (e !== 'cancel') ElMessage.error('删除操作失败') }
  }

  // ═════════════════════════════════════════════════════════════
  //  签署公司管理方法
  // ═════════════════════════════════════════════════════════════

  const fetchSigningCompanies = async () => {
    try {
      const res = await fetch('http://localhost:9080/api/settings/signing-companies')
      if (res.ok) {
        const data = await res.json()
        signingCompanies.value = data.signingCompanies || []
        console.log('✅ 签署公司已加载:', signingCompanies.value.length, '个')
      }
    } catch (e) { console.error('加载签署公司失败:', e) }
  }

  const openAddSignCompanyDialog = () => {
    signCompanyForm.name = ''
    signCompanyForm.index = -1
    signCompanyForm.isEdit = false
    showSignCompanyDialog.value = true
  }

  const openEditSignCompanyDialog = (index) => {
    signCompanyForm.name = signingCompanies.value[index]
    signCompanyForm.index = index
    signCompanyForm.isEdit = true
    showSignCompanyDialog.value = true
  }

  const handleSaveSignCompany = async () => {
    if (!signCompanyForm.name.trim()) {
      ElMessage.warning('请输入公司名称')
      return
    }
    try {
      const body = { name: signCompanyForm.name.trim(), token: localStorage.getItem('token') }
      let res
      if (signCompanyForm.isEdit) {
        res = await fetch(`http://localhost:9080/api/settings/signing-companies/${signCompanyForm.index}`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
        })
      } else {
        res = await fetch('http://localhost:9080/api/settings/signing-companies', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
        })
      }
      if (res.ok) {
        const data = await res.json()
        signingCompanies.value = data.signingCompanies || []
        ElMessage.success(signCompanyForm.isEdit ? '签署公司已更新' : '签署公司已新增')
        showSignCompanyDialog.value = false
      } else {
        const err = await res.json()
        ElMessage.error(err.detail || '操作失败')
      }
    } catch (e) { ElMessage.error('网络请求失败') }
  }

  const handleDeleteSignCompany = async (index) => {
    const name = signingCompanies.value[index]
    try {
      await ElMessageBox.confirm(`确定删除签署公司「${name}」？`, '删除确认', {
        confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'error',
      })
      const res = await fetch(`http://localhost:9080/api/settings/signing-companies/${index}?token=${encodeURIComponent(localStorage.getItem('token'))}`, { method: 'DELETE' })
      if (res.ok) {
        const data = await res.json()
        signingCompanies.value = data.signingCompanies || []
        ElMessage.success('签署公司已删除')
      } else {
        const err = await res.json()
        ElMessage.error(err.detail || '删除失败')
      }
    } catch (e) { if (e !== 'cancel') ElMessage.error('删除操作失败') }
  }

  // ═════════════════════════════════════════════════════════════
  //  初始化
  // ═════════════════════════════════════════════════════════════
  const fetchInitialData = async () => {
    try {
      // 并发拉取：系统配置 + 可用字段
      const [configRes, fieldsRes] = await Promise.all([
        fetch('http://localhost:9080/api/settings/'),
        fetch('http://localhost:9080/api/settings/fields'),
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

      // 日志独立分页加载
      await fetchLogs()
      // 字段定义 + 产品类别 + 签署公司
      await Promise.all([fetchFieldDefinitions(), fetchCategories(), fetchSigningCompanies()])
    } catch (err) {
      console.error('❌ 系统设置初始化失败:', err)
      ElMessage.error('系统设置初始化失败，请检查后端服务')
    }
  }

  // ═════════════════════════════════════════════════════════════
  //  配置保存
  // ═════════════════════════════════════════════════════════════
  const saveConfig = async (key, value) => {
    const token = localStorage.getItem('token')
    try {
      const response = await fetch('http://localhost:9080/api/settings/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value, token }),
      })

      if (response.ok) {
        ElMessage({ message: '系统配置已实时生效', type: 'success', plain: true })
        // 刷新日志
        logPage.value = 1
        await fetchLogs()
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
    const token = localStorage.getItem('token')
    try {
      const response = await fetch('http://localhost:9080/api/settings/default-fields', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields: configForm.default_visible_fields, token }),
      })

      if (response.ok) {
        ElMessage({ message: '默认显示字段已更新', type: 'success', plain: true })
        const logRes = await fetch('http://localhost:9080/api/settings/logs')
        if (logRes.ok) { logs.value = await logRes.json(); applyLogFilter() }
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

  const handleSetRole = (row) => {
    roleTargetUser.value = row
    selectedRole.value = row.role
    showRoleDialog.value = true
  }

  const confirmSetRole = async () => {
    const token = localStorage.getItem('token')
    const row = roleTargetUser.value
    if (!row || selectedRole.value === row.role) {
      showRoleDialog.value = false
      return
    }
    try {
      const res = await fetch('http://localhost:9080/api/admin/set-user-role', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, username: row.username, role: selectedRole.value }),
      })
      if (res.ok) {
        ElMessage.success(`用户 ${row.username} 的角色已设为「${roleLabel(selectedRole.value)}」`)
        showRoleDialog.value = false
        fetchUsers()
      } else {
        const err = await res.json()
        ElMessage.error(err.detail || '操作失败')
      }
    } catch (e) {
      ElMessage.error('权限设置失败')
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

  return {
    activeTab, showPasswordDialog, pwdLoading, pwdForm,
    availableFields, configForm,
    // 字段管理
    fieldDefinitions, baseFieldKeys, showFieldDialog, fieldForm, fieldTypeOptions,
    openAddFieldDialog, openEditFieldDialog, handleSaveField, handleDeleteField,
    // 产品类别管理
    categories, categoryColors, showCatDialog, catForm,
    openAddCatDialog, openEditCatDialog, handleSaveCategory, handleDeleteCategory,
    // 签署公司管理
    signingCompanies, showSignCompanyDialog, signCompanyForm,
    openAddSignCompanyDialog, openEditSignCompanyDialog, handleSaveSignCompany, handleDeleteSignCompany,
    userList, userStatusFilter, userLoading,
    statusTagType, statusLabel,
    roleTagType, roleLabel, roleOptions,
    showRoleDialog, roleTargetUser, selectedRole,
    logs, logFilter, filteredLogs,
    logPage, logPageSize, logTotal,
    getLogCategoryLabel, getLogTagType, getLogColor,
    applyLogFilter, fetchLogs, handleLogPageChange, handleLogSizeChange,
    fetchInitialData, fetchUsers,
    saveConfig, saveDefaultFields,
    handleApprove, handleDeleteUser, handleToggleStatus,
    handleSetRole, confirmSetRole,
    handlePasswordUpdate,
  }
}
