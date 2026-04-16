import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  handleGoHome = () => {
    this.setState({ hasError: false, error: null })
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-surface-50 flex items-center justify-center p-6">
          <div className="max-w-md w-full text-center">
            <div className="text-6xl mb-6">⚠️</div>
            <h1 className="text-2xl font-bold text-surface-900 mb-3">
              页面出了点问题
            </h1>
            <p className="text-surface-400 mb-2">
              应用发生了意外错误，请尝试返回首页。
            </p>
            {this.state.error && (
              <pre className="mt-4 p-4 bg-surface-100 rounded-lg text-left text-sm text-red-500 overflow-auto max-h-40 border border-surface-200">
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={this.handleGoHome}
              className="mt-6 px-6 py-3 bg-primary-600 hover:bg-primary-500 text-white font-medium rounded-xl transition-all duration-200 shadow-sm shadow-primary-500/10"
            >
              返回首页
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
