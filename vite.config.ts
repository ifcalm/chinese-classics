import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    // 兼容国产浏览器常见的旧 Chromium 内核(360/QQ/搜狗多为 86~94)：
    // 只降语法转译目标；运行时新 API(如 AbortSignal.timeout)在代码里已做特性检测
    target: ['chrome87', 'edge88', 'firefox78', 'safari14'],
    // 随包发布 sourcemap：线上报错堆栈直接映射回源码，便于远程定位
    sourcemap: true,
  },
})
