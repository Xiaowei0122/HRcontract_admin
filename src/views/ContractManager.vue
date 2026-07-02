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
          :type="roleTagType"
          effect="light"
          round
          class="status-tag"
        >
          <el-icon><UserFilled /></el-icon>
          {{ roleLabel }}
        </el-tag>
      </div>
    </div>

    <div class="nav-actions">
      <el-button
        type="primary"
        :icon="Plus"
        @click="handleOpenModal()"
        :disabled="isGuest || userRole === 'viewer' || sysConfig.maintenance_mode"
      >
        录入新合同
      </el-button>
      <el-tag v-if="sysConfig.maintenance_mode" type="danger" size="small" style="margin-left: 8px;">维护模式</el-tag>
      
      <el-divider direction="vertical" />
      <el-button
        link
        :icon="Tickets"
        @click="$router.push('/system-settings')"
        :disabled="isGuest || userRole !== 'admin'"
      >
        系统设置
      </el-button>
      <el-button
        v-if="!isGuest && !isSuperAdmin"
        link
        :icon="Lock"
        @click="showChangePwdDialog = true"
        style="color: #409eff;"
      >
        修改密码
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

      <el-card v-if="sysConfig.show_dashboard_charts !== false" shadow="never" class="chart-section">
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
          <div class="chart-legend-grid" :style="legendGridConfig.gridStyle" :class="[legendGridConfig.gridClass, { 'legend-scroll': legendGridConfig.scrollable }]">
            <div v-for="c in categories" :key="c" class="legend-card" :class="legendGridConfig.cardClass">
              <div class="legend-info">
                <span class="legend-dot" :style="{ background: categoryColorMap[c] || '#909399' }"></span>
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
            <el-option v-for="ct in contractTypes" :key="ct" :label="ct" :value="ct" />
          </el-select>
          <el-select v-model="filters.customerType" placeholder="客户类别" clearable>
            <el-option v-for="ct in customerTypes" :key="ct" :label="ct" :value="ct" />
          </el-select>
          <el-select v-model="filters.status" placeholder="全部状态" clearable>
            <el-option v-for="s in statusList" :key="s" :label="s" :value="s" />
          </el-select>
          
          <!-- 金额区间筛选内联 -->
          <div class="amount-inline">
            <span class="amount-label">合同金额区间(元)：</span>
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
              <template v-else-if="col.key === 'amount'">
                <span :class="{ 'big-amount': sysConfig.big_amount_threshold > 0 && row.amount > sysConfig.big_amount_threshold * 10000 }">
                  ￥{{ row.amount?.toFixed(2) }}
                </span>
              </template>
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
                  :disabled="isGuest || userRole === 'viewer' || sysConfig.maintenance_mode"
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
                      :disabled="isGuest || userRole === 'viewer' || sysConfig.maintenance_mode || (userRole === 'user' && !sysConfig.allow_user_delete)"
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

    <footer class="app-footer">
      <p>© 2026 鸿瑞办公 · 数字化工程部 系统版本：v1.4.9-release</p>
    </footer>

    <el-dialog
      v-model="modalVisible" 
      :title="form._id ? '编辑合同' : '+ 新建合同'" 
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
                <el-option v-for="ct in contractTypes" :key="ct" :label="ct" :value="ct" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品类别">
              <el-select v-model="form.category" style="width: 100%">
                <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="客户类别">
              <el-select v-model="form.customerType" style="width: 100%">
                <el-option v-for="ct in customerTypes" :key="ct" :label="ct" :value="ct" />
              </el-select>
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
            <el-form-item label="合同金额(元)">
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

        <!-- 动态自定义字段 -->
        <template v-if="customFieldDefs.length > 0">
          <el-divider content-position="left">
            <span style="font-size: 13px; color: #909399;">自定义字段</span>
          </el-divider>
          <el-row :gutter="24">
            <el-col :span="12" v-for="cf in customFieldDefs" :key="cf.key">
              <el-form-item :label="cf.label">
                <el-input
                  v-if="cf.fieldType === 'text'"
                  v-model="form[cf.key]"
                  :placeholder="'请输入' + cf.label"
                />
                <el-input-number
                  v-else-if="cf.fieldType === 'number'"
                  v-model="form[cf.key]"
                  :precision="2"
                  :controls="false"
                  style="width: 100%"
                />
                <el-date-picker
                  v-else-if="cf.fieldType === 'date'"
                  v-model="form[cf.key]"
                  type="date"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
                <el-input
                  v-else
                  v-model="form[cf.key]"
                  :placeholder="'请输入' + cf.label"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </template>
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

    <!-- ═══════════════ 修改密码对话框（普通用户和子管理员） ═══════════════ -->
    <el-dialog v-model="showChangePwdDialog" title="修改登录密码" width="420px" :close-on-click-modal="false">
      <el-form :model="changePwdForm" label-position="top">
        <el-form-item label="原密码">
          <el-input v-model="changePwdForm.oldPassword" type="password" placeholder="请输入原密码" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="changePwdForm.newPassword" type="password" placeholder="请输入新密码（至少6位）" show-password />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="changePwdForm.confirmPassword" type="password" placeholder="请再次输入新密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangePwdDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUserChangePassword" :loading="changePwdLoading">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { Download, Document, ArrowLeft, Delete, EditPen, Briefcase, Plus, Search, PieChart, Setting, InfoFilled, SwitchButton, UserFilled, Tickets, Lock } from '@element-plus/icons-vue'
