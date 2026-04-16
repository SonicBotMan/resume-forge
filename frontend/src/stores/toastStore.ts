import { create } from 'zustand'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: string
  type: ToastType
  message: string
  duration?: number
}

interface ToastStore {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (toast) => {
    const id = crypto.randomUUID()
    const duration = toast.duration ?? 5000
    set((state) => ({ toasts: [...state.toasts, { ...toast, id, duration }] }))
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }))
    }, duration)
  },
  removeToast: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}))

export function toastSuccess(message: string) {
  useToastStore.getState().addToast({ type: 'success', message })
}

export function toastError(message: string) {
  useToastStore.getState().addToast({ type: 'error', message, duration: 7000 })
}

export function toastWarning(message: string) {
  useToastStore.getState().addToast({ type: 'warning', message })
}

export function toastInfo(message: string) {
  useToastStore.getState().addToast({ type: 'info', message })
}
