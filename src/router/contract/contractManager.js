import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Files, Money, Check, Timer } from '@element-plus/icons-vue'
import Chart from 'chart.js/auto'
import axios from 'axios'
import { useRouter } from 'vue-router'
import CryptoJS from 'crypto-js'

export function useContractManager() {

//登录退出逻辑
const router = useRouter()

// 获取当前登录状态
const userRole = ref(localStorage.getItem('userRole') || 'visitor')
const isGuest = ref(localStorage.getItem('isGuest') === 'true')
const realName = ref(localStorage.getItem('realName') || localStorage.getItem('username') || '用户')

// 修改密码对话框（普通用户和子管理员可用）
const showChangePwdDialog = ref(false)
const changePwdLoading = ref(false)
const changePwdForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})
// 判断当前登录用户是否为超级管理员
const isSuperAdmin = computed(() => localStorage.getItem('username') === 'admin')

// 角色标签文字和颜色
const roleLabel = computed(() => {
  if (isGuest.value) return '访客预览模式'
  if (userRole.value === 'admin') return '系统管理员'
  return `用户: ${realName.value}`
})
const roleTagType = computed(() => {
  if (isGuest.value) return 'warning'
  if (userRole.value === 'admin') return 'danger'
  return 'success'
})

// 退出登录逻辑
const handleLogout = () => {
  ElMessageBox.confirm('确定要退出系统并返回登录页面吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
    buttonSize: 'default'
  }).then(async () => {
    try {
      const currentToken = localStorage.getItem('token')
      const currentUsername = localStorage.getItem('username')
      await fetch('http://localhost:9080/api/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: currentToken, username: currentUsername })
      })
    } catch (e) {
      console.warn("后端退出接口调用失败，执行本地强制清理")
    }
    // 清除本地存储的状态
    localStorage.removeItem('userRole')
    localStorage.removeItem('isGuest')
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('admin_token')

    ElMessage.success('已安全退出')
    router.push('/login')
  }).catch(() => {})
}

// 强制退出（不弹确认框，用于 token 失效 / 会话超时）
const forceLogout = async () => {
  try {
    const currentToken = localStorage.getItem('token')
    const currentUsername = localStorage.getItem('username')
    await fetch('http://localhost:9080/api/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: currentToken, username: currentUsername })
    })
  } catch (e) { /* 忽略 */ }
  localStorage.removeItem('userRole')
  localStorage.removeItem('isGuest')
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('admin_token')
  router.push('/login')
}

// ── Token 有效性校验（页面加载时调用）──
const verifyToken = async () => {
  const token = localStorage.getItem('token')
  if (!token) {
    // 访客模式不需要 token
    if (localStorage.getItem('isGuest') === 'true') return true
    return false
  }
  try {
    const res = await fetch('http://localhost:9080/api/verify-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    })
    if (res.ok) {
      const data = await res.json()
      // 同步后端最新角色和真实姓名到 localStorage
      localStorage.setItem('userRole', data.userRole)
      localStorage.setItem('realName', data.realName)
      userRole.value = data.userRole
      realName.value = data.realName
      return true
    }
    // Token 无效或账号已被禁用/删除
    const err = await res.json().catch(() => ({}))
    ElMessage.error(err.detail || '登录凭证已失效，请重新登录')
    await forceLogout()
    return false
  } catch (e) {
    // 网络不通时不强制退出，允许离线查看（但后续 API 调用会失败）
    console.warn('⚠️ Token 校验失败（网络异常），跳过校验')
    return true
  }
}

// ── 会话超时控制 ──
let lastActivityTime = Date.now()
let sessionTimeoutMinutes = 0  // 0 = 不限
let timeoutCheckInterval = null

const resetActivityTimer = () => {
  lastActivityTime = Date.now()
}

const startSessionTimeout = (timeoutMinutes) => {
  sessionTimeoutMinutes = timeoutMinutes
  // 清除旧定时器
  if (timeoutCheckInterval) clearInterval(timeoutCheckInterval)
  if (timeoutMinutes <= 0) return  // 不限时

  // 每 30 秒检查一次
  timeoutCheckInterval = setInterval(() => {
    const idleMs = Date.now() - lastActivityTime
    if (idleMs > timeoutMinutes * 60 * 1000) {
      console.warn(`⏰ 会话超时（闲置 ${Math.round(idleMs / 60000)} 分钟），强制退出`)
      ElMessage.warning(`您已闲置超过 ${timeoutMinutes} 分钟，系统已自动退出`)
      if (timeoutCheckInterval) clearInterval(timeoutCheckInterval)
      forceLogout()
    }
  }, 30000)
}

// 监听用户活动
if (typeof window !== 'undefined') {
  window.addEventListener('mousemove', resetActivityTimer, { passive: true })
  window.addEventListener('keydown', resetActivityTimer, { passive: true })
  window.addEventListener('click', resetActivityTimer, { passive: true })
  window.addEventListener('scroll', resetActivityTimer, { passive: true })
}

// 主页修改密码（普通用户和子管理员可用，需验证原密码）
const handleUserChangePassword = async () => {
  if (!changePwdForm.oldPassword) {
    return ElMessage.warning('请输入原密码')
  }
  if (!changePwdForm.newPassword || !changePwdForm.confirmPassword) {
    return ElMessage.warning('请填写新密码')
  }
  if (changePwdForm.newPassword !== changePwdForm.confirmPassword) {
    return ElMessage.error('两次密码输入不一致')
  }
  if (changePwdForm.newPassword.length < 6) {
    return ElMessage.warning('密码长度不能少于6位')
  }

  changePwdLoading.value = true
  try {
    const oldHash = CryptoJS.SHA256(changePwdForm.oldPassword).toString()
    const newHash = CryptoJS.SHA256(changePwdForm.newPassword).toString()
    const response = await fetch('http://localhost:9080/api/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: localStorage.getItem('username'),
        oldPassword: oldHash,
        newPassword: newHash,
      }),
    })
    const res = await response.json()
    if (response.ok) {
      ElMessage.success('密码修改成功')
      showChangePwdDialog.value = false
      changePwdForm.oldPassword = ''
      changePwdForm.newPassword = ''
      changePwdForm.confirmPassword = ''
    } else {
      ElMessage.error(res.detail || '密码修改失败')
    }
  } catch (err) {
    ElMessage.error('无法连接服务器，请检查后端网络')
  } finally {
    changePwdLoading.value = false
  }
}

