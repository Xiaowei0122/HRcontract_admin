<template>
  <div class="app-container">
    <header class="navbar">
    <div class="brand">
      <el-icon class="logo-icon"><Briefcase /></el-icon>
      <div class="brand-text">
        <span class="title">鸿瑞智链合同</span>
        <span class="subtitle">数字化管理系统</span>
      </div>
      
      <div class="role-badge">
        <el-tag 
          :type="isGuest ? 'warning' : 'success'" 
          effect="light" 
          round
          class="status-tag"
        >
          <el-icon><UserFilled /></el-icon>
          {{ isGuest ? '访客预览模式' : '系统管理员' }}
        </el-tag>
      </div>
    </div>

    <div class="nav-actions">
      <el-button 
        type="primary" 
        :icon="Plus"
        @click="handleOpenModal()"
        :disabled="isGuest"
      >
        录入新合同
      </el-button>
      
      <el-divider direction="vertical" />
      <el-button 
        link 
        :icon="Tickets" 
        @click="$router.push('/system-settings')"
        :disabled="isGuest"
      >
        系统设置
      </el-button>

      <el-button 
        class="logout-btn"
        link 
        :icon="SwitchButton" 
        @click="handleLogout"
      >
        退出系统
      </el-button>
    </div>
  </header>

    <main class="content">
      <el-row :gutter="20" class="stat-row">
        <el-col :span="6" v-for="s in statistics" :key="s.title">
          <el-card shadow="never" class="stat-card">
            <div class="stat-info">
              <p class="label">{{ s.title }}</p>
              <h2 class="value">{{ s.value }}<small>{{ s.unit }}</small></h2>
            </div>
            <div class="stat-icon" :style="{ color: s.color, background: s.color + '15' }">
              <el-icon><component :is="s.icon" /></el-icon>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="chart-section">
        <div class="section-header">
          <span class="panel-title"><el-icon><PieChart /></el-icon> 合同分类占比分析</span>
        </div>
        <div class="chart-layout">
          <div class="canvas-wrapper">
            <canvas id="categoryChart"></canvas>
            <div class="chart-inner-text">
              <p class="total-val">{{ contractCount }}</p>
              <p class="total-lab">总合同数</p>
            </div>
          </div>
          <div class="chart-legend-grid">
            <div v-for="c in categories" :key="c" class="legend-card">
              <div class="legend-info">
                <span class="legend-dot" :style="{ background: categoryColorMap[c] }"></span>
                <span class="legend-name">{{ c }}</span>
              </div>
              <div class="legend-data">
                <span class="count">{{ getCatData(c, categoryStatistics).count }} 份</span>
                <span class="percent">{{ getCatData(c, categoryStatistics).percent }}%</span>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="filter-section">
        <!-- 显示字段行 -->
        <div class="filter-row field-row">
          <span class="row-label"><el-icon><Setting /></el-icon> 显示字段：</span>
          <div class="field-tags-wrapper">
            <el-check-tag
              v-for="f in allFields" :key="f.key"
              :checked="visibleFields.includes(f.key)"
              @change="toggleField(f.key)"
              class="custom-tag"
            >
              {{ f.label }}
            </el-check-tag>
          </div>
        </div>
        
        <!-- 搜索和筛选行 -->
        <div class="filter-row search-row">
          <el-input v-model="filters.keyword" placeholder="搜索名称/编号/客户名称" clearable :prefix-icon="Search" class="search-input" />
          <el-select v-model="filters.category" placeholder="产品类别" clearable>
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
          <el-select v-model="filters.contractType" placeholder="合同类型" clearable>
            <el-option label="销售合同" value="销售合同" />
            <el-option label="采购合同" value="采购合同" />
            <el-option label="服务合同" value="服务合同" />
          </el-select>
          <el-select v-model="filters.customerType" placeholder="客户类别" clearable>
            <el-option v-for="ct in customerTypes" :key="ct" :label="ct" :value="ct" />
          </el-select>
          <el-select v-model="filters.status" placeholder="全部状态" clearable>
            <el-option v-for="s in statusList" :key="s" :label="s" :value="s" />
          </el-select>
          
          <!-- 金额区间筛选内联 -->
          <div class="amount-inline">
            <span class="amount-label">合同金额区间(万元)：</span>
            <el-input-number v-model="filters.minAmount" placeholder="最小值" :min="0" :precision="2" class="amount-input" clearable controls-position="right" />
            <span class="amount-separator">~</span>
            <el-input-number v-model="filters.maxAmount" placeholder="最大值" :min="0" :precision="2" class="amount-input" clearable controls-position="right" />
          </div>
          
          <el-button type="primary" @click="handleSearch" class="search-btn"><el-icon><Search /></el-icon> 搜索</el-button>
          <el-button @click="handleResetFilters" class="reset-btn"><el-icon><ArrowLeft /></el-icon> 重置</el-button>
          <el-button type="warning" :icon="Download" @click="handleBatchDownload" :disabled="isGuest || selectedRows.length === 0" style="margin-left: 12px;">
            批量下载 (已选 {{ selectedRows.length }} 份)
          </el-button>
        </div>
        </el-card>

      <el-card shadow="never" class="table-card">
        <el-table ref="tableRef"  :data="displayedTableData" stripe @selection-change="handleSelectionChange" v-loading="loading" element-loading-text="数据加载中..." style="width: 100%">
          <el-table-column type="selection" width="50" />
          <el-table-column v-for="col in activeColumns" :key="col.key" :prop="col.key" :label="col.label" show-overflow-tooltip>
            <template #default="{ row }">
              <template v-if="col.key === 'status'">
                <el-tag :type="statusTagMap[row.status]" size="small">{{ row.status }}</el-tag>
              </template>
              <template v-else-if="col.key === 'amount'">￥{{ row.amount?.toFixed(2) }}</template>
              <template v-else>{{ row[col.key] || '-' }}</template>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" align="center" fixed="right">
            <template #default="{ row }">
              <div class="action-btns">
                <el-button 
                  link 
                  type="primary" 
                  :icon="EditPen" 
                  @click="handleOpenModal(row)"
                  :disabled="isGuest"
                  class="action-btn"
                >
                  编辑
                </el-button>

                <el-button 
                  link 
                  type="success" 
                  :icon="Document"
                  @click="handleDownload(row)"
                  :disabled="!row.fileUrl"
                  class="action-btn"
                >
                  下载
                </el-button>
                
                <el-popconfirm
                  title="确定删除吗？"
                  @confirm="handleDelete(row)"
                  confirm-button-text="确定"
                  cancel-button-text="取消"
                >
                  <template #reference>
                    <el-button 
                      link 
                      type="danger" 
                      :icon="Delete"
                      :disabled="isGuest"
                      class="action-btn"
                    >
                      删除
                    </el-button>
                  </template>
                </el-popconfirm>
            </div>
            </template>
          </el-table-column>
        </el-table>
          <div class="pagination-footer" style="margin-top: 20px; display: flex; justify-content: flex-end;">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[5, 10, 20, 50]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="totalCount"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
      </el-card>
    </main>

    <el-dialog
      v-model="modalVisible" 
      :title="form.id ? '编辑合同' : '+ 新建合同'" 
      width="820px"
      append-to-body
      destroy-on-close
      class="contract-dialog"
    >
      <el-form :model="form" label-position="top" class="custom-edit-form">
        <el-col :span="24">
            <el-form-item label="上传电子合同">
          <el-upload
            class="drag-uploader"
            drag
            action="#"
            :auto-upload="false"
            :before-upload="handleFileBeforeUpload"
            :on-change="handleFileChange"
            :on-remove="handleUploadRemove"
            :file-list="fileList"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip blue-info">
                <el-icon><InfoFilled /></el-icon> 上传后将自动识别文件名为“合同名称”
              </div>
            </template>
          </el-upload>
        </el-form-item>
        </el-col>
        
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="合同名称 *" required>
              <el-input v-model="form.name" placeholder="请输入名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合同编号 *" required>
              <el-input v-model="form.contractId" disabled placeholder="系统自动生成" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="合同类型">
              <el-select v-model="form.contractType" style="width: 100%">
                <el-option label="销售合同" value="销售合同" />
                <el-option label="采购合同" value="采购合同" />
                <el-option label="服务合同" value="服务合同" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品类别">
              <div class="input-group">
                <el-select v-model="form.category" style="flex: 1">
                  <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
                </el-select>
                <el-button class="side-btn"><el-icon><Plus /></el-icon> 新增</el-button>
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="客户类别">
              <div class="input-group">
                <el-select v-model="form.customerType" style="flex: 1">
                  <el-option v-for="ct in customerTypes" :key="ct" :label="ct" :value="ct" />
                </el-select>
                <el-button class="side-btn"><el-icon><Plus /></el-icon> 新增</el-button>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户名称">
              <el-input v-model="form.customer" placeholder="请输入单位全称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="签署公司">
              <el-select v-model="form.signingCompany" style="width: 100%" clearable>
                <el-option v-for="sc in signingCompanies" :key="sc" :label="sc" :value="sc" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="联系人">
              <el-input v-model="form.contactPerson" placeholder="姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话">
              <el-input v-model="form.contactPhone" placeholder="手机/座机" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="服务期限">
              <el-input v-model="form.servicePeriod" placeholder="如：12个月" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="签订日期">
              <el-date-picker v-model="form.signDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="合同金额(万元)">
              <el-input-number v-model="form.amount" :precision="2" :controls="false" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option v-for="s in statusList" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" />
        </el-form-item>

        <div class="custom-field-action">
          <span class="section-title">自定义字段</span>
          <el-button link type="primary"><el-icon><Plus /></el-icon> 添加自定义字段</el-button>
        </div>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="modalVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSave" :loading="isSubmitting">
            {{ isSubmitting ? '正在提交...' : '保存提交' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { Download, Document, ArrowLeft, Delete ,EditPen ,Briefcase, Plus, Search, PieChart, Setting, UploadFilled, InfoFilled, Files, Money, Check, Timer, SwitchButton, UserFilled, Tickets } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Chart from 'chart.js/auto'
import axios from 'axios'
import { el } from 'element-plus/es/locale/index.mjs'
import { useRouter } from 'vue-router'

//登录退出逻辑
const router = useRouter()

// 获取当前登录状态
const userRole = ref(localStorage.getItem('userRole') || 'visitor')
const isGuest = ref(localStorage.getItem('isGuest') === 'true')

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

// --- 基础数据 (保持原有配置) ---
const categories = ["计算机设备", "办公用品", "电子产品", "福利产品", "劳保用品", "办公耗材" , "网络安防" ,"维修维护服务"]
const customerTypes = ["高校", "党政机关", "国企", "央企", "事业单位", "民营企业"]
const signingCompanies = ["鸿瑞办公", "政通慧采", "众冠供应链"] // 新增：签署公司列表
const categoryColorMap =  {"计算机设备": "#3b82f6","办公用品": "#10b981","电子产品": "#f59e0b", "福利产品": "#ef4444",  "劳保用品": "#f97316",  "办公耗材": "#8b5cf6",  "网络安防": "#06b6d4",  "维修维护服务": "#ec4899"}
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
  const role = localStorage.getItem('userRole') || 'visitor'
  
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
    }
  } catch (error) {
    console.error("筛选联动失败:", error)
  } finally {
    loading.value = false
  }
}

