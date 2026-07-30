import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// /api 转发到作业后端(python -m uvicorn backend.main:app --port 8787)。
// 后端未启动时前端自动降级:顶栏回退 WebGL 读 GPU 名,提交动作提示后端未连接。
const proxy = { '/api': { target: 'http://127.0.0.1:8787', changeOrigin: false } }

export default defineConfig({
  plugins: [vue()],
  base: './', // 相对路径:允许 file:// 直接打开 dist/index.html,也便于挂在任意子路径下
  // 监听所有接口:本机有 Clash TUN 时浏览器访问回环地址会被代理拦截,
  // 用局域网 IP(如 http://192.168.x.x:5173)可绕行;node 只听 [::1] 时 127.0.0.1 也会打不开
  server: { host: true, proxy },
  preview: { host: true, proxy },
  test: { environment: 'happy-dom' },
})
