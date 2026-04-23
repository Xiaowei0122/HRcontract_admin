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
          <el-tab-pane label="参数配置" name="config">
            <div class="config-section">
              <h3 class="section-title">权限与预览控制</h3>
              <el-form label-width="160px" label-position="left">
                <el-form-item label="访客可见合同条数">
                  <div class="input-with-tip">
                    <el-input-number 
                      v-model="configForm.guest_data_limit" 
                      :min="0" 
                      :max="100" 
                      @change="saveConfig('guest_data_limit', configForm.guest_data_limit)"
                    />
                    <span class="tip-text">当前设为 {{ configForm.guest_data_limit }} 条，设为 0 则完全不可见。</span>
                  </div>
                </el-form-item>

                <el-form-item label="系统维护模式">
                  <el-switch 
                    v-model="configForm.maintenance_mode" 
                    active-text="开启"
                    inactive-text="关闭"
                    @change="saveConfig('maintenance_mode', configForm.maintenance_mode)" 
                  />
                </el-form-item>

                <el-divider />
                
                <h3 class="section-title">业务预警与显示</h3>
                <el-form-item label="大额合同阈值 (万)">
                  <div class="input-with-tip">
                    <el-input-number 
                      v-model="configForm.big_amount_threshold" 
                      :min="0" 
                      :step="10"
                      @change="saveConfig('big_amount_threshold', configForm.big_amount_threshold)"
                    />
                    <span class="tip-text">金额超过此标准的合同将在列表中高亮显示。</span>
                  </div>
                </el-form-item>

                <el-form-item label="显示统计图表">
                  <el-switch 
                    v-model="configForm.show_dashboard_charts" 
                    @change="saveConfig('show_dashboard_charts', configForm.show_dashboard_charts)"
                  />
                  <span class="tip-text" style="margin-left: 10px">控制合同管理页顶部饼图的可见性。</span>
                </el-form-item>

                <el-divider />

                <h3 class="section-title">安全与系统审计</h3>
                <el-form-item label="日志保留天数">
                  <el-select 
                    v-model="configForm.log_retention_days" 
                    style="width: 120px"
                    @change="saveConfig('log_retention_days', configForm.log_retention_days)"
                  >
                    <el-option label="7天" :value="7" />
                    <el-option label="30天" :value="30" />
                    <el-option label="永久" :value="0" />
                  </el-select>
                </el-form-item>

                <el-form-item label="管理员密码修改">
                  <el-button type="primary" icon="Lock" @click="showPasswordDialog = true">修改密码</el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-tab-pane>

          <el-tab-pane label="用户管理" name="users">
             <el-table :data="userList" border style="width: 100%; margin-top: 15px">
               <el-table-column prop="username" label="用户名" width="180" />
               <el-table-column prop="role" label="角色">
                 <template #default="scope">
                   <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'success'" effect="plain">
                     {{ scope.row.role.toUpperCase() }}
                   </el-tag>
                 </template>
               </el-table-column>
               <el-table-column prop="lastLogin" label="最后登录" />
               <el-table-column label="操作" width="200">
                 <template #default="scope">
                   <el-button link type="primary" v-if="scope.row.role !== 'admin'">权限设置</el-button>
                   <el-button link type="danger" v-if="scope.row.role !== 'admin'">禁用账号</el-button>
                 </template>
               </el-table-column>
             </el-table>
          </el-tab-pane>

          <el-tab-pane label="操作日志" name="logs">
            <div class="log-container">
              <el-timeline>
                <el-timeline-item
                  v-for="(log, index) in logs"
                  :key="index"
                  :timestamp="log.time"
                  :type="log.type"
                  hollow
                >
                  <span class="log-user">{{ log.user }}</span> 
                  <span class="log-action">{{ log.action }}</span>
                </el-timeline-item>
              </el-timeline>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted, ref } from 'vue' 
import { ArrowLeft, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const activeTab = ref('config')
const showPasswordDialog = ref(false)
const newPassword = ref('')

// 1. 初始化配置表单：必须补全 template 中引用的所有字段
const configForm = reactive({
  guest_data_limit: 0,
  maintenance_mode: false,
  // --- 以下是新增的“面向用户”配置字段 ---
  big_amount_threshold: 100,      // 大额合同阈值 (万)
  show_dashboard_charts: true,    // 是否显示首页统计图表
  log_retention_days: 30          // 日志保留天数
})

// 2. 定义用户列表 (保持不变)
const userList = ref([
  { username: 'admin', role: 'admin', lastLogin: '2026-04-23 18:00:00' },
  { username: 'guest_user', role: 'guest', lastLogin: '2026-04-22 10:00:00' }
])

// 3. 定义日志列表 (保持不变)
const logs = ref([])

// 4. 获取初始化数据：从后端加载最新的系统运行参数
const fetchInitialData = async () => {
  try {
    const configRes = await fetch('http://localhost:9080/api/settings/')
    if (configRes.ok) {
      const data = await configRes.json()
      // 使用 Object.assign 批量更新，确保响应式
      Object.assign(configForm, data)
    }

    const logRes = await fetch('http://localhost:9080/api/settings/logs')
    if (logRes.ok) {
      logs.value = await logRes.json()
    }
  } catch (err) {
    console.error("系统设置初始化失败:", err)
  }
}

onMounted(() => {
  fetchInitialData()
})

// 5. 保存配置到后端：支持动态更新任意配置项
const saveConfig = async (key, value) => {
  try {
    const response = await fetch('http://localhost:9080/api/settings/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, value })
    })
    
    if (response.ok) {
      ElMessage({
        message: `系统配置已实时生效`,
        type: 'success',
        plain: true
      })
      // 更新成功后刷新日志，用户能立刻看到自己的修改记录
      const logRes = await fetch('http://localhost:9080/api/settings/logs')
      if (logRes.ok) logs.value = await logRes.json()
    }
  } catch (err) {
    ElMessage.error('无法同步至服务器，请检查后端网络')
  }
}

// 密码修改逻辑 (后续可对接后端)
const handlePasswordUpdate = () => {
  if (!newPassword.value) return ElMessage.warning('请输入新密码')
  ElMessage.success('管理员密码修改成功')
  showPasswordDialog.value = false
  newPassword.value = ''
}
</script>

<style scoped>
/* 整体背景美化 */
.system-wrapper {
  background-color: #f5f7fa;
  min-height: 100vh;
}

/* 顶部栏：增加阴影和固定感 */
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

/* 内容区 */
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

/* 日志样式 */
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

/* 覆盖 Element Tabs 默认样式 */
:deep(.el-tabs__item) {
  font-size: 15px;
  height: 50px;
}
</style>