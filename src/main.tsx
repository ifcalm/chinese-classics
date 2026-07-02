import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
// global.css 必须先于 App(app.css) 注入，否则 .page 会覆盖页面级同优先级样式
import './styles/global.css'
import App from './App.tsx'
import { ThemeProvider } from './theme/ThemeProvider.tsx'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>
)
