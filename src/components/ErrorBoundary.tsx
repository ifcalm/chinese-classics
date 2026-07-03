import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}
interface State {
  error: Error | null
}

/** 全局渲染错误兜底：任何组件抛错时显示可恢复的提示，而不是整页空白。 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // 保留完整堆栈，便于用户截图回报定位
    console.error('页面渲染出错:', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="page">
          <p className="empty">
            页面出了点问题（{this.state.error.message}）。
            <button className="reader__retry" onClick={() => this.setState({ error: null })}>
              重试
            </button>{' '}
            或{' '}
            <button className="reader__retry" onClick={() => location.reload()}>
              刷新页面
            </button>
            。
          </p>
        </div>
      )
    }
    return this.props.children
  }
}