// --- 基础数据（优先从后端加载，失败则使用默认值）---
const categories = ref(["计算机设备", "办公用品", "电子产品", "福利产品", "劳保用品", "办公耗材", "网络安防", "维修维护服务"])
const customerTypes = ref(["高校", "党政机关", "国企", "央企", "事业单位", "民营企业"])
const signingCompanies = ref(["鸿瑞办公", "政通慧采", "众冠供应链"])
const contractTypes = ref(["销售合同", "采购合同", "服务合同"])
const categoryColorMap = ref({"计算机设备": "#3b82f6","办公用品": "#10b981","电子产品": "#f59e0b", "福利产品": "#ef4444",  "劳保用品": "#f97316",  "办公耗材": "#8b5cf6",  "网络安防": "#06b6d4",  "维修维护服务": "#ec4899"})
const statusList = ["草稿", "待签署", "已签署", "已终止"]
const statusTagMap = { '已签署': 'success', '待签署': 'warning', '草稿': 'info', '已终止': 'danger' }


// --- 请求主要数据与状态 ---
const contracts = ref([])
const allContractsData = ref([]) // 💡 新增：专门用来喂给图表和顶部统计的全量数据
const categoryStatistics = ref({}) // 新增：存储分类统计数据
const totalAmount = ref(0)
const archivedCount = ref(0)
const activeCount = ref(0)
const contractCount = ref(0)
const loading = ref(false)
const selectedFile = ref(null)
const fileList = ref([])
// 获取合同数据的核心逻辑
const fetchTableData = async () => {
  loading.value = true
  let role = localStorage.getItem('userRole') || 'visitor'

  // 🔧 管理员开启「访客全部开放」后，访客以管理员权限拉取全量数据（前端 UI 仍限制编辑）
  if (role !== 'admin' && sysConfig.guest_full_access) {
    role = 'admin'
  }

  try {
    // -------------------------------------------------------------
    // 1. 构建参数（大看板统计和底部分页表格公用同一套筛选框参数，保证联动）
    // -------------------------------------------------------------
    const params = new URLSearchParams();
    params.append('role', role);
    if (filters.keyword) params.append('keyword', filters.keyword.trim());
    if (filters.category) params.append('category', filters.category);
    if (filters.contractType) params.append('contractType', filters.contractType);
    if (filters.customerType) params.append('customerType', filters.customerType);
    if (filters.status) params.append('status', filters.status);
    if (filters.minAmount !== null && filters.minAmount !== undefined && filters.minAmount !== '') {
      params.append('minAmount', filters.minAmount);
    }
    if (filters.maxAmount !== null && filters.maxAmount !== undefined && filters.maxAmount !== '') {
      params.append('maxAmount', filters.maxAmount);
    }

    // 表格专属的切片参数（每次只要 10 条，分页绝对正常！）
    const pageParams = new URLSearchParams(params);
    pageParams.append('page', currentPage.value);
    pageParams.append('size', pageSize.value);

    // -------------------------------------------------------------
    // 2. 并发派发两个请求：一个要10条表格JSON，一个要大看板纯数字统计
    // -------------------------------------------------------------
    const [pageRes, statsRes] = await Promise.all([
      fetch(`http://localhost:9080/api/contracts?${pageParams.toString()}`),
      fetch(`http://localhost:9080/api/contracts/dashboard-stats?${params.toString()}`)
    ])

    if (pageRes.ok && statsRes.ok) {
      const pageData = await pageRes.json()
      const statsData = await statsRes.json()

      //console.log("📋 底部分页表格切片数据:", pageData)
      //console.log("📊 顶部大看板轻量纯数字统计:", statsData)

      // A. 表格赋值（保持你最原始无误的解构）
      if (pageData && typeof pageData === 'object' && 'list' in pageData) {
        contracts.value = pageData.list || []
        totalCount.value = pageData.total || 0
      } else if (Array.isArray(pageData)) {
        contracts.value = pageData
        totalCount.value = pageData.length
      }

      // B. 🌟 大看板卡片纯数字直接赋值（完全还原你最初定义的变量）
      totalAmount.value = statsData.totalAmount || 0
      contractCount.value = statsData.totalCount || 0
      archivedCount.value = statsData.archivedCount || 0
      activeCount.value = statsData.activeCount || 0
      // 这里的全局条数如果你上方卡片有用，也可以赋值：dashboardTotal.value = statsData.totalCount

      // C. 🌟 饼图重绘：直接把后端算好的轻量分类映射表给到画图函数
      categoryStatistics.value = statsData.categoryStats || {}
      updateChart(categoryStatistics.value)
    } else {
      // 🚫 401 = token 失效，强制退出；403 = 权限不足（不退出，只提示）
      if (pageRes.status === 401 || statsRes.status === 401) {
        console.warn('🔒 Token 已失效，强制退出登录')
        ElMessage.error('登录凭证已失效，请重新登录')
        await forceLogout()
        return
      }
      if (pageRes.status === 403 || statsRes.status === 403) {
        ElMessage.error('权限不足，无法获取数据')
      }
      console.error('数据请求失败:', pageRes.status, statsRes.status)
    }
  } catch (error) {
    console.error("筛选联动失败:", error)
  } finally {
    loading.value = false
  }
}



