import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import CryptoJS from 'crypto-js'

export function useLogin() {
  const router = useRouter()
  const activeTab = ref('admin')
  const loading = ref(false)
  const rememberMe = ref(false)

  // 修改密码相关
  const showChangePwd = ref(false)
  const changePwdLoading = ref(false)
  const changePwdUsername = ref('')
  const changePwdOldHash = ref('')
  const changePwdForm = reactive({
    newPassword: '',
    confirmPassword: ''
  })

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
    //console.log("准备发起请求...")
    try {
      const encryptedPassword = CryptoJS.SHA256(loginForm.password).toString();
      // 调用本地 FastAPI 后端
      const response = await fetch('http://localhost:9080/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: loginForm.username,
          password: encryptedPassword
        })
      })

      const res = await response.json()
      // -- 处理后端响应，根据状态码判断登录结果 --
      if (response.ok) {
        // 登录成功：存储后端返回的角色和状态
        localStorage.setItem('userRole', res.userRole)
        localStorage.setItem('isGuest', String(res.isGuest))
        localStorage.setItem('token', res.token) // 存入 token 方便后续鉴权
        localStorage.setItem('username', loginForm.username) // 存入用户名用于退出
        localStorage.setItem('realName', res.realName || loginForm.username) // 存入真实姓名用于显示

        // 检测是否为默认密码，弹出修改提醒
        if (res.isDefaultPassword) {
          changePwdUsername.value = loginForm.username
          changePwdOldHash.value = encryptedPassword
          showChangePwd.value = true
          ElMessage.warning('您正在使用默认密码，请尽快修改！')
        } else {
          ElMessage.success(res.userRole === 'admin' ? '欢迎回来，管理员' : '登录成功')
          router.push('/')
        }
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

  // 提交修改密码
  const submitChangePwd = async () => {
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
      const newHash = CryptoJS.SHA256(changePwdForm.newPassword).toString()
      const response = await fetch('http://localhost:9080/api/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: changePwdUsername.value,
          oldPassword: changePwdOldHash.value,
          newPassword: newHash
        })
      })
      const res = await response.json()
      if (response.ok) {
        ElMessage.success('密码修改成功，欢迎使用系统')
        showChangePwd.value = false
        router.push('/')
      } else {
        ElMessage.error(res.detail || '密码修改失败')
      }
    } catch (error) {
      ElMessage.error('无法连接服务器')
    } finally {
      changePwdLoading.value = false
    }
  }

  // 跳过修改密码
  const skipChangePwd = () => {
    showChangePwd.value = false
    ElMessage.info('请尽快在系统设置中修改默认密码')
    router.push('/')
  }

  //账户退出逻辑
  const handleLogout = async () => {
    try {
      // 1. 同步通知后端
      const currentToken = localStorage.getItem('token');
      const currentUsername = localStorage.getItem('username');
      const response = await fetch('http://localhost:9080/api/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: currentToken, username: currentUsername })
      })

      const res = await response.json()
      //console.log("%c[同步状态]", "color: #f56c6c; font-weight: bold;", res.message)

    } catch (error) {
      console.warn("后端退出接口调用失败，执行本地强制清理")
    } finally {
      localStorage.removeItem('token')
      localStorage.removeItem('isGuest')
      localStorage.removeItem('userRole')
      localStorage.removeItem('username')
      localStorage.removeItem('admin_token')

      // 3. 提示并跳转
      ElMessage.success('已安全退出系统')
      router.push('/login')
    }
  }
  // 忘记密码提示
  const handleForgotPassword = () => {
    ElMessageBox.alert('如忘记登录密码，请联系系统管理员进行密码重置。', '忘记密码', {
      confirmButtonText: '知道了',
      type: 'info',
    })
  }

  // 访客模式逻辑
  const enterAsGuest = async () => {
    try {
      const response = await fetch('http://localhost:9080/api/guest')
      const res = await response.json()

      // 同步后端返回的状态
      localStorage.setItem('userRole', res.userRole)
      localStorage.setItem('isGuest', String(res.isGuest))

      //console.log("%c[后端通知]", "color: #e6a23c;", res.message)
      ElMessage({
      message: res.message,
      type: 'warning'
    })
      router.push('/')
    } catch (error) {
      ElMessage.error('无法连接后端访客通道')
    }
  }

  return {
    activeTab, loading, rememberMe,
    showChangePwd, changePwdLoading, changePwdUsername, changePwdOldHash, changePwdForm,
    loginForm, rules,
    handleLogin, submitChangePwd, skipChangePwd, handleLogout, enterAsGuest, handleForgotPassword,
  }
}
