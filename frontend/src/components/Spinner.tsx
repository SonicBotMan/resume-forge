export function Spinner({ className = 'w-4 h-4' }: { className?: string }) {
  return (
    <div
      className={`${className} border-2 border-primary-500 border-t-transparent rounded-full animate-spin-slow`}
      role="status"
      aria-label="加载中"
    />
  )
}
