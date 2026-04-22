<template>
  <div class="app-container">
    <header class="navbar">
    <div class="brand">
      <el-icon class="logo-icon"><Briefcase /></el-icon>
      <div class="brand-text">
        <span class="title">智链合同</span>
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
              <p class="total-val">{{ contracts.length }}</p>
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
                <span class="count">{{ getCatData(c).count }} 份</span>
                <span class="percent">{{ getCatData(c).percent }}%</span>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="filter-section">
        <div class="filter-row field-row">
          <span class="row-label"><el-icon><Setting /></el-icon> 显示字段：</span>
          <el-check-tag
            v-for="f in allFields" :key="f.key"
            :checked="visibleFields.includes(f.key)"
            @change="toggleField(f.key)"
            class="custom-tag"
          >
            {{ f.label }}
          </el-check-tag>
        </div>
        <div class="filter-row">
          <el-space wrap :size="12">
            <el-input v-model="filters.keyword" placeholder="搜索名称/编号/客户名称" style="width: 300px" clearable :prefix-icon="Search" />
            <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 140px">
              <el-option v-for="s in statusList" :key="s" :label="s" :value="s" />
            </el-select>
          </el-space>
        </div>
        </el-card>

      <el-card shadow="never" class="table-card">
        <el-table ref="tableRef" :data="filteredData" stripe>
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
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ row }">
              <el-button link type="primary" @click="handleOpenModal(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
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
            :on-change="handleAutoRecognize"
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
              <el-input v-model="form.contractNo" placeholder="请输入或系统生成" />
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
          <el-button type="primary" @click="handleSave">保存提交</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { Briefcase, Plus, Search, PieChart, Setting, UploadFilled, InfoFilled, Files, Money, Check, Timer, SwitchButton, UserFilled, Tickets } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Chart from 'chart.js/auto'
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
  }).then(() => {
    // 清除本地存储的状态
    localStorage.removeItem('userRole')
    localStorage.removeItem('isGuest')
    
    ElMessage.success('已安全退出')
    router.push('/login')
  }).catch(() => {})
}

// --- 基础数据 (保持原有配置) ---
const categories = ["计算机设备", "办公用品", "电子产品", "福利产品"]
const customerTypes = ["高校", "党政机关", "国企", "央企", "事业单位", "民营企业"]
const categoryColorMap = { "计算机设备": "#3b82f6", "办公用品": "#10b981", "电子产品": "#f59e0b", "福利产品": "#ef4444" }
const statusList = ["草稿", "待签署", "已签署", "已终止"]
const statusTagMap = { '已签署': 'success', '待签署': 'warning', '草稿': 'info', '已终止': 'danger' }

const contracts = ref([
  { id: 1, name: '2026年度实验室服务器群组采购', contractNo: 'HT-2026-JSJ-001', category: '计算机设备', amount: 128.50, status: '已签署', customer: '华南理工大学', customerType: '高校', contractType: '采购合同', contactPerson: '张教授', signDate: '2026-03-12' },
  { id: 2, name: '省政务中心办公耗材框架协议', contractNo: 'HT-2026-BG-042', category: '办公用品', amount: 12.80, status: '待签署', customer: '省政务服务中心', customerType: '党政机关', contractType: '框架合同', contactPerson: '李主任', signDate: '2026-04-05' },
  { id: 3, name: '智慧校园多媒体终端升级', contractNo: 'HT-2026-DZ-015', category: '电子产品', amount: 45.00, status: '已签署', customer: '市第一中学', customerType: '事业单位', contractType: '销售合同', contactPerson: '王老师', signDate: '2026-02-28' },
  { id: 4, name: '企业云端协作系统定制服务', contractNo: 'HT-2026-FW-009', category: '计算机设备', amount: 86.40, status: '草稿', customer: '中铁建某局分公司', customerType: '国企', contractType: '服务合同', contactPerson: '赵经理', signDate: '-' },
  { id: 5, name: '员工端午节福利礼品采购', contractNo: 'HT-2026-FL-003', category: '福利产品', amount: 5.20, status: '已终止', customer: '腾讯科技(深圳)', customerType: '民营企业', contractType: '采购合同', contactPerson: '陈女士', signDate: '2026-01-15' }
])


// --- 弹窗逻辑整合 ---
const modalVisible = ref(false)
const form = reactive({
  id: null, name: '', contractNo: '', contractType: '销售合同', category: '',
  customerType: '', customer: '', contactPerson: '', contactPhone: '',
  servicePeriod: '', signDate: '', amount: 0, status: '草稿', remark: ''
})

