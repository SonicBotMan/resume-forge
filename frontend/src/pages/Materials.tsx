import { useEffect, useState, useRef, useCallback, memo } from 'react'
import { useNavigate } from 'react-router-dom'
import { materialsApi, analyzeApi } from '../api/client'
import { toastError } from '../stores/toastStore'
import AppHeader from '../components/AppHeader'
import ConfirmDialog from '../components/ConfirmDialog'
import { Spinner } from '../components/Spinner'
import { PageLoader, PageError } from '../components/PageState'
import { formatDate } from '../utils/format'
import type { Material } from '../types'

const STATUS_CONFIG: Record<string, { text: string; color: string }> = {
  pending: { text: '待分析', color: 'bg-slate-100 text-slate-600 border border-slate-200' },
  queued: { text: '排队中', color: 'bg-amber-50 text-amber-600 border border-amber-200' },
  analyzing: { text: '分析中', color: 'bg-blue-50 text-blue-600 border border-blue-200' },
  success: { text: '已完成', color: 'bg-emerald-50 text-emerald-600 border border-emerald-200' },
  failed: { text: '失败', color: 'bg-red-50 text-red-600 border border-red-200' },
}

const TYPE_CONFIG: Record<string, { label: string; emoji: string }> = {
  pdf: { label: 'PDF', emoji: '📄' },
  docx: { label: 'Word', emoji: '📝' },
  pptx: { label: 'PPT', emoji: '📊' },
  text: { label: '文本', emoji: '📝' },
  image: { label: '图片', emoji: '🖼️' },
  text_input: { label: '文本', emoji: '📝' },
}

