import { useToastStore } from '../../stores/toastStore'

const iconMap = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ',
}

const colorMap = {
  success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  warning: 'bg-amber-50 border-amber-200 text-amber-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
}

const iconBgMap = {
  success: 'bg-emerald-500',
  error: 'bg-red-500',
  warning: 'bg-amber-500',
  info: 'bg-blue-500',
}

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 left-4 right-4 sm:left-auto sm:right-4 sm:w-96 z-50 flex flex-col gap-2" role="status" aria-live="polite">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-start gap-3 px-4 py-3 rounded-xl border shadow-lg animate-slide-in ${colorMap[toast.type]}`}
          role="alert"
        >
          <span
            className={`w-5 h-5 rounded-full flex items-center justify-center text-white text-xs flex-shrink-0 mt-0.5 ${iconBgMap[toast.type]}`}
          >
            {iconMap[toast.type]}
          </span>
          <p className="flex-1 text-sm">{toast.message}</p>
          <button
            onClick={() => removeToast(toast.id)}
            className="text-current opacity-50 hover:opacity-100 flex-shrink-0 transition-opacity"
            aria-label="关闭"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  )
}
