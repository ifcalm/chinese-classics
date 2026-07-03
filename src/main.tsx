import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
// global.css 必须先于 App(app.css) 注入，否则 .page 会覆盖页面级同优先级样式
import './styles/global.css'
import App from './App.tsx'
import { ThemeProvider } from './theme/ThemeProvider.tsx'

// 远程定位辅助：未捕获错误连同完整堆栈醒目输出(线上带 sourcemap，堆栈可读)
window.addEventListener('error', (e) => {
  console.error('[全局错误]', e.error?.stack ?? e.message)
})
window.addEventListener('unhandledrejection', (e) => {
  console.error('[未处理的 Promise 异常]', (e.reason as Error)?.stack ?? e.reason)
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>
)
