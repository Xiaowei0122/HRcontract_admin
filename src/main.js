import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // 1. 引入刚才定义的 router 逻辑
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

// 2. 注册所有图标（保持你原有的逻辑，这样全局都能直接用图标）
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 3. 挂载插件
app.use(router)        // 必须在 mount 之前 use
app.use(ElementPlus)

app.mount('#app')