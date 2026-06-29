import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import CryptoJS from 'crypto-js'

export function useRegister() {
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

  return {
    loading, formRef, form, rules,
    handleRegister,
  }
}
