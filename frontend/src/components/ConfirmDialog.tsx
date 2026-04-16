interface ConfirmDialogProps {
  open: boolean
  message: string
  onConfirm: () => void
  onCancel: () => void
  confirmText?: string
}

export default function ConfirmDialog({ open, message, onConfirm, onCancel, confirmText = '确认删除' }: ConfirmDialogProps) {
  if (!open) return null
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onCancel} role="dialog" aria-modal="true" aria-label={message}>
      <div className="bg-white rounded-xl p-6 max-w-sm w-full shadow-xl" onClick={(e) => e.stopPropagation()}>
        <p className="text-surface-800 mb-4">{message}</p>
        <div className="flex justify-end gap-2">
          <button onClick={onCancel} className="px-4 py-2 text-sm text-surface-500 hover:bg-surface-50 rounded-lg">取消</button>
          <button onClick={onConfirm} className="px-4 py-2 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600">{confirmText}</button>
        </div>
      </div>
    </div>
  )
}