// --- 弹窗逻辑整合 ---
const modalVisible = ref(false)
const form = reactive({
  // 1. 唯一标识：改为 contractId，初始给空字符串
  contractId: '',
  name: '',
  contractNo: '',
  contractType: '销售合同',
  category: '',
  customerType: '',
  customer: '',
  signingCompany: '',  // 新增：签署公司
  contactPerson: '',
  contactPhone: '',
  servicePeriod: '',
  signDate: '',
  amount: 0,
  status: '草稿',
  remark: '',
  createTime: '',
  updateTime: '',
  fileUrl: ''
})

const handleOpenModal = (row = null) => {
  selectedFile.value = null
  fileList.value = []

  // 先清空所有自定义字段值
  customFieldDefs.value.forEach(f => {
    form[f.key] = undefined
  })

  if (row) {
    Object.assign(form, { ...row })

    // 回填自定义字段值
    if (row.customFields && typeof row.customFields === 'object') {
      Object.entries(row.customFields).forEach(([k, v]) => {
        form[k] = v
      })
    }

    // 💡 彻底防空：过滤掉可能遗留的 "undefined" 伪值
    if (row._id && String(row._id).trim() !== 'undefined') {
      const idStr = typeof row._id === 'object' ? (row._id.$oid || JSON.stringify(row._id)) : String(row._id);
      const match = idStr.match(/[0-9a-fA-F]{24}/);
      form._id = match ? match[0] : '';
    } else {
      form._id = '';
    }

    form.contractId = row.contractId || row.contractNo || ''
  } else {
    const now = new Date()
    const prefix = sysConfig.contract_id_prefix || 'HT'
    const uniqueId = `${prefix}${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}${String(now.getMilliseconds()).padStart(3, '0')}`

    Object.assign(form, {
      _id: '',
      contractId: uniqueId,
      name: '',
      contractType: '销售合同',
      category: '',
      signingCompany: '',
      customerType: '',
      customer: '',
      contactPerson: '',
      contactPhone: '',
      servicePeriod: '',
      signDate: '',
      amount: 0,
      status: '草稿',
      remark: ''
    })
  }
  modalVisible.value = true
}

