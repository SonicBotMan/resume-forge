export function formatDate(iso: string, options?: { includeYear?: boolean }): string {
  const opts: Intl.DateTimeFormatOptions = {
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }
  if (options?.includeYear) {
    opts.year = 'numeric'
  }
  return new Date(iso).toLocaleDateString('zh-CN', opts)
}
