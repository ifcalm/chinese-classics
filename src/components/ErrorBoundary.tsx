import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}
interface State {
  error: Error | null
  componentStack: string
}

/** 报错详情文本：sourcemap 已随包发布，堆栈可直接映射回源码，故原样呈现供回报。 */
function report(error: Error, componentStack: string): string {
  return [
    `信息: ${error.message}`,
    `地址: ${location.href}`,
    `UA: ${navigator.userAgent}`,
    `时间: ${new Date().toISOString()}`,
    '',
    error.stack ?? '(无 stack)',
    '',
    '组件栈:',
    componentStack || '(无)',
  ].join('\n')
}

/** 全局渲染错误兜底：任何组件抛错时显示可恢复的提示，而不是整页空白。 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null, componentStack: '' }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    const componentStack = info.componentStack ?? ''
    this.setState({ componentStack })
    console.error('页面渲染出错:', error, componentStack)
    const text = report(error, componentStack)
    // 留一份在全局，便于在控制台直接取用：copy(__ccLastError)
    ;(window as unknown as { __ccLastError?: string }).__ccLastError = text
    // 上报 Worker 落 Workers Logs，线上报错不再依赖用户回报。静默失败，绝不二次抛错。
    try {
      fetch('/api/err', { method: 'POST', body: text, keepalive: true }).catch(() => {})
    } catch {
      /* fetch 本身不可用(极老环境)也不影响兜底 UI */
    }
  }

  private copy = () => {
    const { error, componentStack } = this.state
    if (!error) return
    const text = report(error, componentStack)
    navigator.clipboard?.writeText(text).catch(() => {
      // 无剪贴板权限(非安全上下文等)时退回手选：详情区本就可见可选
    })
  }

  render() {
    const { error, componentStack } = this.state
    if (error) {
      return (
        <div className="page">
          <p className="empty">
            页面出了点问题（{error.message}）。
            <button
              className="reader__retry"
              onClick={() => this.setState({ error: null, componentStack: '' })}
            >
              重试
            </button>{' '}
            或{' '}
            <button className="reader__retry" onClick={() => location.reload()}>
              刷新页面
            </button>
            。
          </p>
          <details className="errbox">
            <summary className="errbox__sum">
              展开报错详情（回报此段即可定位）
              <button
                className="reader__retry"
                onClick={(e) => {
                  e.preventDefault()
                  this.copy()
                }}
              >
                复制
              </button>
            </summary>
            <pre className="errbox__pre">{report(error, componentStack)}</pre>
          </details>
        </div>
      )
    }
    return this.props.children
  }
}