const handleFileBeforeUpload = (file) => {
  selectedFile.value = file
  fileList.value = [file]
  // 仅在合同名称为空时自动识别文件名（编辑时不覆盖已有名称）
  if (!form.name || form.name.trim() === '') {
    const fileName = file.name.substring(0, file.name.lastIndexOf('.'))
    form.name = fileName
    ElMessage.success(`自动识别：已填充合同名称为 "${fileName}"`)
  }
  return false
}

const handleFileChange = (file, fileListArg) => {
  selectedFile.value = file.raw || file
  fileList.value = fileListArg
}

const handleUploadRemove = () => {
  selectedFile.value = null
  fileList.value = []
}

const isSubmitting = ref(false)

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1   // 切换每页条数时，自动重置回第一页
  fetchTableData()        // 💡 关键：条数变了，立刻命令后端重新查询
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchTableData()        // 💡 关键：页码变了，立刻让后端去捞对应页的数据
}

const handleSave = async () => {
  console.log("1. 启用保存，准备提交数据");
  try {
    loading.value = true;
    isSubmitting.value = true;

    const formData = new FormData();

    // 确保传输给后端的业务编号绝对纯净
    formData.append('contractId', form.contractId);
    formData.append('contractNo', form.contractId);

    formData.append('name', form.name || '');
    formData.append('category', form.category || '');
    formData.append('amount', parseFloat(form.amount) || 0);
    formData.append('status', form.status || '草稿');
    formData.append('customer', form.customer || '');
    formData.append('signingCompany', form.signingCompany || '');
    formData.append('customerType', form.customerType || '');
    formData.append('contractType', form.contractType || '');
    formData.append('contactPerson', form.contactPerson || '');
    formData.append('contactPhone', form.contactPhone || '');
    formData.append('signDate', form.signDate || '');
    formData.append('servicePeriod', form.servicePeriod || '');
    formData.append('remark', form.remark || '');
    formData.append('operator', localStorage.getItem('realName') || localStorage.getItem('username') || 'admin');

    // 收集自定义字段值
    const customFieldsData = {}
    customFieldDefs.value.forEach(f => {
      if (form[f.key] !== undefined && form[f.key] !== null && form[f.key] !== '') {
        customFieldsData[f.key] = form[f.key]
      }
    })
    if (Object.keys(customFieldsData).length > 0) {
      formData.append('customFields', JSON.stringify(customFieldsData))
    }

    // 💡 健壮修复：全方位拦截任何形式的空值或 "undefined" 伪字符串
    let rawId = '';
    if (form._id && String(form._id).trim() !== 'undefined') {
      const idStr = typeof form._id === 'object'
        ? (form._id.$oid || JSON.stringify(form._id))
        : String(form._id);

      // 必须符合 24 位 MongoDB ObjectId 规范 (0-9, a-f)
      const match = idStr.match(/[0-9a-fA-F]{24}/);
      rawId = match ? match[0] : '';
    }

    // 💡 只有真正拥有 24 位数据库特征 ID 的才判定为编辑修改模式
    const isEdit = !!rawId;

    // 🔧 编辑模式下：如果合同已有文件且用户又选了新文件，弹窗确认是否覆盖
    let shouldUploadFile = fileList.value.length > 0;
    if (isEdit && shouldUploadFile && form.fileUrl) {
      try {
        await ElMessageBox.confirm(
          '合同文件已存在，是否更新当前合同文件？',
          '文件覆盖确认',
          { confirmButtonText: '是，更新文件', cancelButtonText: '否', type: 'warning' }
        );
        // 用户确认 — 继续上传新文件
      } catch {
        // 用户取消 — 跳过文件上传
        shouldUploadFile = false;
      }
    }

    if (shouldUploadFile) {
      formData.append('file', fileList.value[0].raw);
    }

    const url = isEdit
      ? `http://localhost:9080/api/contracts/${rawId}`
      : `http://localhost:9080/api/contracts/upload`;

    const method = isEdit ? 'put' : 'post';
    console.log(`[数据网络同步] 操作模式: ${isEdit ? '修改' : '新建'}, 最终路由: ${url}`);

    const response = await axios[method](url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    if (response.data.status === 'success') {
      ElMessage.success('合同档案数据同步成功');
      modalVisible.value = false;
      fileList.value = [];
      fetchTableData();
    }
  } catch (error) {
    console.error("提交异常详情:", error);
    const errorDetail = error.response?.data?.detail;
    let errorMsg = '数据更新失败';
    if (Array.isArray(errorDetail)) {
        errorMsg = `${errorDetail[0].loc[1]}: ${errorDetail[0].msg}`;
    } else if (typeof errorDetail === 'string') {
        errorMsg = errorDetail;
    }
    ElMessage.error(errorMsg);
  } finally {
    loading.value = false;
    isSubmitting.value = false;
  }
};

// 删除合同
const handleDelete = async (row) => {
  // 💡 健壮修复：提取多层嵌套，同时阻断 "undefined"
  let rawId = '';
  const sourceId = row._id || row.id;

  if (sourceId && String(sourceId).trim() !== 'undefined') {
    const idStr = typeof sourceId === 'object'
      ? (sourceId.$oid || JSON.stringify(sourceId))
      : String(sourceId);
    const match = idStr.match(/[0-9a-fA-F]{24}/);
    rawId = match ? match[0] : '';
  }

  // 💡 如果实在拿不到 24 位主键，则拿新版的 contractId 去匹配删除（作为后备降级手段）
  const fallbackId = rawId || row.contractId || row.contractNo;

  if (!fallbackId || fallbackId === 'undefined') {
    ElMessage.error('无法提取该合同的有效标识符，删除中止');
    return;
  }

  try {
    await ElMessageBox.confirm('确定要永久移出该合同及关联附件吗？', '系统警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    loading.value = true;
    const op = encodeURIComponent(localStorage.getItem('realName') || localStorage.getItem('username') || 'admin');
    const response = await fetch(`http://localhost:9080/api/contracts/${fallbackId}?operator=${op}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      ElMessage.success('合同档案已成功移出系统');
      fetchTableData();
    } else {
      const errorData = await response.json();
      throw new Error(errorData.detail || '删除失败');
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除请求失败：' + error.message);
    }
  } finally {
    loading.value = false;
  }
}

// 单独下载附件
const handleDownload = async (row) => {
  if (!row.contractId) {
    ElMessage.error('该合同数据没有关联的唯一编号(contractId)');
    return;
  }

  // 💡 直接导航下载，不用 fetch+blob，避免 Chrome HTTP blob 安全警告
  const downloadApiUrl = `/api/contracts/download-by-id/${row.contractId}`;
  const a = document.createElement('a');
  a.href = downloadApiUrl;
  a.download = row.name ? `${row.name}.pdf` : `合同_${row.contractId}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};


// --- 批量选择与下载逻辑 ---
const selectedRows = ref([]) // 💡 存放勾选的合同行数据

// 表格多选框改变时的回调
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

// 执行批量下载
const handleBatchDownload = async () => {
  if (selectedRows.value.length === 0) return;

  // 1. 提取 ID：优先用唯一 contractId 驱动逻辑
  const contractIds = selectedRows.value.map(row => {
    return row.contractId || row.contractNo || row._id;
  }).filter(Boolean);

  if (contractIds.length === 0) {
    ElMessage.error('选中的合同数据不完整，无法获取文件编号');
    return;
  }

  try {
    ElMessage.info('系统正在为您打包文件，请稍候...');
    const params = new URLSearchParams();

    // 将兼容后得到的真实 ID 逐个追加到 URL 参数中
    contractIds.forEach(id => params.append('contract_ids', id));
    params.append('operator', localStorage.getItem('realName') || localStorage.getItem('username') || 'admin');

    // 💡 直接导航下载，不用 fetch+blob，避免 Chrome HTTP blob 安全警告
    const batchDownloadUrl = `/api/contracts/batch-download?${params.toString()}`;
    const a = document.createElement('a');
    a.href = batchDownloadUrl;
    const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    a.download = `合同批量下载_${dateStr}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } catch (error) {
    console.error('批量下载流捕获异常:', error);
    // 🌟 核心修复：用户看不懂群晖 Container，改成指导他们检查网络或联系管理员 🌟
    ElMessage.error('下载失败，请检查网络连接或联系系统管理员');
  }
};


// 翻页组件
// --- 1. 基础状态 ---
// --- 翻页组件所需的核心状态 ---
const sysConfig = reactive({
  guest_data_limit: 2,
  maintenance_mode: false,
  guest_full_access: false,
  show_dashboard_charts: true,
  big_amount_threshold: 100,
  default_visible_fields: [],
  contract_id_prefix: 'HT',
  allow_user_delete: false,
})
const currentPage = ref(1)
const pageSize = ref(10)
const totalCount = ref(0) // 💡 变成响应式变量，由第二步的 fetchTableData 统一赋值

// --- 表格渲染计算属性 ---
// 直接返回后端过滤后的数据，不在前端再做过滤
// 后端已经根据 keyword、category、contractType、customerType、amount 等条件过滤好了
const displayedTableData = computed(() => {
  return contracts.value || []
})

// --- 统计/筛选/显示逻辑 ---
const toggleField = (k) => {
  const i = visibleFields.value.indexOf(k);
  i > -1 ? visibleFields.value.splice(i, 1) : visibleFields.value.push(k);
  // 保存用户偏好到本地，下次进入以用户选择为准
  localStorage.setItem('visibleFields', JSON.stringify(visibleFields.value));
}
const statistics = computed(() => [
  { title: '合同总量', value: contractCount.value, unit: '份', icon: Files, color: '#3b82f6' },
  { title: '累计总金额', value: totalAmount.value.toFixed(1), unit: '万', icon: Money, color: '#ef4444' },
  { title: '已签署', value: archivedCount.value, unit: '份', icon: Check, color: '#10b981' },
  { title: '待处理', value: activeCount.value, unit: '份', icon: Timer, color: '#f59e0b' }
])

const visibleFields = ref(['contractId', 'name', 'category', 'contractType', 'customer', 'customerType','signingCompany', 'amount', 'status', 'signDate'])
const allFields = ref([
  { key: 'name', label: '合同名称' },
  { key: 'contractId', label: '合同ID '},
  { key: 'contractType', label: '合同类型' },
  { key: 'category', label: '产品类别' },
  { key: 'customerType', label: '客户类别' },
  { key: 'customer', label: '客户名称' },
  { key: 'signingCompany', label: '签署公司' },
  { key: 'contactPerson', label: '联系人' },
  { key: 'contactPhone', label: '联系电话' },
  { key: 'servicePeriod', label: '服务期限' },
  { key: 'signDate', label: '签订日期' },
  { key: 'amount', label: '合同金额(元)' },
  { key: 'status', label: '状态' },
  { key: 'remark', label: '备注' },
  { key: 'createTime', label: '创建时间' },
  { key: 'updateTime', label: '更新时间' },
  { key: 'contractNo', label: '合同编号' },
  { key: 'operator', label: '最后操作人'}
])
const activeColumns = computed(() => allFields.value.filter(f => visibleFields.value.includes(f.key)))
// 自定义字段列表（从 allFields 中过滤 isCustom 标记的）
const customFieldDefs = computed(() => allFields.value.filter(f => f.isCustom))
// 新增：扩展filters对象以支持多维度筛选
const filters = reactive({
  keyword: '',
  status: '',
  category: '',
  contractType: '',
  customerType: '',
  minAmount: null,
  maxAmount: null
})
const filteredData = computed(() => {
  return contracts.value.filter(i => (!filters.keyword || i.name.includes(filters.keyword)) && (!filters.status || i.status === filters.status))
})

// 新增：搜索函数，根据筛选条件向后端调用
// 支持完全灵活的筛选：不需要填写任何条件、可单独一项、也可以多项组合
const handleSearch = async () => {
  // 统计条件数量
  const filterCount = [filters.keyword, filters.category, filters.contractType, filters.customerType, filters.status].filter(Boolean).length +
                     ((filters.minAmount !== null && filters.minAmount !== undefined) ? 1 : 0) +
                     ((filters.maxAmount !== null && filters.maxAmount !== undefined) ? 1 : 0);

  if (filterCount === 0) {
    ElMessage.info('未选择任何筛选条件，即将为您显示全部数据');
  } else {
    console.log(`执行搜索，已选择 ${filterCount} 个筛选条件：`, filters);
  }

  currentPage.value = 1 // 恢复到第一页
  await fetchTableData();
}

const handleResetFilters = () => {
  console.log('重置筛选条件');
  filters.keyword = '';
  filters.status = '';
  filters.category = '';
  filters.contractType = '';
  filters.customerType = '';
  filters.minAmount = null;
  filters.maxAmount = null;
  currentPage.value = 1;
  fetchTableData(); // 重新加载同步处理
}

// 新增：拨打参数并向后端发起请求的带筛选条件的获取函数
const fetchTableDataWithFilters = async () => {
  loading.value = true
  const role = localStorage.getItem('userRole') || 'visitor'

  // 构建查询参数
  const params = new URLSearchParams();
  params.append('role', role);
  params.append('page', currentPage.value);
  params.append('size', pageSize.value);

  // 筛选条件
  if (filters.keyword) params.append('keyword', filters.keyword);
  if (filters.category) params.append('category', filters.category);
  if (filters.contractType) params.append('contractType', filters.contractType);
  if (filters.customerType) params.append('customerType', filters.customerType);
  if (filters.minAmount !== null && filters.minAmount !== undefined) params.append('minAmount', filters.minAmount);
  if (filters.maxAmount !== null && filters.maxAmount !== undefined) params.append('maxAmount', filters.maxAmount);
  if (filters.status) params.append('status', filters.status);

  try {
    const [pageRes, allRes] = await Promise.all([
      fetch(`http://localhost:9080/api/contracts?${params.toString()}`),
      fetch(`http://localhost:9080/api/contracts?role=${role}`) // 全量数据悠保不带筛选条件来更新图表
    ])

    if (pageRes.ok && allRes.ok) {
      const pageData = await pageRes.json()
      const allData = await allRes.json()

      if (pageData && typeof pageData === 'object' && 'list' in pageData) {
        contracts.value = pageData.list
        totalCount.value = pageData.total
      } else {
        contracts.value = pageData
        totalCount.value = pageData.length
      }

      if (allData && typeof allData === 'object' && 'list' in allData) {
        allContractsData.value = allData.list
      } else {
        allContractsData.value = allData
      }

      // 消成批量提示会话之提供了成功带流 专网阐排源须每一条数据湋是董手一次正优一龍
      ElMessage.success(`筛选成功，共找到 ${totalCount.value} 条合同`);
      console.log('按条件查找成功', {total: totalCount.value, currentCount: contracts.value.length})
    }
  } catch (error) {
    console.error('API 联动失败:', error)
  } finally {
    loading.value = false
  }
}

const getCatData = (cat, stats) => {
  const count = Number(stats[cat]) || 0
  return {
    count,
    percent: contractCount.value ? ((count / contractCount.value) * 100).toFixed(0) : 0
  }
}

// 图例网格自适应：类别 ≤10 时保持 2 列；超过后自动增加列数、缩小卡片，统计图区域不再撑大
const legendGridConfig = computed(() => {
  const count = categories.value.length
  let columns, sizeClass, gridClass

  if (count <= 10) {
    columns = 2
    sizeClass = ''
    gridClass = ''
  } else if (count <= 12) {
    columns = 3
    sizeClass = 'legend-compact'
    gridClass = 'legend-gap-sm'
  } else if (count <= 16) {
    columns = 4
    sizeClass = 'legend-dense'
    gridClass = 'legend-gap-xs'
  } else {
    columns = 5
    sizeClass = 'legend-mini'
    gridClass = 'legend-gap-xs'
  }

  return {
    gridStyle: { gridTemplateColumns: `repeat(${columns}, 1fr)` },
    cardClass: sizeClass,
    gridClass,
    scrollable: count > 16
  }
})

// 图表渲染逻辑
let chartInst = null

// 💡 接收 fetchTableData 传过来的轻量分类字典
const updateChart = (categoryStats = {}) => {
  const ctx = document.getElementById('categoryChart')
  if (!ctx) return

  const cats = categories.value
  const colors = categoryColorMap.value
  // 按类别列表提取统计数据
  const newData = cats.map(c => Number(categoryStats[c]) || 0)

  if (!chartInst) {
    chartInst = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: cats,
        datasets: [{
          data: newData,
          backgroundColor: cats.map(c => colors[c] || '#909399'),
          borderWidth: 0,
          cutout: '70%'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
      }
    })
  } else {
    // 如果标签列表变了（类别有增删），重建图表
    const oldLabels = chartInst.data.labels
    if (JSON.stringify(oldLabels) !== JSON.stringify(cats)) {
      chartInst.data.labels = cats
      chartInst.data.datasets[0].backgroundColor = cats.map(c => colors[c] || '#909399')
    }
    const oldData = chartInst.data.datasets[0].data
    if (JSON.stringify(oldData) === JSON.stringify(newData)) {
      return // 数据若一致，无视重绘动画
    }
    chartInst.data.datasets[0].data = newData
    chartInst.update()
  }
}

// 💡 核心修正：侦听器改为只死盯全量大盘数据 allContractsData
watch(allContractsData, (newVal) => {
  if (newVal && newVal.length > 0) {
    updateChart()
  }
}, { deep: true })

const initPageData = async () => {
  try {
    // 0. 校验 token 有效性（防止旧会话绕过登录）
    const isTokenValid = await verifyToken()
    if (!isTokenValid && localStorage.getItem('isGuest') !== 'true') {
      return  // verifyToken 已处理跳转
    }

    // 1. 获取系统参数配置
    const response = await fetch('http://localhost:9080/api/settings/')
    if (response.ok) {
      const configRes = await response.json()
      Object.assign(sysConfig, configRes)
      console.log("翻页系统配置加载完成")

      // 💡 启动会话超时监控
      startSessionTimeout(configRes.session_timeout_minutes || 0)

      // 2. 🔧 读取管理员设定的默认可见字段
      const serverDefaults = configRes.default_visible_fields || []
      const userPref = localStorage.getItem('visibleFields')
      const cachedDefaults = JSON.parse(localStorage.getItem('cachedDefaultFields') || '[]')
      const defaultsChanged = JSON.stringify([...serverDefaults].sort()) !== JSON.stringify([...cachedDefaults].sort())

      if (defaultsChanged && serverDefaults.length > 0) {
        visibleFields.value = [...serverDefaults]
        localStorage.setItem('visibleFields', JSON.stringify(serverDefaults))
        localStorage.setItem('cachedDefaultFields', JSON.stringify(serverDefaults))
        console.log('🔄 管理员已更新默认显示字段，已同步:', serverDefaults)
      } else if (userPref) {
        try {
          visibleFields.value = JSON.parse(userPref)
        } catch {
          if (serverDefaults.length > 0) {
            visibleFields.value = [...serverDefaults]
          }
        }
      } else if (serverDefaults.length > 0) {
        visibleFields.value = [...serverDefaults]
        localStorage.setItem('cachedDefaultFields', JSON.stringify(serverDefaults))
      }
    }

    // 3. 并发加载：字段定义 + 产品类别 + 签署公司 + 客户类别 + 合同类型
    const [fieldsRes, catRes, scRes, ctRes, coRes] = await Promise.all([
      fetch('http://localhost:9080/api/settings/fields'),
      fetch('http://localhost:9080/api/settings/categories'),
      fetch('http://localhost:9080/api/settings/signing-companies'),
      fetch('http://localhost:9080/api/settings/customer-types'),
      fetch('http://localhost:9080/api/settings/contract-types'),
    ])
    if (fieldsRes.ok) {
      const fData = await fieldsRes.json()
      if (fData.availableFields) {
        allFields.value = fData.availableFields
        console.log('✅ 合同字段已同步:', allFields.value.length, '个')
      }
    }
    if (catRes.ok) {
      const cData = await catRes.json()
      if (cData.categories) {
        categories.value = cData.categories
        categoryColorMap.value = cData.categoryColors || {}
        console.log('✅ 产品类别已同步:', categories.value.length, '个')
      }
    }
    if (scRes.ok) {
      const scData = await scRes.json()
      if (scData.signingCompanies) {
        signingCompanies.value = scData.signingCompanies
        console.log('✅ 签署公司已同步:', signingCompanies.value.length, '个')
      }
    }
    if (ctRes.ok) {
      const ctData = await ctRes.json()
      if (ctData.customerTypes) {
        customerTypes.value = ctData.customerTypes
        console.log('✅ 客户类别已同步:', customerTypes.value.length, '个')
      }
    }
    if (coRes.ok) {
      const coData = await coRes.json()
      if (coData.contractTypes) {
        contractTypes.value = coData.contractTypes
        console.log('✅ 合同类型已同步:', contractTypes.value.length, '个')
      }
    }

    // 4. 💡 关键：配置加载完后，立刻让真正的后端分页去捞第一页的合同数据！
    await fetchTableData()
    console.log("合同数据加载完成")

  } catch (err) {
    console.error("加载配置或首屏数据失败:", err)
  }
}
// 3. 挂载时执行一次（防止有时数据加载极快）
onMounted(() => {
  initPageData()

})

return {
  // EVERY variable, function, computed that the template references
  userRole, isGuest, realName, roleLabel, roleTagType,
  handleLogout, forceLogout,
  verifyToken,
  showChangePwdDialog, changePwdLoading, changePwdForm,
  isSuperAdmin,
  handleUserChangePassword,
  categories, customerTypes, signingCompanies, contractTypes, categoryColorMap,
  customFieldDefs,
  statusList, statusTagMap,
  contracts, allContractsData, categoryStatistics,
  totalAmount, archivedCount, activeCount, contractCount,
  loading, selectedFile, fileList,
  fetchTableData,
  modalVisible, form,
  handleOpenModal, handleFileBeforeUpload, handleFileChange, handleUploadRemove,
  isSubmitting,
  handleSizeChange, handleCurrentChange, handleSave, handleDelete,
  handleDownload,
  selectedRows, handleSelectionChange, handleBatchDownload,
  sysConfig, currentPage, pageSize, totalCount,
  displayedTableData,
  toggleField, statistics,
  visibleFields, allFields, activeColumns,
  filters, filteredData,
  handleSearch, handleResetFilters,
  fetchTableDataWithFilters,
  getCatData, legendGridConfig,
  updateChart,
  initPageData,
}

}
