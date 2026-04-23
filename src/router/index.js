import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import ContractManager from '../views/ContractManager.vue'
import SystemSettings from '../views/SystemSettings.vue'

const routes = [
  { 
    path: '/login',
    name: 'Login', 
    component: Login },
  { 
    path: '/', 
    name: 'ContractManager', 
    component: ContractManager,
    // 路由守卫：未登录跳回登录页
    beforeEnter: (to, from, next) => {
      const role = localStorage.getItem('userRole')
      if (!role) next('/login')
      else next()
    }
  },
  { 
    path: '/system-settings', 
    name: 'SystemSettings', 
    component: SystemSettings,
    // 路由守卫：仅管理员可访问
    beforeEnter: (to, from, next) => {
      const role = localStorage.getItem('userRole')
      if (role !== 'admin') next('/login')
      else next()
    }
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})