import { useContractManager } from '../router/contract/contractManager'

const {
  userRole, isGuest, realName, roleLabel, roleTagType,
  handleLogout,
  showChangePwdDialog, changePwdLoading, changePwdForm,
  isSuperAdmin,
  handleUserChangePassword,
  categories, customerTypes, signingCompanies, contractTypes, categoryColorMap,
  customFieldDefs,
  statusList, statusTagMap,
  categoryStatistics,
  totalAmount, archivedCount, activeCount, contractCount,
  loading, fileList,
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
  filters,
  handleSearch, handleResetFilters,
  getCatData, legendGridConfig,
} = useContractManager()
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
.chart-legend-grid { display: grid; gap: 15px; flex: 1; }
.legend-card { background: #fcfcfc; border: 1px solid #f0f0f0; padding: 12px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; }
.legend-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; flex-shrink: 0; }

/* 图例自适应：类别超过 10 个后自动缩小卡片、增加列数 */
.legend-compact { padding: 8px 10px; }
.legend-compact .legend-dot { width: 8px; height: 8px; }
.legend-compact .legend-name { font-size: 12px; }
.legend-compact .count { font-size: 12px; }
.legend-compact .percent { font-size: 11px; }

.legend-dense { padding: 5px 8px; }
.legend-dense .legend-dot { width: 7px; height: 7px; }
.legend-dense .legend-name { font-size: 11px; }
.legend-dense .count { font-size: 11px; }
.legend-dense .percent { font-size: 10px; }

.legend-mini { padding: 3px 6px; }
.legend-mini .legend-dot { width: 6px; height: 6px; }
.legend-mini .legend-name { font-size: 10px; }
.legend-mini .count { font-size: 10px; }
.legend-mini .percent { font-size: 9px; }

/* 图例间距收窄 */
.legend-gap-sm { gap: 10px; }
.legend-gap-xs { gap: 6px; }

/* 类别极多时限定高度并滚动，防止撑破布局 */
.legend-scroll { max-height: 340px; overflow-y: auto; }
.legend-scroll::-webkit-scrollbar { width: 5px; }
.legend-scroll::-webkit-scrollbar-thumb { background: #c0c4cc; border-radius: 4px; }
.legend-scroll::-webkit-scrollbar-track { background: transparent; }
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

/* 大额合同高亮 */
.big-amount {
  color: #f56c6c;
  font-weight: 700;
  background: #fef0f0;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #fde2e2;
}

/* 页脚版本信息 */
.app-footer {
  margin-top: 30px;
  padding: 16px 0;
  text-align: center;
  color: #909399;
  font-size: 13px;
}
</style>