function formatFileSize(bytes: number | null): string {
  if (bytes === null) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const AnalysisSection = memo(function AnalysisSection({ data }: { data: Record<string, any> }) {
  return (
    <div className="mt-4 pt-4 border-t border-surface-200 space-y-4">
      {data.confidence != null && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-surface-400">置信度</span>
          <span
            className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              data.confidence >= 0.8
                ? 'bg-emerald-50 text-emerald-600'
                : data.confidence >= 0.5
                  ? 'bg-amber-50 text-amber-600'
                  : 'bg-red-50 text-red-600'
            }`}
          >
            {Math.round(data.confidence * 100)}%
          </span>
        </div>
      )}

      {data.summary && (
        <div>
          <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-1.5">摘要</h4>
          <p className="text-sm text-surface-700 leading-relaxed bg-surface-50 rounded-lg p-3">
            {data.summary}
          </p>
        </div>
      )}

      {Array.isArray(data.projects) && data.projects.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">项目经历</h4>
          <div className="space-y-2">
            {data.projects.map((proj: any, i: number) => (
              <div key={i} className="bg-surface-50 rounded-lg p-3 border border-surface-100">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-surface-900">{proj.name || '未命名项目'}</span>
                  {proj.role && (
                    <span className="px-1.5 py-0.5 rounded text-xs bg-primary-50 text-primary-600 border border-primary-100">
                      {proj.role}
                    </span>
                  )}
                </div>
                {(proj.description || proj.result) && (
                  <p className="text-xs text-surface-500 leading-relaxed">{proj.description || proj.result}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {Array.isArray(data.experience) && data.experience.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">工作经历</h4>
          <div className="space-y-2">
            {data.experience.map((exp: any, i: number) => (
              <div key={i} className="bg-surface-50 rounded-lg p-3 border border-surface-100">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className="text-sm font-medium text-surface-900">{exp.company || ''}</span>
                  {exp.position && (
                    <span className="text-xs text-primary-600">{exp.position}</span>
                  )}
                  {exp.period && (
                    <span className="text-xs text-surface-400 ml-auto">{exp.period}</span>
                  )}
                </div>
                {Array.isArray(exp.highlights) && exp.highlights.length > 0 && (
                  <ul className="mt-1.5 space-y-1">
                    {exp.highlights.map((h: string, j: number) => (
                      <li key={j} className="text-xs text-surface-500 flex items-start gap-1.5">
                        <span className="text-surface-300 mt-0.5 shrink-0">•</span>
                        <span>{h}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {Array.isArray(data.skills) && data.skills.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">技能标签</h4>
          <div className="flex flex-wrap gap-1.5">
            {data.skills.map((skill: any, i: number) => (
              <span
                key={i}
                className="px-2.5 py-1 rounded-lg text-xs bg-blue-50 text-blue-700 border border-blue-100"
              >
                {typeof skill === 'string' ? skill : skill.name || JSON.stringify(skill)}
              </span>
            ))}
          </div>
        </div>
      )}

      {Array.isArray(data.education) && data.education.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-2">教育背景</h4>
          <div className="space-y-2">
            {data.education.map((edu: any, i: number) => (
              <div key={i} className="bg-surface-50 rounded-lg p-3 border border-surface-100">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-surface-900">{edu.school || edu.institution || ''}</span>
                  {edu.major && <span className="text-xs text-surface-600">{edu.major}</span>}
                  {edu.degree && (
                    <span className="px-1.5 py-0.5 rounded text-xs bg-purple-50 text-purple-600 border border-purple-100">
                      {edu.degree}
                    </span>
                  )}
                  {edu.period && <span className="text-xs text-surface-400 ml-auto">{edu.period}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
})

interface MaterialItemProps {
  material: any
  isSelected: boolean
  onToggleSelect: () => void
  isQueued: boolean
  onAnalyze: () => void
  onRetry: () => void
  onViewAnalysis: () => void
  isViewingAnalysis: boolean
  expandedAnalysisData: Record<string, any> | undefined
  onDelete: () => void
}

const MaterialItem = memo(function MaterialItem({
  material,
  isSelected,
  onToggleSelect,
  isQueued,
  onAnalyze,
  onRetry,
  onViewAnalysis,
  isViewingAnalysis,
  expandedAnalysisData,
  onDelete,
}: MaterialItemProps) {
  const status = (material.analysis_status || 'pending') as string
  const statusCfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending
  const typeCfg = TYPE_CONFIG[material.source_type] || TYPE_CONFIG.text
  const isActive = status === 'analyzing' || isQueued

  return (
    <div className={`bg-white rounded-xl border transition-all ${
      isSelected ? 'border-primary-300 ring-1 ring-primary-100' : 'border-surface-200 hover:border-surface-300'
    }`}>
      <div className="p-4">
        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={onToggleSelect}
            className="mt-1 w-4 h-4 rounded border-surface-300 bg-surface-50 text-primary-500 focus:ring-primary-500 focus:ring-offset-0 shrink-0"
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <span className="text-sm font-medium text-surface-900 truncate">{material.name}</span>
              <span className="text-xs text-surface-400">{typeCfg.emoji} {typeCfg.label}</span>
              {material.file_size && <span className="text-xs text-surface-400">{formatFileSize(material.file_size)}</span>}
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusCfg.color}`}>
                {isQueued && status === 'pending' ? '排队中' : statusCfg.text}
              </span>
              {material.created_at && (
                <span className="text-xs text-surface-400">{formatDate(material.created_at, { includeYear: true })}</span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            {status === 'pending' && !isQueued && (
              <button onClick={onAnalyze} className="px-3 py-1.5 text-xs bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-all">
                分析
              </button>
            )}
            {status === 'failed' && (
              <button onClick={onRetry} className="px-3 py-1.5 text-xs bg-amber-50 text-amber-600 rounded-lg hover:bg-amber-100 transition-all">
                重试
              </button>
            )}
            {status === 'success' && (
              <button onClick={onViewAnalysis} disabled={isViewingAnalysis} className="px-3 py-1.5 text-xs bg-primary-50 text-primary-600 rounded-lg hover:bg-primary-100 transition-all disabled:opacity-50">
                {isViewingAnalysis ? '加载中...' : '查看分析'}
              </button>
            )}
            <button onClick={onDelete} className="px-3 py-1.5 text-xs text-surface-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all">
              删除
            </button>
          </div>
        </div>
        {isActive && (
          <div className="mt-3 ml-7 flex items-center gap-2">
            <div className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin-slow" />
            <span className="text-xs text-blue-500">正在分析，请稍候...</span>
          </div>
        )}
        {expandedAnalysisData && (
          <div className="ml-7">
            <AnalysisSection data={expandedAnalysisData} />
          </div>
        )}
      </div>
    </div>
  )
})

export default function Materials() {
  const navigate = useNavigate()
  const [materials, setMaterials] = useState<any[]>([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(false)
  const [fetchError, setFetchError] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [inputTab, setInputTab] = useState<'upload' | 'text'>('upload')
  const [textTitle, setTextTitle] = useState('')
  const [textContent, setTextContent] = useState('')
  const [creatingText, setCreatingText] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [typeFilter, setTypeFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [queuedIds, setQueuedIds] = useState<Set<string>>(new Set())
  const [expandedAnalysis, setExpandedAnalysis] = useState<Record<string, any>>({})
  const [loadingAnalysis, setLoadingAnalysis] = useState<Set<string>>(new Set())
  const [batchAnalyzing, setBatchAnalyzing] = useState(false)
  const [confirmAction, setConfirmAction] = useState<{ message: string; onConfirm: () => void } | null>(null)
  const pageSize = 10
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchMaterials = useCallback(async (p: number) => {
    setLoading(true)
    setFetchError(false)
    try {
      const params: Record<string, string | number> = { page: p, page_size: pageSize }
      if (typeFilter !== 'all') params.type = typeFilter
      if (statusFilter !== 'all') params.status = statusFilter
      const response = await materialsApi.list(params)
      const data = response.data
      if (Array.isArray(data)) {
        setMaterials(data)
        setTotalPages(1)
      } else {
        setMaterials(data.items || [])
        setTotalPages(data.total_pages || Math.ceil((data.total || 0) / pageSize) || 1)
      }
    } catch {
      setFetchError(true)
    } finally {
      setLoading(false)
    }
  }, [typeFilter, statusFilter])

  useEffect(() => {
    setPage(1)
    fetchMaterials(1)
  }, [typeFilter, statusFilter, fetchMaterials])

  useEffect(() => {
    if (page > 1) fetchMaterials(page)
  }, [page, fetchMaterials])

  useEffect(() => {
    setSelectedIds(new Set())
  }, [typeFilter, statusFilter])

  const hasActive = materials.some((m) => m.analysis_status === 'analyzing' || queuedIds.has(m.id))
  useEffect(() => {
    if (!hasActive) {
      if (pollingRef.current) clearInterval(pollingRef.current)
      pollingRef.current = null
      return
    }
    if (pollingRef.current) return

    pollingRef.current = setInterval(async () => {
      const activeIds = materials
        .filter((m) => m.analysis_status === 'analyzing' || queuedIds.has(m.id))
        .map((m) => m.id)
      if (activeIds.length === 0) {
        if (pollingRef.current) clearInterval(pollingRef.current)
        pollingRef.current = null
        return
      }
      try {
        const results = await Promise.allSettled(
          activeIds.map((id) => analyzeApi.getStatus(id))
        )
        setMaterials((prev) =>
          prev.map((m) => {
            const idx = activeIds.indexOf(m.id)
            if (idx === -1) return m
            const result = results[idx]
            if (result.status === 'fulfilled') {
              const status = result.value.data?.status
              if (status && status !== m.analysis_status) {
                if (status === 'success' || status === 'failed') {
                  setQueuedIds((prev) => { const next = new Set(prev); next.delete(m.id); return next })
                }
                return { ...m, analysis_status: status as Material['analysis_status'] }
              }
            }
            return m
          })
        )
      } catch {
        // intentionally empty: polling continues on failure
      }
    }, 3000)

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [hasActive])

  const handleFileUpload = async (file: File) => {
    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    try {
      await materialsApi.upload(formData)
      fetchMaterials(page)
    } catch {
      toastError('上传失败')
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) handleFileUpload(files[0])
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => setIsDragging(false)

  const handleCreateText = async () => {
    if (!textTitle.trim() || !textContent.trim()) {
      toastError('请填写标题和内容')
      return
    }
    setCreatingText(true)
    try {
      await materialsApi.createText({ title: textTitle, content: textContent })
      setTextTitle('')
      setTextContent('')
      fetchMaterials(page)
    } catch {
      toastError('创建文本资料失败')
    } finally {
      setCreatingText(false)
    }
  }

  const handleDelete = async (id: string) => {
    setConfirmAction({
      message: '确定删除这个资料？删除后无法恢复。',
      onConfirm: async () => {
        setConfirmAction(null)
        try {
          await materialsApi.delete(id)
          setMaterials((prev) => prev.filter((m) => m.id !== id))
          setSelectedIds((prev) => {
            const next = new Set(prev)
            next.delete(id)
            return next
          })
        } catch {
          toastError('删除失败')
        }
      },
    })
  }

  const handleAnalyzeSingle = async (id: string) => {
    try {
      await analyzeApi.analyzeSingle(id)
      setQueuedIds((prev) => new Set(prev).add(id))
      setMaterials((prev) =>
        prev.map((m) => (m.id === id ? { ...m, analysis_status: 'pending' as const } : m))
      )
    } catch {
      toastError('触发分析失败')
    }
  }

  const handleRetry = async (id: string) => {
    try {
      await analyzeApi.retry(id)
      setQueuedIds((prev) => new Set(prev).add(id))
      setMaterials((prev) =>
        prev.map((m) => (m.id === id ? { ...m, analysis_status: 'pending' as const } : m))
      )
    } catch {
      toastError('重试失败')
    }
  }

  const fetchAnalysis = async (id: string) => {
    setLoadingAnalysis((prev) => new Set(prev).add(id))
    try {
      const response = await analyzeApi.getResult(id)
      setExpandedAnalysis((prev) => ({ ...prev, [id]: response.data }))
    } catch {
      toastError('获取分析结果失败')
    } finally {
      setLoadingAnalysis((prev) => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    }
  }

  const handleBatchAnalyze = async () => {
    if (selectedIds.size === 0) {
      toastError('请先选择要分析的资料')
      return
    }
    setBatchAnalyzing(true)
    try {
      await analyzeApi.batchAnalyze({ material_ids: Array.from(selectedIds) })
      setQueuedIds((prev) => { const next = new Set(prev); selectedIds.forEach(id => next.add(id)); return next })
      setMaterials((prev) =>
        prev.map((m) =>
          selectedIds.has(m.id) ? { ...m, analysis_status: 'pending' as const } : m
        )
      )
      setSelectedIds(new Set())
    } catch {
      toastError('批量分析失败')
    } finally {
      setBatchAnalyzing(false)
    }
  }

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === materials.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(materials.map((m) => m.id)))
    }
  }

  if (loading && materials.length === 0) {
    return <PageLoader />
  }

  if (fetchError && materials.length === 0) {
    return <PageError title="资料库" activeNav="materials" message="无法加载资料列表，请检查网络连接后重试" onRetry={() => fetchMaterials(1)} />
  }

  return (
    <div className="min-h-screen bg-surface-50">
      <AppHeader title="资料库" activeNav="materials" />

      <main className="max-w-5xl mx-auto p-4 sm:p-6">
        {materials.some((m) => m.analysis_status === 'success') && (
          <div className="bg-primary-50 border border-primary-200 rounded-xl p-4 mb-6 flex items-center justify-between">
            <div>
              <p className="text-sm text-primary-600 font-medium">资料分析已完成</p>
              <p className="text-xs text-surface-500 mt-0.5">你可以基于已分析的资料生成底版简历了</p>
            </div>
            <button
              onClick={() => navigate('/resumes')}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 text-sm transition-all shadow-sm shadow-primary-500/10"
            >
              生成底版简历 →
            </button>
          </div>
        )}
        <div className="bg-white rounded-xl border border-surface-200 mb-6 overflow-hidden">
          <div className="flex border-b border-surface-200">
            <button
              onClick={() => setInputTab('upload')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-all ${
                inputTab === 'upload'
                  ? 'text-primary-600 border-b-2 border-primary-500 bg-primary-50/50'
                  : 'text-surface-500 hover:text-surface-700 hover:bg-surface-50'
              }`}
            >
              📤 上传资料
            </button>
            <button
              onClick={() => setInputTab('text')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-all ${
                inputTab === 'text'
                  ? 'text-primary-600 border-b-2 border-primary-500 bg-primary-50/50'
                  : 'text-surface-500 hover:text-surface-700 hover:bg-surface-50'
              }`}
            >
              📝 文本资料
            </button>
          </div>

          {inputTab === 'upload' && (
            <div
              className={`p-8 border-2 border-dashed m-4 rounded-lg transition-all ${
                isDragging
                  ? 'border-primary-500 bg-primary-50/50'
                  : 'border-surface-300 hover:border-primary-300'
              }`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <div className="text-center">
                <div className="text-4xl mb-3">
                  {uploading ? '⏳' : '📂'}
                </div>
                <p className="text-surface-700 mb-4">
                  {uploading ? '正在上传...' : '拖拽文件到这里，或点击按钮选择文件'}
                </p>
                <p className="text-xs text-surface-400 mb-4">
                  支持 PDF、Word、PPT、图片等格式
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  accept=".pdf,.doc,.docx,.ppt,.pptx,.txt,.png,.jpg,.jpeg,.webp"
                  onChange={(e) => {
                    const file = e.target.files?.[0]
                    if (file) handleFileUpload(file)
                    e.target.value = ''
                  }}
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="px-6 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-500 transition-all shadow-sm shadow-primary-500/10 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? '上传中...' : '选择文件'}
                </button>
              </div>
            </div>
          )}

          {inputTab === 'text' && (
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm text-surface-700 mb-1.5">标题</label>
                <input
                  type="text"
                  value={textTitle}
                  onChange={(e) => setTextTitle(e.target.value)}
                  className="w-full px-4 py-2 bg-surface-50 border border-surface-200 rounded-lg text-surface-900 placeholder-surface-300 focus:outline-none focus:border-primary-500 transition-colors"
                  placeholder="例如：项目经历整理、个人总结..."
                />
              </div>
              <div>
                <label className="block text-sm text-surface-700 mb-1.5">内容</label>
                <textarea
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  rows={6}
                  className="w-full px-4 py-2 bg-surface-50 border border-surface-200 rounded-lg text-surface-900 placeholder-surface-300 focus:outline-none focus:border-primary-500 resize-none transition-colors"
                  placeholder="粘贴或输入你的文本资料..."
                />
              </div>
              <div className="flex justify-end">
                <button
                  onClick={handleCreateText}
                  disabled={creatingText || !textTitle.trim() || !textContent.trim()}
                  className="px-6 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-500 transition-all shadow-sm shadow-primary-500/10 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {creatingText ? '创建中...' : '添加文本'}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setTypeFilter('all')}
              className={`px-4 py-2 rounded-lg text-xs transition-all ${
                typeFilter === 'all'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white border border-surface-200 text-surface-500 hover:bg-surface-100 hover:text-surface-700'
              }`}
            >
              全部类型
            </button>
            <button
              onClick={() => setTypeFilter('upload')}
              className={`px-4 py-2 rounded-lg text-xs transition-all ${
                typeFilter === 'upload'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white border border-surface-200 text-surface-500 hover:bg-surface-100 hover:text-surface-700'
              }`}
            >
              📤 上传
            </button>
            <button
              onClick={() => setTypeFilter('text')}
              className={`px-4 py-2 rounded-lg text-xs transition-all ${
                typeFilter === 'text'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white border border-surface-200 text-surface-500 hover:bg-surface-100 hover:text-surface-700'
              }`}
            >
              📝 文本
            </button>

            <span className="text-surface-300 self-center">|</span>

            <button
              onClick={() => setStatusFilter('all')}
              className={`px-4 py-2 rounded-lg text-xs transition-all ${
                statusFilter === 'all'
                  ? 'bg-slate-600 text-white'
                  : 'bg-white border border-surface-200 text-surface-500 hover:bg-surface-100 hover:text-surface-700'
              }`}
            >
              全部状态
            </button>
            <button
              onClick={() => setStatusFilter('pending')}
              className={`px-4 py-2 rounded-lg text-xs transition-all ${
                statusFilter === 'pending'
                  ? 'bg-slate-600 text-white'
                  : 'bg-white border border-surface-200 text-surface-500 hover:bg-surface-100 hover:text-surface-700'
              }`}
            >
              待分析
            </button>
            <button
              onClick={() => setStatusFilter('analyzing')}
              className={`px-4 py-2 rounded-lg text-xs transition-all ${
                statusFilter === 'analyzing'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-surface-200 text-surface-500 hover:bg-surface-100 hover:text-surface-700'
              }`}
            >
              分析中
            </button>
            <button
              onClick={() => setStatusFilter('success')}
              className={`px-4 py-2 rounded-lg text-xs transition-all ${
                statusFilter === 'success'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-white border border-surface-200 text-surface-500 hover:bg-surface-100 hover:text-surface-700'
              }`}
            >
              已完成
            </button>
            <button
              onClick={() => setStatusFilter('failed')}
              className={`px-4 py-2 rounded-lg text-xs transition-all ${
                statusFilter === 'failed'
                  ? 'bg-red-600 text-white'
                  : 'bg-white border border-surface-200 text-surface-500 hover:bg-surface-100 hover:text-surface-700'
              }`}
            >
              失败
            </button>
          </div>

          {selectedIds.size > 0 && (
            <button
              onClick={handleBatchAnalyze}
              disabled={batchAnalyzing}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 text-sm transition-all shadow-sm shadow-primary-500/10 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {batchAnalyzing && <Spinner />}
              分析选中 ({selectedIds.size})
            </button>
          )}
        </div>

        {materials.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">📂</div>
            <h2 className="text-lg font-semibold text-surface-900 mb-2">还没有资料</h2>
            <p className="text-surface-400 mb-6">上传文件或添加文本开始积累你的资料库</p>
            <button
              onClick={() => setInputTab('upload')}
              className="px-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-500 transition-all shadow-sm shadow-primary-500/10"
            >
              开始添加资料
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-3 mb-2 px-1">
              <input
                type="checkbox"
                checked={selectedIds.size === materials.length && materials.length > 0}
                onChange={toggleSelectAll}
                 className="w-4 h-4 rounded border-surface-300 bg-surface-50 text-primary-500 focus:ring-primary-500 focus:ring-offset-0"
               />
               <span className="text-xs text-surface-400">
                {selectedIds.size > 0 ? `已选 ${selectedIds.size} 项` : `共 ${materials.length} 项`}
              </span>
            </div>

            <div className="grid gap-3">
              {materials.map((material) => (
                <MaterialItem
                  key={material.id}
                  material={material}
                  isSelected={selectedIds.has(material.id)}
                  onToggleSelect={() => toggleSelect(material.id)}
                  isQueued={queuedIds.has(material.id)}
                  onAnalyze={() => handleAnalyzeSingle(material.id)}
                  onRetry={() => handleRetry(material.id)}
                  onViewAnalysis={() => fetchAnalysis(material.id)}
                  isViewingAnalysis={loadingAnalysis.has(material.id)}
                  expandedAnalysisData={expandedAnalysis[material.id]}
                  onDelete={() => handleDelete(material.id)}
                />
              ))}
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-6">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-4 py-2 text-sm text-surface-500 hover:text-surface-700 hover:bg-surface-50 rounded-lg transition-all disabled:text-surface-300 disabled:cursor-not-allowed disabled:hover:bg-transparent"
                >
                  上一页
                </button>
                <span className="text-sm text-surface-400 px-2">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-4 py-2 text-sm text-surface-500 hover:text-surface-700 hover:bg-surface-50 rounded-lg transition-all disabled:text-surface-300 disabled:cursor-not-allowed disabled:hover:bg-transparent"
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </main>
      <ConfirmDialog open={!!confirmAction} message={confirmAction?.message || ''} onConfirm={confirmAction?.onConfirm || (() => {})} onCancel={() => setConfirmAction(null)} />
    </div>
  )
}