const handleOpenModal = (row = null) => {
  if (row) {
    Object.assign(form, { ...row })
  } else {
    Object.assign(form, {
      id: null, name: '', contractNo: 'HT-' + Date.now().toString().slice(-4),
      contractType: '销售合同', category: '', customerType: '', customer: '',
      contactPerson: '', contactPhone: '', servicePeriod: '', signDate: '',
      amount: 0, status: '草稿', remark: ''
    })
  }
  modalVisible.value = true
}

// 自动识别模拟
const handleAutoRecognize = (file) => {
  const fileName = file.name.substring(0, file.name.lastIndexOf('.'))
  form.name = fileName
  ElMessage.success(`自动识别：已填充合同名称为 "${fileName}"`)
}

const handleSave = () => {
  if (!form.name) return ElMessage.warning('合同名称不能为空')
  if (form.id) {
    const index = contracts.value.findIndex(c => c.id === form.id)
    contracts.value[index] = { ...form }
  } else {
    contracts.value.unshift({ ...form, id: Date.now() })
  }
  modalVisible.value = false
  ElMessage.success('保存成功')
}

// --- 统计/筛选/显示逻辑 (保持不变) ---
const statistics = computed(() => [
  { title: '合同总量', value: contracts.value.length, unit: '份', icon: Files, color: '#3b82f6' },
  { title: '累计总金额', value: contracts.value.reduce((s, c) => s + c.amount, 0).toFixed(1), unit: '万', icon: Money, color: '#ef4444' },
  { title: '已签署', value: contracts.value.filter(c => c.status === '已签署').length, unit: '份', icon: Check, color: '#10b981' },
  { title: '待处理', value: contracts.value.filter(c => c.status !== '已签署').length, unit: '份', icon: Timer, color: '#f59e0b' }
])

const visibleFields = ref(['contractNo', 'name', 'customer', 'amount', 'status', 'signDate'])
const allFields = [
  { key: 'name', label: '合同名称' },
  { key: 'contractNo', label: '合同编号' },
  { key: 'contractType', label: '合同类型' },
  { key: 'category', label: '产品类别' },
  { key: 'customerType', label: '客户类别' },
  { key: 'customer', label: '客户名称' },
  { key: 'contactPerson', label: '联系人' },
  { key: 'contactPhone', label: '联系电话' },
  { key: 'servicePeriod', label: '服务期限' },
  { key: 'signDate', label: '签订日期' },
  { key: 'amount', label: '合同金额(万元)' },
  { key: 'status', label: '状态' },
  { key: 'remark', label: '备注' }
]
const activeColumns = computed(() => allFields.filter(f => visibleFields.value.includes(f.key)))
const filters = reactive({ keyword: '', status: '' })
const filteredData = computed(() => {
  return contracts.value.filter(i => (!filters.keyword || i.name.includes(filters.keyword)) && (!filters.status || i.status === filters.status))
})

// 图表渲染逻辑...
let chartInst = null
const updateChart = () => {
  const ctx = document.getElementById('categoryChart')
  if (!ctx || chartInst) return
  chartInst = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: categories,
      datasets: [{ data: categories.map(c => contracts.value.filter(i => i.category === c).length), backgroundColor: categories.map(c => categoryColorMap[c]), borderWidth: 0, cutout: '70%' }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
  })
}
const getCatData = (cat) => {
  const count = contracts.value.filter(i => i.category === cat).length
  return { count, percent: contracts.value.length ? ((count / contracts.value.length) * 100).toFixed(0) : 0 }
}
const toggleField = (k) => { const i = visibleFields.value.indexOf(k); i > -1 ? visibleFields.value.splice(i, 1) : visibleFields.value.push(k) }

onMounted(() => updateChart())
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

:deep(.el-divider--vertical) {
  margin: 0 15px;
  height: 20px;
}
.content { max-width: 1400px; margin: 0 auto; padding: 20px; }
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
.row-label { font-size: 13px; color: #909399; font-weight: bold; margin-right: 10px; flex-shrink: 0; }
.custom-tag { cursor: pointer; border-radius: 20px; margin-right: 8px; border: 1px solid #dcdfe6; background: #fff; }
.custom-tag.is-checked { background: #409eff !important; color: #fff !important; }

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
  width: 100%; /* 强制拖拽区域撑满父容器 */
  height: 160px; /* 如果觉得太高可以适当调小，默认是 180px */
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