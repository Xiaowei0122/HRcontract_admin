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
              <p class="total-val">{{ allContractsData.length }}</p>
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
        <el-table ref="tableRef" :data="displayedTableData" v-loading="loading" stripe>
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
import { Document, ArrowLeft, Delete ,EditPen ,Briefcase, Plus, Search, PieChart, Setting, UploadFilled, InfoFilled, Files, Money, Check, Timer, SwitchButton, UserFilled, Tickets } from '@element-plus/icons-vue'
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
  }).then(() => {
    // 清除本地存储的状态
    localStorage.removeItem('userRole')
    localStorage.removeItem('isGuest')
    
    ElMessage.success('已安全退出')
    router.push('/login')
  }).catch(() => {})
}

// --- 基础数据 (保持原有配置) ---
const categories = ["计算机设备", "办公用品", "电子产品", "福利产品", "劳保用品", "办公耗材" , "网络安防" ,"维修维护服务"]
const customerTypes = ["高校", "党政机关", "国企", "央企", "事业单位", "民营企业"]
const categoryColorMap =  {"计算机设备": "#3b82f6","办公用品": "#10b981","电子产品": "#f59e0b", "福利产品": "#ef4444",  "劳保用品": "#f97316",  "办公耗材": "#8b5cf6",  "网络安防": "#06b6d4",  "维修维护服务": "#ec4899"}
const statusList = ["草稿", "待签署", "已签署", "已终止"]
const statusTagMap = { '已签署': 'success', '待签署': 'warning', '草稿': 'info', '已终止': 'danger' }


