import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '192.168.1.170', // 允许局域网访问
    port: 5173,       // Vite 默认端口
  },
})