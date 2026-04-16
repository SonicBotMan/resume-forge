import { Spinner } from './Spinner'

export function PageLoader({ text = '加载中...' }: { text?: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-50">
      <div className="flex items-center gap-3">
        <Spinner className="w-6 h-6" />
        <span className="text-surface-500">{text}</span>
      </div>
    </div>
  )
}

export function PageError({
  title,
  activeNav,
  message = '加载失败，请检查网络连接后重试',
  onRetry,
}: {
  title: string
  activeNav: string
  message?: string
  onRetry: () => void
}) {
  return (
    <div className="min-h-screen bg-surface-50">
      {title && activeNav && (
        <div className="py-4 px-6 border-b border-surface-200 bg-white">
          <span className="text-lg font-semibold text-surface-900">{title}</span>
        </div>
      )}
      <div className="max-w-5xl mx-auto p-4 sm:p-6 text-center py-20">
        <div className="text-6xl mb-4">⚠️</div>
        <h2 className="text-lg font-semibold text-surface-900 mb-2">加载失败</h2>
        <p className="text-surface-400 mb-6">{message}</p>
        <button
          onClick={onRetry}
          className="px-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-500 transition-all shadow-sm shadow-primary-500/10"
        >
          重试
        </button>
      </div>
    </div>
  )
}