// --- 请求主要数据与状态 ---
const contracts = ref([])
const allContractsData = ref([]) // 💡 新增：专门用来喂给图表和顶部统计的全量数据
const loading = ref(false)
const selectedFile = ref(null)
const fileList = ref([])
// 获取合同数据的核心逻辑
const fetchTableData = async () => {
  loading.value = true
  const role = localStorage.getItem('userRole') || 'visitor'
  
  try {
    // 💡 使用 Promise.all 同时发出两个请求，速度最快
    const [pageRes, allRes] = await Promise.all([
      // 请求 1：带分页参数，拿当前页的切片数据
      fetch(`http://localhost:9080/api/contracts?role=${role}&page=${currentPage.value}&size=${pageSize.value}`),
      // 请求 2：不带分页参数，捞全盘不切片的数据（供大盘使用）
      fetch(`http://localhost:9080/api/contracts?role=${role}`)
    ])

    if (pageRes.ok && allRes.ok) {
      const pageData = await pageRes.json()
      const allData = await allRes.json()
      
      // 1. 给表格赋值（解析后端的打包结构）
      if (pageData && typeof pageData === 'object' && 'list' in pageData) {
        contracts.value = pageData.list     
        totalCount.value = pageData.total   // 撑开底部分页器
      } else {
        contracts.value = pageData
        totalCount.value = pageData.length
      }

      // 2. 给大盘全量变量赋值
      if (allData && typeof allData === 'object' && 'list' in allData) {
        allContractsData.value = allData.list
      } else {
        allContractsData.value = allData
      }
      console.log("--- 切片数据与大盘总数同步成功 ---")
    }
  } catch (error) {
    console.error("API 联动失败:", error)
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
  // 1. 唯一标识：改为 contractId (对应图 2)，初始给空字符串
  contractId: '', 
  name: '', 
  contractNo: '', 
  contractType: '销售合同', 
  category: '',
  customerType: '', 
  customer: '', 
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
    form.id = row._id || row.id || null
  } else {
    Object.assign(form, {
      id: null, name: '', contractNo: 'HT-' + Date.now().toString().slice(-4),
      contractType: '销售合同', category: '', customerType: '', customer: '',
      contactPerson: '', contactPhone: '', servicePeriod: '', signDate: '',
      amount: 0, status: '草稿', remark: '', createTime: '', updateTime: ''
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
    // 1. 开启加载状态
    loading.value = true;
    
    // 2. 创建 FormData 对象
    const formData = new FormData();
    //console.log("2. 准备构建数据", form);
    
    // 3. 按照后端接口定义的参数添加
    // 注意：只传业务输入字段，系统字段（ID、时间）交给后端生成
    formData.append('name', form.name);
    formData.append('contractNo', form.contractNo);
    formData.append('category', form.category || '');
    formData.append('amount', parseFloat(form.amount) || 0);
    formData.append('status', form.status || '草稿');
    formData.append('customer', form.customer || '');
    formData.append('customerType', form.customerType || '');
    formData.append('contractType', form.contractType || '');
    formData.append('contactPerson', form.contactPerson || '');
    formData.append('contactPhone', form.contactPhone || '');
    formData.append('signDate', form.signDate || '');
    formData.append('servicePeriod', form.servicePeriod || '');
    formData.append('remark', form.remark || '');
    
    // 操作人可以从本地存储获取
    formData.append('operator', localStorage.getItem('userRole') || 'admin');

    // 4. 添加文件 (这里的 key 'file' 必须与后端的 upload_contract 参数名一致)
    if (fileList.value.length > 0) {
      formData.append('file', fileList.value[0].raw);
    }
    console.log("3. 准备发送请求到后端...");

    const isEdit = !!form._id; 
    
    const url = isEdit 
      ? `http://localhost:9080/api/contracts/${form._id}` 
      : `http://localhost:9080/api/contracts/upload`;
    
    const method = isEdit ? 'put' : 'post';

    // 5. 发送请求
    const response = await axios[method](url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    if (response.data.status === 'success') {
      ElMessage.success('合同数据与附件已同步至数据库');
      modalVisible.value = false;
      // 重置文件列表和表单 (可选)
      fileList.value = [];
      fetchTableData(); // 刷新列表
    }
  } catch (error) {    
    // 提取 FastAPI 返回的具体错误信息
    const errorDetail = error.response?.data?.detail;
    let errorMsg = '字段校验错误';
    if (Array.isArray(errorDetail)) {
        errorMsg = `${errorDetail[0].loc[1]}: ${errorDetail[0].msg}`;
    }
    
    ElMessage.error('同步失败: ' + errorMsg);
  } finally {
    loading.value = false;
    isSubmitting.value = false
  }
};

// 删除合同
const handleDelete = async (row) => {
  const id = row._id || row.id; // 确保获取到数据库生成的唯一 ID
  if (!id) {
    ElMessage.error('无法获取合同ID，请刷新列表重试');
    return;
  }

  try {
    loading.value = true;
    // 调用后端删除接口
    const response = await fetch(`http://localhost:9080/api/contracts/${id}`, {
      method: 'DELETE'
    });

    if (response.ok) {
      ElMessage.success('合同已成功删除');
      fetchTableData(); // 重新加载列表，更新统计数据和图表
    } else {
      const errorData = await response.json();
      throw new Error(errorData.detail || '删除失败');
    }
  } catch (error) {
    console.error("删除出错:", error);
    ElMessage.error('删除失败：' + error.message);
  } finally {
    loading.value = false;
  }
}

// 下载附件
const handleDownload = async (row) => {
  if (!row.fileUrl || !row.fileName) {
    ElMessage.error('文件信息不完整，无法下载');
    return;
  }

  try {
    const response = await fetch(`http://localhost:9080${row.fileUrl}`);
    if (!response.ok) {
      throw new Error('下载失败');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = row.fileName;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    ElMessage.success('文件下载成功');
  } catch (error) {
    console.error("下载出错:", error);
    ElMessage.error('下载失败：' + error.message);
  }
}

// 翻页组件
// --- 1. 基础状态 ---
// --- 翻页组件所需的核心状态 ---
const sysConfig = reactive({ guest_data_limit: 2 }) 
const currentPage = ref(1)
const pageSize = ref(10)
const totalCount = ref(0) // 💡 变成响应式变量，由第二步的 fetchTableData 统一赋值

// --- 💡 修正后的表格渲染计算属性 ---
// 现在的 contracts.value 已经是后端切好片吐出来的 10 条了，不需要再用 .slice() 切片
// 我们只需要在这里保留你原本的模糊搜索逻辑，确保搜索框（名称/编号/状态）完美好使！
const displayedTableData = computed(() => {
  const data = contracts.value || []
  return data.filter(i => 
    (!filters.keyword || 
      (i.name && i.name.includes(filters.keyword)) || 
      (i.contractNo && i.contractNo.includes(filters.keyword)) || 
      (i.customer && i.customer.includes(filters.keyword))
    ) && 
    (!filters.status || i.status === filters.status)
  )
})

// --- 统计/筛选/显示逻辑 ---
const toggleField = (k) => { 
  const i = visibleFields.value.indexOf(k); 
  i > -1 ? visibleFields.value.splice(i, 1) : visibleFields.value.push(k); 
}
const statistics = computed(() => [
  { title: '合同总量', value: allContractsData.value.length, unit: '份', icon: Files, color: '#3b82f6' },
  { title: '累计总金额', value: allContractsData.value.reduce((s, c) => s + c.amount, 0).toFixed(1), unit: '万', icon: Money, color: '#ef4444' },
  { title: '已签署', value: allContractsData.value.filter(c => c.status === '已签署').length, unit: '份', icon: Check, color: '#10b981' },
  { title: '待处理', value: allContractsData.value.filter(c => c.status !== '已签署').length, unit: '份', icon: Timer, color: '#f59e0b' }
])

const visibleFields = ref(['contractId', 'name','contractType','customer','customerType', 'amount', 'status', 'signDate'])
const allFields = [
  { key: 'name', label: '合同名称' },
  { key: 'contractId', label: '合同ID '},
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
  { key: 'remark', label: '备注' },
  { key: 'createTime', label: '创建时间' },
  { key: 'updateTime', label: '更新时间' },
  { key: 'contractNo', label: '合同编号' },
  { key: 'operator', label: '操作人'}
]
const activeColumns = computed(() => allFields.filter(f => visibleFields.value.includes(f.key)))
const filters = reactive({ keyword: '', status: '' })
const filteredData = computed(() => {
  return contracts.value.filter(i => (!filters.keyword || i.name.includes(filters.keyword)) && (!filters.status || i.status === filters.status))
})

const getCatData = (cat) => {
  const data = allContractsData.value || [] 
  const count = data.filter(i => i.category === cat).length
  return { 
    count, 
    percent: data.length ? ((count / data.length) * 100).toFixed(0) : 0 
  }
}

// 图表渲染逻辑
let chartInst = null

const updateChart = () => {
  const ctx = document.getElementById('categoryChart')
  if (!ctx) return

  //基于全量数据进行统计，保证翻页时数据源稳定
  const newData = categories.map(c => 
    allContractsData.value.filter(i => i.category === c).length
  )

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
        animation: {
          duration: 400 // 缩短初次加载动画时间，体验更丝滑
        },
        plugins: { legend: { display: false } } 
      }
    })
  } else {
    // 💡 关键机制：先转为字符串比对新旧数据，若完全一致则直接拦截，绝不触发 Chart.js 的重绘动画！
    const oldData = chartInst.data.datasets[0].data
    if (JSON.stringify(oldData) === JSON.stringify(newData)) {
      return // 数据没变，直接抱拳告退，圆环纹丝不动
    }
    
    // 如果真的增删了合同，数据变了，才进行静默更新
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
    console.log("首屏第一页合同数据加载完成")

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