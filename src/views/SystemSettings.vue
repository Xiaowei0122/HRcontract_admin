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
                    <span class="tip-text">设为 0 则访客完全不可见。如开启访客全部开放，则此设置无效。</span>
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

                <el-divider />

                <!-- ── 合同字段管理 ── -->
                <h3 class="section-title">合同字段管理</h3>
                <div class="field-mgmt-section">
                  <div class="field-mgmt-tip">
                    <el-icon><InfoFilled /></el-icon>
                    基础字段不可删除，自定义字段可编辑显示名称、类型或删除。新增字段将同步到合同表单和列表。
                  </div>
                    <el-table :data="fieldDefinitions" border stripe size="small" style="width: 100%; margin-top: 12px;" :max-height="320">
                      <el-table-column prop="key" label="字段标识" width="160" />
                      <el-table-column prop="label" label="显示名称" width="180">
                        <template #default="{ row }">
                          <span>{{ row.label }}</span>
                          <el-tag v-if="row.isCustom" type="warning" size="small" effect="plain" style="margin-left: 6px;">自定义</el-tag>
                        </template>
                      </el-table-column>
                      <el-table-column prop="fieldType" label="字段类型" width="100">
                        <template #default="{ row }">
                          <el-tag size="small" :type="row.fieldType === 'number' ? 'danger' : row.fieldType === 'date' ? 'success' : row.fieldType === 'select' ? 'warning' : 'info'">
                            {{ { text: '文本', number: '数字', date: '日期', select: '下拉' }[row.fieldType] || row.fieldType }}
                          </el-tag>
                        </template>
                      </el-table-column>
                      <el-table-column label="操作" width="160">
                        <template #default="{ row }">
                          <el-button link type="primary" size="small" @click="openEditFieldDialog(row)">
                            <el-icon><EditPen /></el-icon> 编辑
                          </el-button>
                          <el-button v-if="row.isCustom" link type="danger" size="small" @click="handleDeleteField(row)">
                            <el-icon><Delete /></el-icon> 删除
                          </el-button>
                          <span v-else style="color: #c0c4cc; font-size: 12px;">—</span>
                        </template>
                      </el-table-column>
                    </el-table>
                  <el-button type="primary" :icon="Plus" size="small" style="margin-top: 12px;" @click="openAddFieldDialog">
                    新增自定义字段
                  </el-button>
                </div>

                <el-divider />

                <!-- ── 产品类别管理 ── -->
                <h3 class="section-title">产品类别管理</h3>
                <div class="field-mgmt-section">
                  <div class="field-mgmt-tip">
                    <el-icon><InfoFilled /></el-icon>
                    管理合同的产品类别，将同步更新合同管理页饼图分类及右侧图例列表。
                  </div>
                  <div class="category-tags" style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">
                    <el-tag
                      v-for="(cat, idx) in categories"
                      :key="cat"
                      :color="categoryColors[cat] || '#909399'"
                      size="large"
                      closable
                      effect="dark"
                      style="cursor: pointer;"
                      @close="handleDeleteCategory(idx)"
                      @click="openEditCatDialog(idx)"
                    >
                      {{ cat }}
                    </el-tag>
                    <el-button type="primary" :icon="Plus" size="small" @click="openAddCatDialog" plain>
                      新增类别
                    </el-button>
                  </div>
                </div>

                <el-divider />

                <!-- ── 签署公司管理 ── -->
                <h3 class="section-title">签署公司管理</h3>
                <div class="field-mgmt-section">
                  <div class="field-mgmt-tip">
                    <el-icon><InfoFilled /></el-icon>
                    管理合同的签署公司选项，将同步更新合同管理页下拉列表。
                  </div>
                  <div class="category-tags" style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">
                    <el-tag
                      v-for="(company, idx) in signingCompanies"
                      :key="idx"
                      type="info"
                      size="large"
                      closable
                      effect="dark"
                      style="cursor: pointer;"
                      @close="handleDeleteSignCompany(idx)"
                      @click="openEditSignCompanyDialog(idx)"
                    >
                      {{ company }}
                    </el-tag>
                    <el-button type="primary" :icon="Plus" size="small" @click="openAddSignCompanyDialog" plain>
                      新增签署公司
                    </el-button>
                  </div>
                </div>

                <el-divider />

                <!-- ── 客户类别管理 ── -->
                <h3 class="section-title">客户类别管理</h3>
                <div class="field-mgmt-section">
                  <div class="field-mgmt-tip">
                    <el-icon><InfoFilled /></el-icon>
                    管理合同的客户类别选项，将同步更新合同管理页筛选下拉和表单下拉。
                  </div>
                  <div class="category-tags" style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">
                    <el-tag
                      v-for="(ct, idx) in customerTypes"
                      :key="ct"
                      type="primary"
                      size="large"
                      closable
                      effect="dark"
                      style="cursor: pointer;"
                      @close="handleDeleteCustomerType(idx)"
                      @click="openEditCustomerTypeDialog(idx)"
                    >
                      {{ ct }}
                    </el-tag>
                    <el-button type="primary" :icon="Plus" size="small" @click="openAddCustomerTypeDialog" plain>
                      新增客户类别
                    </el-button>
                  </div>
                </div>

                <el-divider />

                <!-- ── 默认显示字段 ── -->
                <h3 class="section-title">默认显示字段</h3>
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
                        <el-tag v-if="f.isCustom" type="warning" size="small" effect="plain" style="margin-left: 4px; font-size: 10px;">自定义</el-tag>
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
            <div style="margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between;">
              <el-radio-group v-model="userStatusFilter" @change="fetchUsers" size="small">
                <el-radio-button value="">全部</el-radio-button>
                <el-radio-button value="pending">待审核</el-radio-button>
                <el-radio-button label="active">已通过</el-radio-button>
                <el-radio-button label="rejected">已拒绝</el-radio-button>
                <el-radio-button label="disabled">已禁用</el-radio-button>
              </el-radio-group>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 13px; color: #606266;">允许普通用户删除合同：</span>
                <el-switch
                  v-model="configForm.allow_user_delete"
                  active-text="允许" inactive-text="禁止"
                  @change="saveConfig('allow_user_delete', configForm.allow_user_delete)"
                />
              </div>
            </div>
            <el-table :data="userList" border style="width: 100%" v-loading="userLoading">
              <el-table-column prop="username" label="用户名" width="140" />
              <el-table-column prop="realName" label="真实姓名" width="100" />
              <el-table-column prop="role" label="角色" width="80">
                <template #default="{ row }">
                  <el-tag :type="roleTagType(row.role)" effect="plain" size="small">
                    {{ roleLabel(row.role) }}
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
              <el-table-column prop="createTime" label="创建时间" width="160" />
              <el-table-column prop="isDisable" label="是否禁用" width="90">
                <template #default="{ row }">
                  <el-tag :type="row.isDisable ? 'danger' : 'success'" effect="plain" size="small">
                    {{ row.isDisable ? '是' : '否' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="currentToken" label="当前Token" width="180" show-overflow-tooltip>
                <template #default="{ row }">
                  <span v-if="row.currentToken" :title="row.currentToken" style="font-size: 12px; color: #909399;">
                    {{ row.currentToken.substring(0, 20) }}{{ row.currentToken.length > 20 ? '...' : '' }}
                  </span>
                  <span v-else style="color: #c0c4cc;">—</span>
                </template>
              </el-table-column>
              <el-table-column prop="lastLogin" label="最后登录" width="160" />
              <el-table-column label="操作" width="240" fixed="right">
                <template #default="{ row }">
                  <template v-if="row.status === 'pending'">
                    <el-button link type="success" size="small" @click="handleApprove(row.username, 'approve')">通过</el-button>
                    <el-button link type="danger" size="small" @click="handleApprove(row.username, 'reject')">拒绝</el-button>
                  </template>
                  <template v-else-if="row.username !== 'admin'">
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
              <!-- 日志筛选 -->
              <div class="log-filter-bar" v-if="logTotal > 0">
                <el-radio-group v-model="logFilter" size="small" @change="applyLogFilter">
                  <el-radio-button value="all">全部 ({{ logTotal }})</el-radio-button>
                  <el-radio-button value="contract">📄 合同</el-radio-button>
                  <el-radio-button value="user">👤 用户</el-radio-button>
                  <el-radio-button value="settings">⚙️ 设置</el-radio-button>
                  <el-radio-button value="system">🖥️ 系统</el-radio-button>
                </el-radio-group>
              </div>

              <el-timeline v-if="filteredLogs.length > 0">
                <el-timeline-item
                  v-for="(log, index) in filteredLogs"
                  :key="index"
                  :timestamp="log.time"
                  :type="log.type || 'info'"
                  :hollow="log.type === 'info'"
                  :color="getLogColor(log)"
                >
                  <div class="log-entry">
                    <el-tag
                      :type="getLogTagType(log)"
                      size="small"
                      effect="plain"
                      class="log-category-tag"
                    >
                      {{ getLogCategoryLabel(log) }}
                    </el-tag>
                    <span class="log-user">{{ log.user }}</span>
                    <span class="log-action">{{ log.action }}</span>
                  </div>
                </el-timeline-item>
              </el-timeline>

              <div class="log-pagination" v-if="logTotal > logPageSize">
                <el-pagination
                  v-model:current-page="logPage"
                  v-model:page-size="logPageSize"
                  :total="logTotal"
                  :page-sizes="[10, 20, 50]"
                  layout="total, sizes, prev, pager, next, jumper"
                  background
                  @current-change="handleLogPageChange"
                  @size-change="handleLogSizeChange"
                />
              </div>

              <el-empty v-if="filteredLogs.length === 0" description="暂无操作日志">
                <template v-if="logFilter !== 'all'">
                  <el-button type="primary" link @click="logFilter = 'all'">查看全部日志</el-button>
                </template>
              </el-empty>
            </div>
          </el-tab-pane>

        </el-tabs>
      </el-card>
    </div>

    <!-- ═══════════════ 角色设置对话框 ═══════════════ -->
    <el-dialog v-model="showRoleDialog" title="设置用户角色" width="460px" :close-on-click-modal="false">
      <div v-if="roleTargetUser" style="padding: 10px 0;">
        <p style="margin-bottom: 16px; color: #606266;">
          用户：<strong>{{ roleTargetUser.username }}</strong>（{{ roleTargetUser.realName }}）
          &nbsp;→&nbsp; 当前角色：<el-tag :type="roleTagType(roleTargetUser.role)" size="small">{{ roleLabel(roleTargetUser.role) }}</el-tag>
        </p>
        <p style="margin-bottom: 10px; font-weight: 600; color: #303133;">选择新角色：</p>
        <el-radio-group v-model="selectedRole" style="display: flex; flex-direction: column; gap: 12px;">
          <el-radio
            v-for="opt in roleOptions"
            :key="opt.value"
            :value="opt.value"
            :disabled="opt.value === roleTargetUser.role"
            border
            style="padding: 12px 16px; border-radius: 8px; width: 100%; margin: 0;"
          >
            <span style="font-weight: 600;">{{ opt.label.split(' — ')[0] }}</span>
            <span style="color: #909399; font-size: 12px; margin-left: 8px;">— {{ opt.label.split(' — ')[1] }}</span>
          </el-radio>
        </el-radio-group>
      </div>
      <template #footer>
        <el-button @click="showRoleDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmSetRole" :disabled="selectedRole === roleTargetUser?.role">确认更改</el-button>
      </template>
    </el-dialog>

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

    <!-- ═══════════════ 字段编辑对话框 ═══════════════ -->
    <el-dialog v-model="showFieldDialog" :title="fieldForm.isEdit ? '编辑字段' : '新增自定义字段'" width="450px" :close-on-click-modal="false">
      <el-form :model="fieldForm" label-position="top">
        <el-form-item label="字段标识" v-if="fieldForm.isEdit">
          <el-input :model-value="fieldForm.key" disabled />
          <span class="tip-text" style="font-size: 11px;">字段标识创建后不可修改</span>
        </el-form-item>
        <el-form-item label="字段标识" v-else>
          <el-input v-model="fieldForm.key" placeholder="必须以英文命名，如：supplierName" />
          <span class="tip-text" style="font-size: 11px;">必须以英文字母开头，只能包含英文、数字和下划线</span>
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="fieldForm.label" placeholder="如：供应商名称" />
        </el-form-item>
        <el-form-item label="字段类型">
          <el-select v-model="fieldForm.fieldType" style="width: 100%">
            <el-option v-for="opt in fieldTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFieldDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveField">{{ fieldForm.isEdit ? '保存修改' : '确认新增' }}</el-button>
      </template>
    </el-dialog>

    <!-- ═══════════════ 类别编辑对话框 ═══════════════ -->
    <el-dialog v-model="showCatDialog" :title="catForm.isEdit ? '编辑产品类别' : '新增产品类别'" width="440px" :close-on-click-modal="false">
      <el-form :model="catForm" label-position="top">
        <el-form-item label="类别名称">
          <el-input v-model="catForm.name" placeholder="如：医疗器械" />
        </el-form-item>
        <el-form-item label="类别颜色">
          <div style="display: flex; align-items: center; gap: 12px;">
            <input
              type="color"
              v-model="catForm.color"
              style="width: 40px; height: 36px; border: 1px solid #dcdfe6; border-radius: 6px; cursor: pointer; padding: 2px;"
            />
            <span style="font-size: 13px; color: #606266;">{{ catForm.color }}</span>
            <el-button size="small" text @click="catForm.color = autoPickColor()" style="font-size: 12px; color: #909399;">
              自动分配
            </el-button>
          </div>
          <div
            v-if="catForm.color"
            style="margin-top: 8px; height: 28px; border-radius: 6px; transition: background 0.2s;"
            :style="{ background: catForm.color }"
          ></div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCatDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveCategory">{{ catForm.isEdit ? '保存修改' : '确认新增' }}</el-button>
      </template>
    </el-dialog>

    <!-- ═══════════════ 签署公司编辑对话框 ═══════════════ -->
    <el-dialog v-model="showSignCompanyDialog" :title="signCompanyForm.isEdit ? '编辑签署公司' : '新增签署公司'" width="420px" :close-on-click-modal="false">
      <el-form :model="signCompanyForm" label-position="top">
        <el-form-item label="公司名称">
          <el-input v-model="signCompanyForm.name" placeholder="如：鸿瑞办公" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSignCompanyDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveSignCompany">{{ signCompanyForm.isEdit ? '保存修改' : '确认新增' }}</el-button>
      </template>
    </el-dialog>

    <!-- ═══════════════ 客户类别编辑对话框 ═══════════════ -->
    <el-dialog v-model="showCustTypeDialog" :title="custTypeForm.isEdit ? '编辑客户类别' : '新增客户类别'" width="420px" :close-on-click-modal="false">
      <el-form :model="custTypeForm" label-position="top">
        <el-form-item label="类别名称">
          <el-input v-model="custTypeForm.name" placeholder="如：外资企业" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCustTypeDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveCustomerType">{{ custTypeForm.isEdit ? '保存修改' : '确认新增' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { ArrowLeft, Lock, InfoFilled, EditPen, Delete, Plus } from '@element-plus/icons-vue'
import { useSystemSettings } from '../router/settings/systemSettings'

const {
  activeTab, showPasswordDialog, pwdLoading, pwdForm,
  availableFields, configForm,
  // 字段管理
  fieldDefinitions, baseFieldKeys, showFieldDialog, fieldForm, fieldTypeOptions,
  openAddFieldDialog, openEditFieldDialog, handleSaveField, handleDeleteField,
  // 产品类别管理
  categories, categoryColors, showCatDialog, catForm,
  openAddCatDialog, openEditCatDialog, handleSaveCategory, handleDeleteCategory, autoPickColor,
  // 签署公司管理
  signingCompanies, showSignCompanyDialog, signCompanyForm,
  openAddSignCompanyDialog, openEditSignCompanyDialog, handleSaveSignCompany, handleDeleteSignCompany,
  // 客户类别管理
  customerTypes, showCustTypeDialog, custTypeForm,
  openAddCustomerTypeDialog, openEditCustomerTypeDialog, handleSaveCustomerType, handleDeleteCustomerType,
  userList, userStatusFilter, userLoading,
  statusTagType, statusLabel,
  roleTagType, roleLabel, roleOptions,
  showRoleDialog, roleTargetUser, selectedRole,
  logs, logFilter, filteredLogs,
  logPage, logPageSize, logTotal,
  getLogColor, getLogTagType, getLogCategoryLabel,
  applyLogFilter, fetchLogs, handleLogPageChange, handleLogSizeChange,
  fetchInitialData, fetchUsers,
  saveConfig, saveDefaultFields,
  handleApprove, handleDeleteUser, handleToggleStatus,
  handleSetRole, confirmSetRole,
  handlePasswordUpdate,
} = useSystemSettings()

onMounted(() => {
  fetchInitialData()
  fetchUsers()
})
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

.log-filter-bar {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.log-entry {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.log-category-tag {
  flex-shrink: 0;
  font-size: 12px;
}

.log-user {
  font-weight: bold;
  color: #409eff;
}

.log-action {
  color: #606266;
  line-height: 1.6;
}

.log-pagination {
  display: flex;
  justify-content: center;
  padding: 20px 0 10px;
}

/* ── 字段 / 类别管理 ── */
.field-mgmt-section {
  margin-top: 4px;
}

.field-mgmt-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
  padding: 8px 12px;
  background: #f0f7ff;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.category-tags .el-tag {
  font-size: 14px;
  padding: 8px 16px;
  border-radius: 6px;
}

.category-tags .el-tag:hover {
  opacity: 0.85;
  transform: scale(1.03);
  transition: all 0.2s;
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
