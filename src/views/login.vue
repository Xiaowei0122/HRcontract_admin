<template>
  <div class="login-container">
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
    </div>

    <el-card class="login-card" shadow="always">
      <div class="login-header">
        <el-icon class="login-logo"><Briefcase /></el-icon>
        <h2>鸿瑞办公合同管理系统</h2>
        <p>数字化合同全生命周期管理</p>
      </div>

      <el-tabs v-model="activeTab" stretch>
        <el-tab-pane label="管理员登录" name="admin">
          <el-form :model="loginForm" :rules="rules" ref="loginRef" label-position="top" class="login-form">
            <el-form-item label="账号" prop="username">
              <el-input 
                v-model="loginForm.username" 
                placeholder="请输入管理员账号" 
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input 
                v-model="loginForm.password" 
                type="password" 
                placeholder="请输入密码" 
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            
            <div class="form-options">
              <el-checkbox v-model="rememberMe">记住我</el-checkbox>
              <el-link type="primary" :underline="false">忘记密码？</el-link>
            </div>

            <el-button type="primary" class="submit-btn" @click="handleLogin" :loading="loading">
              立即登录
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <el-divider>或者</el-divider>

      <div class="visitor-section">
        <el-button class="visitor-btn" @click="enterAsGuest" :icon="View">
          访客模式直接进入
        </el-button>
        <p class="visitor-tip">提示：访客模式仅支持数据查询与报表下载</p>
      </div>
    </el-card>

    <footer class="login-footer">
      <p>© 2026 鸿瑞办公 · 数字化工程部</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { User, Lock, Briefcase, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const activeTab = ref('admin')
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 管理员登录逻辑
const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    return ElMessage.warning('请输入账号和密码')
  }

  loading.value = true
  console.log("准备发起请求...")
  try {
    // 调用本地 FastAPI 后端
    const response = await fetch('http://localhost:9080/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: loginForm.username,
        password: loginForm.password
      })
    })

    const res = await response.json()
    // -- 处理后端响应，根据状态码判断登录结果 --
    if (response.ok) {
      // 登录成功：存储后端返回的角色和状态
      localStorage.setItem('userRole', res.userRole)
      localStorage.setItem('isGuest', String(res.isGuest))
      localStorage.setItem('token', res.token) // 存入 token 方便后续鉴权
      
      ElMessage.success(res.userRole === 'admin' ? '欢迎回来，管理员' : '登录成功')
      router.push('/')
    } else {
      // 登录失败：显示后端返回的错误信息
      ElMessage.error(res.detail || '账号或密码错误')
    }
  } catch (error) {
    console.error('API Error:', error)
    ElMessage.error('无法连接到后端服务器，请检查 API 是否启动')
  } finally {
    loading.value = false
  }
}
//账户退出逻辑
const handleLogout = async () => {
  try {
    // 1. 同步通知后端
    const response = await fetch('http://localhost:9080/api/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    
    const res = await response.json()
    console.log("%c[同步状态]", "color: #f56c6c; font-weight: bold;", res.message)

  } catch (error) {
    console.warn("后端退出接口调用失败，执行本地强制清理")
  } finally {
    // 2. 无论后端是否成功，必须清理本地状态
    localStorage.removeItem('userRole')
    localStorage.removeItem('isGuest')
    localStorage.removeItem('token')
    
    // 3. 提示并跳转
    ElMessage.success('已安全退出系统')
    router.push('/login')
  }
}
// 访客模式逻辑
const enterAsGuest = async () => {
  try {
    const response = await fetch('http://localhost:9080/api/guest')
    const res = await response.json()
    
    // 同步后端返回的状态
    localStorage.setItem('userRole', res.userRole)
    localStorage.setItem('isGuest', String(res.isGuest))
    
    console.log("%c[后端通知]", "color: #e6a23c;", res.message)
    ElMessage({
    message: res.message,
    type: 'warning'
  })
    router.push('/')
  } catch (error) {
    ElMessage.error('无法连接后端访客通道')
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  background-image: radial-gradient(#d2d9e1 1px, transparent 1px);
  background-size: 30px 30px;
  position: relative;
  overflow: hidden;
}

/* 背景装饰圆圈 */
.bg-decoration .circle {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  z-index: 0;
}
.circle-1 {
  width: 400px;
  height: 400px;
  background: rgba(64, 158, 255, 0.2);
  top: -100px;
  right: -100px;
}
.circle-2 {
  width: 300px;
  height: 300px;
  background: rgba(16, 185, 129, 0.1);
  bottom: -50px;
  left: -50px;
}

.login-card {
  width: 420px;
  border-radius: 16px;
  padding: 20px 10px;
  z-index: 1;
  border: 1px solid rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-logo {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 10px;
}

.login-header h2 {
  margin: 0;
  font-size: 24px;
  color: #1f2d3d;
}

.login-header p {
  color: #909399;
  font-size: 14px;
  margin-top: 8px;
}

.login-form {
  margin-top: 20px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.submit-btn {
  width: 100%;
  height: 45px;
  font-size: 16px;
  font-weight: bold;
  border-radius: 8px;
  letter-spacing: 2px;
}

.visitor-section {
  text-align: center;
  margin-top: 10px;
}

.visitor-btn {
  width: 100%;
  height: 40px;
  border-style: dashed;
  color: #606266;
}

.visitor-tip {
  font-size: 12px;
  color: #a8abb2;
  margin-top: 12px;
}

.login-footer {
  margin-top: 40px;
  color: #909399;
  font-size: 13px;
}

/* 覆盖 Element Plus 样式使 UI 更现代 */
:deep(.el-input__wrapper) {
  border-radius: 8px;
  padding: 8px 12px;
}
:deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: bold;
}
</style>