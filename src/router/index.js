import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/login.vue'
import Register from '../views/Register.vue'
import ContractManager from '../views/ContractManager.vue'
import SystemSettings from '../views/SystemSettings.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login },
  {
    path: '/register',
    name: 'Register',
    component: Register },
  {
    path: '/',
    name: 'ContractManager',
    component: ContractManager,
    // 路由守卫：未登录或凭证缺失则跳回登录页
    beforeEnter: (to, from, next) => {
      const role = localStorage.getItem('userRole')
      const isGuest = localStorage.getItem('isGuest') === 'true'
      const token = localStorage.getItem('token')
      // 非访客必须有 token，否则会话已失效
      if (!role || (!isGuest && !token)) {
        // 清理残留数据后跳转登录
        localStorage.removeItem('userRole')
        localStorage.removeItem('isGuest')
        localStorage.removeItem('token')
        localStorage.removeItem('username')
        localStorage.removeItem('admin_token')
        next('/login')
      } else {
        next()
      }
    }
  },
  {
    path: '/system-settings',
    name: 'SystemSettings',
    component: SystemSettings,
    // 路由守卫：仅管理员可访问，且须有有效 token
    beforeEnter: (to, from, next) => {
      const role = localStorage.getItem('userRole')
      const token = localStorage.getItem('token')
      if (role !== 'admin' || !token) next('/')
      else next()
    }
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
