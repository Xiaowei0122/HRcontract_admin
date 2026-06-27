<template>
  <div class="login-container">
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
    </div>

    <el-card class="login-card" shadow="always">
      <div class="login-header">
        <el-icon class="login-logo"><UserFilled /></el-icon>
        <h2>用户注册</h2>
        <p>提交后需等待管理员审核通过方可登录</p>
      </div>

      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" class="login-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" placeholder="登录账号" :prefix-icon="User" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="真实姓名" prop="realName">
              <el-input v-model="form.realName" placeholder="您的姓名" :prefix-icon="EditPen" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="密码" prop="password">
              <el-input v-model="form.password" type="password" placeholder="至少6位" :prefix-icon="Lock" show-password />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="form.confirmPassword" type="password" placeholder="再次输入密码" :prefix-icon="Lock" show-password />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="邮箱">
              <el-input v-model="form.email" placeholder="选填" :prefix-icon="Message" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机号">
              <el-input v-model="form.phone" placeholder="选填" :prefix-icon="Phone" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="部门">
          <el-input v-model="form.department" placeholder="所属部门（选填）" :prefix-icon="OfficeBuilding" />
        </el-form-item>

        <el-button type="primary" class="submit-btn" @click="handleRegister" :loading="loading">
          提交注册
        </el-button>
      </el-form>

      <div style="text-align: center; margin-top: 16px;">
        <span style="color: #909399; font-size: 13px;">已有账号？</span>
        <el-link type="primary" :underline="false" @click="$router.push('/login')">
          立即登录
        </el-link>
      </div>
    </el-card>

    <footer class="login-footer">
      <p>© 2026 鸿瑞办公 · 数字化工程部 系统版本：v1.3.5-release</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { User, Lock, EditPen, Message, Phone, OfficeBuilding, UserFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import CryptoJS from 'crypto-js'

const router = useRouter()
const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  username: '',
  realName: '',
  password: '',
  confirmPassword: '',
  email: '',
  phone: '',
  department: ''
})

const validateConfirmPassword = (_rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次密码输入不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名至少3位', trigger: 'blur' }
  ],
  realName: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const hashedPassword = CryptoJS.SHA256(form.password).toString()

    const response = await fetch('http://localhost:9080/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: form.username,
        password: hashedPassword,
        realName: form.realName,
        email: form.email,
        phone: form.phone,
        department: form.department
      })
    })

    const res = await response.json()

    if (response.ok) {
      ElMessage.success(res.message || '注册成功，请等待管理员审核')
      router.push('/login')
    } else if (response.status === 409) {
      ElMessage.error('该用户名已被注册，请更换')
    } else {
      ElMessage.error(res.detail || '注册失败')
    }
  } catch (error) {
    console.error('注册请求失败:', error)
    ElMessage.error('无法连接到后端服务器，请检查网络')
  } finally {
    loading.value = false
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
  width: 560px;
  border-radius: 16px;
  padding: 20px 30px;
  z-index: 1;
  border: 1px solid rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
}

.login-header {
  text-align: center;
  margin-bottom: 24px;
}

.login-logo {
  font-size: 48px;
  color: #10b981;
  margin-bottom: 10px;
}

.login-header h2 {
  margin: 0;
  font-size: 22px;
  color: #1f2d3d;
}

.login-header p {
  color: #909399;
  font-size: 13px;
  margin-top: 6px;
}

.login-form {
  margin-top: 10px;
}

.submit-btn {
  width: 100%;
  height: 45px;
  font-size: 16px;
  font-weight: bold;
  border-radius: 8px;
  letter-spacing: 2px;
  margin-top: 8px;
}

.login-footer {
  margin-top: 40px;
  color: #909399;
  font-size: 13px;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  padding: 6px 10px;
}
:deep(.el-form-item) {
  margin-bottom: 14px;
}
</style>