// 页面挂载时立即获取数据
onMounted(() => {
  fetchTableData()
})


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

  if (row) {
    Object.assign(form, { ...row })
    
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
    const uniqueId = `HT${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}${String(now.getMilliseconds()).padStart(3, '0')}`

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
  const fileName = file.name.substring(0, file.name.lastIndexOf('.'))
  form.name = fileName
  ElMessage.success(`自动识别：已填充合同名称为 "${fileName}"`)
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
    formData.append('operator', localStorage.getItem('userRole') || 'admin');

    if (fileList.value.length > 0) {
      formData.append('file', fileList.value[0].raw);
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
    const response = await fetch(`http://localhost:9080/api/contracts/${fallbackId}`, {
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
  // 🌟 核心改动：不再依赖可能错位的 fileUrl，直接用绝对唯一的 contractId 驱动下载
  if (!row.contractId) {
    ElMessage.error('该合同数据没有关联的唯一编号(contractId)');
    return;
  }

  try {
    ElMessage.info('正在从 NAS 获取合同文件...');

    // 🌟 核心防坑：动态获取当前浏览器的协议 (http/https) 和主机 IP/域名
    // 完美解决在群晖外网穿透（HTTPS）访问时，请求 http://localhost:9080 被浏览器拦截下载的问题
    const currentHost = window.location.hostname;
    const protocol = window.location.protocol;
    
    // 🌟 路径对齐：严格对应后端刚改好的新路由 /api/contracts/download-by-id/{contract_id}
    const downloadApiUrl = `${protocol}//${currentHost}:9080/api/contracts/download-by-id/${row.contractId}`;
    
    // 发起异步请求
    const response = await fetch(downloadApiUrl);
    
    if (response.status === 404) {
      ElMessage.error('后端数据库或文件系统中未找到对应的电子合同文件');
      return;
    }
    if (!response.ok) throw new Error('下载失败');

    // 将后端返回的文件流转换为二进制内存对象 (Blob)
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    
    // 优先用合同真实名称命名，没有就用编号兜底
    const fileKey = row.contractId || row.contractNo || row._id;
    a.download = row.name ? `${row.name}.pdf` : `合同_${fileKey}.pdf`;
    
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    ElMessage.success('合同文件下载成功');
  } catch (error) {
    console.error('前端下载逻辑捕获到异常:', error);
    ElMessage.error('文件下载失败，请检查后端服务或网络配置');
  }
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

    // 动态抓取当前协议（http/https）与当前访问的 IP 或公网域名
    const currentHost = window.location.hostname;
    const protocol = window.location.protocol;
    
    // 组装动态请求路径
    const batchDownloadUrl = `${protocol}//${currentHost}:9080/api/contracts/batch-download?${params.toString()}`;

    const response = await fetch(batchDownloadUrl);
    
    // 🌟 核心修复：面向用户的状态码提示，告别技术术语 🌟
    if (response.status === 404) {
      ElMessage.error('未找到对应的合同档案记录，请刷新页面重试');
      return;
    }
    if (response.status === 400) {
      // 按照你的要求：不提 NAS，统一话术为数据库，并且通俗易懂
      ElMessage.error('选中的合同在系统数据库中未找到对应的电子 PDF 文件');
      return;
    }
    if (!response.ok) throw new Error('打包失败');

    // 接收后端 StreamingResponse 返回的二进制 ZIP 文件流
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    
    // 规范 ZIP 压缩包命名
    const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    a.download = `合同批量下载_${dateStr}.zip`;
    
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    ElMessage.success(`成功下载 ${contractIds.length} 份合同档案`);
  } catch (error) {
    console.error('批量下载流捕获异常:', error);
    // 🌟 核心修复：用户看不懂群晖 Container，改成指导他们检查网络或联系管理员 🌟
    ElMessage.error('下载失败，请检查网络连接或联系系统管理员');
  }
};


// 翻页组件
// --- 1. 基础状态 ---
// --- 翻页组件所需的核心状态 ---
const sysConfig = reactive({ guest_data_limit: 2 }) 
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
}
const statistics = computed(() => [
  { title: '合同总量', value: contractCount.value, unit: '份', icon: Files, color: '#3b82f6' },
  { title: '累计总金额', value: totalAmount.value.toFixed(1), unit: '万', icon: Money, color: '#ef4444' },
  { title: '已签署', value: archivedCount.value, unit: '份', icon: Check, color: '#10b981' },
  { title: '待处理', value: activeCount.value, unit: '份', icon: Timer, color: '#f59e0b' }
])

const visibleFields = ref(['contractId', 'name', 'category', 'contractType', 'customer', 'customerType','signingCompany', 'amount', 'status', 'signDate'])
const allFields = [
  { key: 'name', label: '合同名称' },
  { key: 'contractId', label: '合同ID '},
  { key: 'contractType', label: '合同类型' },
  { key: 'category', label: '产品类别' },
  { key: 'customerType', label: '客户类别' },
  { key: 'customer', label: '客户名称' },
  { key: 'signingCompany', label: '签署公司' },  // 新增：签署公司显示字段
  { key: 'contactPerson', label: '联系人' },
  { key: 'contactPhone', label: '联系电话' },
  { key: 'servicePeriod', label: '服务期限' },
  { key: 'signDate', label: '签订日期' },
  { key: 'amount', label: '合同金额(万元)' },
  { key: 'status', label: '状态' },
  { key: 'remark', label: '备注' },
  { key: 'createTime', label: '创建时间' },
  { key: 'updateTime', label: '更新时间' },
  { key: 'contractNo', label: '合同编号' },
  { key: 'operator', label: '操作人'}
]
const activeColumns = computed(() => allFields.filter(f => visibleFields.value.includes(f.key)))
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

// 图表渲染逻辑
let chartInst = null

// 💡 接收 fetchTableData 传过来的轻量分类字典
const updateChart = (categoryStats = {}) => {
  const ctx = document.getElementById('categoryChart')
  if (!ctx) return

  // 💡 直接从后端返回的轻量字典里按 categories 数组定义的顺序提取纯数字，极其稳定安全
  const newData = categories.map(c => Number(categoryStats[c]) || 0)

  if (!chartInst) {
    chartInst = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: categories,
        datasets: [{ 
          data: newData, 
          backgroundColor: categories.map(c => categoryColorMap[c]), 
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
    // 1. 获取系统参数配置
    const response = await fetch('http://localhost:9080/api/settings/')
    if (response.ok) {
      const configRes = await response.json()
      Object.assign(sysConfig, configRes)
      console.log("翻页系统配置加载完成")
    }
    
    // 2. 💡 关键：配置加载完后，立刻让真正的后端分页去捞第一页的合同数据！
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
</script>

<style scoped>
/* 1. 基础布局与主页样式 */
.app-container { background: #f0f2f5; min-height: 100vh; }
.navbar {
  background: #fff;
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
}

.role-badge {
  margin-left: 20px;
  padding-left: 20px;
  border-left: 1px solid #ebeef5;
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  padding: 0 12px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logout-btn {
  color: #606266;
  font-size: 14px;
  transition: all 0.3s;
}

.logout-btn:hover {
  color: #f56c6c; /* 悬浮变红，提示危险操作 */
}

/* 操作列按钮布局 */
.action-btns {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px; /* 按钮之间的间距 */
}

/* 按钮基础样式优化 */
.action-btns :deep(.el-button) {
  padding: 4px 8px;
  height: auto;
  font-weight: 500;
  transition: all 0.2s ease; /* 平滑过渡动画 */
}

.action-btn {
  min-width: 50px;
}

/* 悬浮效果：轻轻上浮并加深颜色 */
.action-btns :deep(.el-button--primary:hover:not(.is-disabled)) {
  background-color: rgba(64, 158, 255, 0.1);
  transform: translateY(-1px);
}

.action-btns :deep(.el-button--success:hover:not(.is-disabled)) {
  background-color: rgba(16, 185, 129, 0.1);
  transform: translateY(-1px);
}

.action-btns :deep(.el-button--danger:hover:not(.is-disabled)) {
  background-color: rgba(245, 108, 108, 0.1);
  transform: translateY(-1px);
}

/* 禁用状态样式 */
.action-btns :deep(.el-button.is-disabled) {
  opacity: 0.5;
  cursor: not-allowed !important;
}

.action-btns :deep(.el-button.is-disabled:hover) {
  transform: none;
  background-color: transparent !important;
}

/*翻页组件容器样式*/
.pagination-footer {
  margin-top: 25px;
  padding: 10px 20px;
  background: #fff;
  display: flex;
  justify-content: space-between; /* 左右分布 */
  align-items: center;
  border-radius: 8px;
  border: 1px solid #ebeef5; /* 增加一点边框感 */
}

.footer-left {
  display: flex;
  align-items: center;
}

/* 针对移动端或小屏幕的适配 */
@media (max-width: 768px) {
  .pagination-footer {
    flex-direction: column;
    gap: 15px;
    align-items: flex-end;
  }
}

:deep(.el-divider--vertical) {
  margin: 0 15px;
  height: 20px;
}
.content { max-width: 1800px; margin: 0 auto; padding: 20px; }
.stat-row { margin-bottom: 20px; }
.stat-card { border: none; border-radius: 8px; }
.stat-info .label { color: #8c8c8c; font-size: 13px; margin: 0; }
.stat-info .value { font-size: 24px; font-weight: bold; margin: 4px 0 0 0; }
.stat-card :deep(.el-card__body) { display: flex; align-items: center; justify-content: space-between; }
.chart-section { margin-bottom: 20px; border-radius: 8px; }
.chart-layout { display: flex; align-items: center; gap: 60px; padding: 20px; }
.canvas-wrapper { width: 220px; height: 220px; position: relative; }
.chart-inner-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
.total-val { font-size: 32px; font-weight: bold; margin: 0; }
.chart-legend-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; flex: 1; }
.legend-card { background: #fcfcfc; border: 1px solid #f0f0f0; padding: 12px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; }
.filter-section { margin-bottom: 24px; border: 1px solid #ebeef5; border-radius: 10px; overflow: hidden; }
.filter-row { display: flex; align-items: center; padding: 14px 20px; border-bottom: 1px solid #f2f6fc; }
.filter-row:nth-child(2) { background-color: #fafbfc; }
.filter-row:last-child { border-bottom: none; background-color: #fff; }
.row-label { font-size: 13px; color: #909399; font-weight: bold; margin-right: 20px; flex-shrink: 0; }

/* 显示字段行 */
.field-row { flex-wrap: wrap; gap: 8px; }
.field-tags-wrapper { display: flex; flex-wrap: wrap; gap: 8px; flex: 1; }
.custom-tag { cursor: pointer; border-radius: 20px; border: 1px solid #dcdfe6; background: #fff; font-size: 12px; }
.custom-tag.is-checked { background: #409eff !important; color: #fff !important; }

/* 搜索和筛选行 */
.search-row { gap: 10px !important; align-items: center; }
.search-input { width: 200px; }
.search-row :deep(.el-select) { width: 120px; }
.search-btn { min-width: 90px; }
.reset-btn { min-width: 70px; }

/* 金额区间内联 */
.amount-inline { display: flex; gap: 8px; align-items: center; }
.amount-label { font-size: 12px; color: #909399; font-weight: bold; white-space: nowrap; }
.amount-input { width: 110px; }
.amount-separator { color: #909399; margin: 0 4px; }

/* 搜索按钮靠右 */
.search-btn { margin-left: auto !important; }

/* 2. 弹窗 UI 更新 (对齐图 2) */
:deep(.contract-dialog) { border-radius: 12px; }
:deep(.contract-dialog .el-dialog__header) { padding: 20px 24px; border-bottom: 1px solid #f0f0f0; margin-right: 0; }
:deep(.contract-dialog .el-dialog__title) { font-weight: bold; font-size: 18px; }

.custom-edit-form { padding: 0 10px; }
:deep(.el-form-item__label) { font-weight: bold; color: #303133; padding-bottom: 4px !important; }

.input-group { display: flex; gap: 8px; width: 100%; }
.side-btn { border: 1px solid #dcdfe6; background: #fff; color: #606266; }

.drag-uploader {
  width: 100%;
}

.drag-uploader :deep(.el-upload) {
  width: 100%;
}

.drag-uploader :deep(.el-upload-dragger) {
  width: 100%; 
  height: 160px; 
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

/* 提示文字样式调整 */
.blue-info {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #409eff;
  margin-top: 8px;
  font-size: 12px;
}
.custom-field-action { 
  display: flex; justify-content: space-between; align-items: center; 
  border-top: 1px dashed #dcdfe6; margin-top: 20px; padding-top: 15px; 
}
.section-title { font-size: 14px; font-weight: bold; color: #303133; }

.dialog-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 10px 0; }

/* 3. 其他交互样式 */
.mini-manager { display: flex; border: 1px solid #dcdfe6; border-radius: 4px; padding-right: 8px; height: 32px; background: #fff; }
.mini-manager :deep(.el-input__wrapper) { box-shadow: none !important; }
.mgr-btns { display: flex; align-items: center; border-left: 1px solid #eee; padding-left: 8px; margin-left: 4px; color: #c0c4cc; }
.amount-range { display: flex; align-items: center; border: 1px solid #dcdfe6; border-radius: 4px; padding: 0 10px; height: 32px; background: #fff; }
.batch-bar { display: flex; justify-content: space-between; background: #f0f7ff; padding: 10px 20px; border-top: 1px solid #e1f0ff; }
.selection-info span { color: #409eff; font-weight: bold; }
.dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin-right: 6px; }
</style>