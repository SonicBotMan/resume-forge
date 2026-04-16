import { useEffect, useState, useCallback, useRef, memo, useMemo, forwardRef } from 'react'
import { toastError, toastSuccess } from '../stores/toastStore'
import AppHeader from '../components/AppHeader'
import ConfirmDialog from '../components/ConfirmDialog'
import { Spinner } from '../components/Spinner'
import { PageLoader } from '../components/PageState'
import { resumesApi, reviewsApi, jdsApi } from '../api/client'
import type { BaseResume, TargetedResume, JD, Review } from '../types'
import { formatDate } from '../utils/format'
import { toPng } from 'html-to-image'

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const ResumeImageRenderer = forwardRef<HTMLDivElement, { content: any; name: string; jdTitle?: string }>(
  function ResumeImageRenderer({ content, name: _name, jdTitle }, ref) {
    const summary: string = content.summary || ''
    const experience: Record<string, any>[] = Array.isArray(content.experience) ? content.experience : []
    const projects: Record<string, any>[] = Array.isArray(content.projects) ? content.projects : []
    const skills: string[] = Array.isArray(content.skills) ? content.skills : []
    const education: Record<string, any>[] = Array.isArray(content.education) ? content.education : []
    const personalInfo: Record<string, string> = content.personal_info || {}

    const sectionTitleStyle: React.CSSProperties = {
      fontSize: '13px',
      fontWeight: 700,
      color: '#2563eb',
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
      borderBottom: '2px solid #2563eb',
      paddingBottom: '4px',
      marginTop: '16px',
      marginBottom: '8px',
    }

    return (
      <div ref={ref} style={{
        width: '794px',
        minHeight: '1123px',
        backgroundColor: '#ffffff',
        padding: '48px',
        fontFamily: '"PingFang SC", "Microsoft YaHei", "Hiragino Sans GB", sans-serif',
        color: '#374151',
        fontSize: '12px',
        lineHeight: '1.6',
        boxSizing: 'border-box',
      }}>
        {/* Header: Name + Target Position + Contact */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
          <div>
            <div style={{ fontSize: '24px', fontWeight: 700, color: '#1a1a1a', lineHeight: 1.3 }}>
              {personalInfo.name || '简历'}
            </div>
            {jdTitle && (
              <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
                求职意向：{jdTitle}
              </div>
            )}
          </div>
          <div style={{ fontSize: '11px', color: '#6b7280', textAlign: 'right', lineHeight: 1.8, flexShrink: 0 }}>
            {personalInfo.phone && <span>{personalInfo.phone}</span>}
            {personalInfo.email && personalInfo.phone && <span style={{ margin: '0 6px' }}>|</span>}
            {personalInfo.email && <span>{personalInfo.email}</span>}
            {personalInfo.location && (personalInfo.phone || personalInfo.email) && <span style={{ margin: '0 6px' }}>|</span>}
            {personalInfo.location && <span>{personalInfo.location}</span>}
          </div>
        </div>

        {/* Divider */}
        <div style={{ borderBottom: '1px solid #e5e7eb', marginTop: '8px', marginBottom: '4px' }} />

        {/* Summary */}
        {summary && (
          <div>
            <div style={sectionTitleStyle}>个人简介</div>
            <p style={{ fontSize: '11px', color: '#374151', lineHeight: 1.8, margin: 0 }}>{summary}</p>
          </div>
        )}

        {/* Experience */}
        {experience.length > 0 && (
          <div>
            <div style={sectionTitleStyle}>工作经历</div>
            {experience.map((exp, i) => (
              <div key={i} style={{ marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <span style={{ fontSize: '12px', fontWeight: 700, color: '#1a1a1a' }}>
                    {exp.company}{exp.position ? <span style={{ fontWeight: 400, color: '#374151' }}> · {exp.position}</span> : ''}
                  </span>
                  {exp.period && <span style={{ fontSize: '11px', color: '#6b7280', flexShrink: 0 }}>{exp.period}</span>}
                </div>
                {exp.highlights?.length > 0 && (
                  <div style={{ marginTop: '4px' }}>
                    {exp.highlights.map((h: string, j: number) => (
                      <div key={j} style={{ fontSize: '11px', color: '#374151', lineHeight: 1.7, paddingLeft: '10px', position: 'relative' }}>
                        <span style={{ position: 'absolute', left: 0 }}>•</span>{h}
                      </div>
                    ))}
                  </div>
                )}
                {exp.responsibilities?.length > 0 && (
                  <div style={{ marginTop: '4px' }}>
                    {exp.responsibilities.map((r: string, j: number) => (
                      <div key={j} style={{ fontSize: '11px', color: '#374151', lineHeight: 1.7, paddingLeft: '10px', position: 'relative' }}>
                        <span style={{ position: 'absolute', left: 0 }}>•</span>{r}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Projects */}
        {projects.length > 0 && (
          <div>
            <div style={sectionTitleStyle}>项目经历</div>
            {projects.map((p, i) => (
              <div key={i} style={{ marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <span style={{ fontSize: '12px', fontWeight: 700, color: '#1a1a1a' }}>
                    {p.name}
                    {p.role && <span style={{ fontWeight: 400, color: '#6b7280', marginLeft: '8px' }}>{p.role}</span>}
                  </span>
                  {(p.start_date || p.end_date) && (
                    <span style={{ fontSize: '11px', color: '#6b7280', flexShrink: 0 }}>
                      {[p.start_date, p.end_date].filter(Boolean).join(' - ')}
                    </span>
                  )}
                </div>
                {p.description && (
                  <p style={{ fontSize: '11px', color: '#374151', lineHeight: 1.7, margin: '4px 0 0 0' }}>{p.description}</p>
                )}
                {(p.situation || p.task || p.action || p.result) && (
                  <div style={{ marginTop: '4px' }}>
                    {p.situation && <p style={{ fontSize: '11px', color: '#374151', lineHeight: 1.7, margin: 0 }}>背景: {p.situation}</p>}
                    {p.task && <p style={{ fontSize: '11px', color: '#374151', lineHeight: 1.7, margin: 0 }}>任务: {p.task}</p>}
                    {p.action && <p style={{ fontSize: '11px', color: '#374151', lineHeight: 1.7, margin: 0 }}>行动: {p.action}</p>}
                    {p.result && <p style={{ fontSize: '11px', color: '#374151', lineHeight: 1.7, margin: 0 }}>成果: {p.result}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Skills */}
        {skills.length > 0 && (
          <div>
            <div style={sectionTitleStyle}>技能</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {skills.map((s, i) => (
                <span key={i} style={{
                  display: 'inline-block',
                  padding: '2px 10px',
                  fontSize: '10px',
                  color: '#1d4ed8',
                  backgroundColor: '#eff6ff',
                  borderRadius: '3px',
                }}>{typeof s === 'string' ? s : String(s)}</span>
              ))}
            </div>
          </div>
        )}

        {/* Education */}
        {education.length > 0 && (
          <div>
            <div style={sectionTitleStyle}>教育背景</div>
            {education.map((e, i) => (
              <div key={i} style={{ marginBottom: '4px' }}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#1a1a1a' }}>{e.school}</span>
                {e.major && <span style={{ color: '#374151' }}> · {e.major}</span>}
                {e.degree && <span style={{ color: '#6b7280' }}> · {e.degree}</span>}
                {e.period && <span style={{ color: '#6b7280', marginLeft: '12px' }}>{e.period}</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }
)

const GRADE_STYLES: Record<string, string> = {
  A: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
  B: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
  C: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
  D: 'bg-red-500/10 text-red-400 border border-red-500/20',
}

const REVIEW_STATUS: Record<string, { label: string; color: string; spin?: boolean }> = {
  pending: { label: '排队中', color: 'bg-surface-100 text-surface-500' },
  running: { label: '分析中', color: 'bg-blue-500/10 text-blue-400 border border-blue-500/20', spin: true },
  completed: { label: '已完成', color: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' },
  failed: { label: '失败', color: 'bg-red-500/10 text-red-400 border border-red-500/20' },
}



function SectionHeading({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h2 className="text-lg font-semibold text-surface-900">{title}</h2>
      {children}
    </div>
  )
}

interface DropdownItem {
  id: string
  label: string
  sublabel?: string
}

function Dropdown({
  items,
  placeholder,
  onSelect,
  disabled,
}: {
  items: DropdownItem[]
  placeholder: string
  onSelect: (id: string) => void
  disabled?: boolean
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  if (items.length === 0) {
    return (
      <span className="text-sm text-surface-400">{placeholder}</span>
    )
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        disabled={disabled}
        className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 text-sm transition-all shadow-sm shadow-primary-500/10 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {placeholder} ▾
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-72 bg-white border border-surface-200 shadow-lg rounded-xl z-50 max-h-64 overflow-y-auto">
          {items.map((item) => (
            <button
              key={item.id}
              onClick={() => { onSelect(item.id); setOpen(false) }}
              className="w-full text-left px-4 py-3 hover:bg-surface-50 transition-colors border-b border-surface-100 last:border-0"
            >
              <div className="text-sm text-surface-900">{item.label}</div>
              {item.sublabel && <div className="text-xs text-surface-400 mt-0.5">{item.sublabel}</div>}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function ExportMenu({ onResumeId, onResumeName, onExportPng }: { onResumeId: string; onResumeName?: string; onExportPng: () => void }) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleExport = async (format: 'pdf' | 'docx' | 'txt') => {
    setOpen(false)
    setLoading(true)
    try {
      const res = await resumesApi.exportTargeted(onResumeId, format)
      const fileName = onResumeName ? `${onResumeName}.${format}` : `resume_${onResumeId.slice(0, 8)}.${format}`
      downloadBlob(res.data as Blob, fileName)
    } catch {
      toastError('导出失败')
    } finally {
      setLoading(false)
    }
  }

  const handleFormatClick = (f: string) => {
    setOpen(false)
    if (f === 'png') {
      onExportPng()
    } else {
      handleExport(f as 'pdf' | 'docx' | 'txt')
    }
  }

  return (
    <div className="relative inline-block" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        disabled={loading}
        className="px-4 py-2 text-sm text-surface-500 hover:bg-surface-50 rounded-lg transition-all disabled:opacity-50"
      >
        {loading ? <Spinner className="w-3.5 h-3.5" /> : '导出 ▾'}
      </button>
      {open && (
        <div className="absolute right-0 mt-1 w-32 bg-white border border-surface-200 shadow-lg rounded-lg z-50">
          {(['pdf', 'docx', 'txt', 'png'] as const).map((f) => (
            <button
              key={f}
              onClick={() => handleFormatClick(f)}
              className="w-full text-left px-3 py-2 text-sm text-surface-700 hover:bg-surface-50 uppercase transition-colors"
            >
              {f}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function GeneratingOverlay({
  title,
  subtitle,
  stage,
  stages,
}: {
  title: string
  subtitle: string
  stage: number
  stages: { label: string; desc: string }[]
}) {
  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-8 border border-surface-200 shadow-2xl max-w-sm w-full mx-4 text-center">
        <div className="flex justify-center mb-5">
          <div className="w-10 h-10 border-[3px] border-primary-200 border-t-primary-600 rounded-full animate-spin" />
        </div>
        <h3 className="text-lg font-semibold text-surface-900 mb-1">{title}</h3>
        <p className="text-sm text-surface-500 mb-6">{subtitle}</p>
        <div className="space-y-3 text-left">
          {stages.map((s, i) => (
            <div key={i} className="flex items-start gap-3">
              {i < stage ? (
                <div className="w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center shrink-0 mt-0.5">
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              ) : i === stage ? (
                <div className="w-5 h-5 rounded-full border-2 border-primary-500 border-t-transparent animate-spin shrink-0 mt-0.5" />
              ) : (
                <div className="w-5 h-5 rounded-full bg-surface-100 shrink-0 mt-0.5" />
              )}
              <div>
                <p className={`text-sm font-medium ${i <= stage ? 'text-surface-900' : 'text-surface-400'}`}>{s.label}</p>
                <p className={`text-xs ${i <= stage ? 'text-surface-500' : 'text-surface-300'}`}>{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

const BaseResumeCard = memo(function BaseResumeCard({
  content,
  updatedAt,
}: {
  content: Record<string, any> | null
  updatedAt: string
}) {
  const c = content as Record<string, any> | null
  if (!c) return null
  const personal: Record<string, string> = c.personal_info ?? {}
  const experience: Record<string, any>[] = Array.isArray(c.experience) ? c.experience : []
  const projects: Record<string, any>[] = Array.isArray(c.projects) ? c.projects : []
  const skills: string[] = Array.isArray(c.skills) ? c.skills : []
  const education: Record<string, any>[] = Array.isArray(c.education) ? c.education : []
  const highlights: string[] = Array.isArray(c.career_highlights) ? c.career_highlights : []
  const summary: string = c.summary ?? ''

  const hasContent = personal.name || summary || experience.length > 0 || projects.length > 0 || skills.length > 0 || education.length > 0 || highlights.length > 0

  const latestPosition = experience[0]?.position || ''
  const latestCompany = experience[0]?.company || ''
  const stats = [
    experience.length > 0 ? `${experience.length}段经历` : null,
    projects.length > 0 ? `${projects.length}个项目` : null,
    skills.length > 0 ? `${skills.length}项技能` : null,
  ].filter(Boolean).join(' · ')

  if (!hasContent) return (
    <div className="bg-white border border-surface-200 rounded-xl p-5 hover:border-surface-300 transition-all duration-200">
      <div className="flex items-center justify-between">
        <span className="text-sm text-surface-500">更新于 {formatDate(updatedAt)}</span>
        <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">已生成</span>
      </div>
      <p className="text-surface-400 text-sm mt-2">简历内容为空</p>
    </div>
  )

  return (
    <details className="group bg-white border border-surface-200 rounded-xl hover:border-surface-300 transition-all duration-200">
      <summary className="flex items-center justify-between gap-3 p-4 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-lg bg-primary-50 flex items-center justify-center shrink-0 border border-primary-100">
            <span className="text-primary-600 text-sm font-semibold">{(personal.name || '简')[0]}</span>
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium text-surface-900 truncate">{personal.name || '底版简历'}</span>
              <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">已生成</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-surface-400 mt-0.5">
              {latestPosition && <span className="truncate">{latestPosition}{latestCompany ? ` · ${latestCompany}` : ''}</span>}
              {stats && <span className="shrink-0">{stats}</span>}
              <span className="shrink-0">更新于 {formatDate(updatedAt)}</span>
            </div>
          </div>
        </div>
        <svg className="w-4 h-4 text-surface-300 transition-transform group-open:rotate-180 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
      </summary>
      <div className="px-5 pb-5 border-t border-surface-100">
        <div className="max-h-[70vh] sm:max-h-[600px] overflow-y-auto space-y-5 text-sm pr-1 pt-4">
        {personal.name && (
          <div className="pb-4 border-b border-surface-100">
            <h3 className="text-xl font-bold text-surface-900 tracking-tight">{personal.name}</h3>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-surface-500 text-xs">
              {personal.phone && <span>{personal.phone}</span>}
              {personal.email && <span>{personal.email}</span>}
              {personal.location && <span>{personal.location}</span>}
              {personal.birth_year && <span>{personal.birth_year}</span>}
            </div>
          </div>
        )}

        {summary && (
          <div className="bg-primary-50/50 border-l-2 border-primary-400 rounded-r-lg px-4 py-3">
            <p className="text-surface-700 leading-relaxed">{summary}</p>
          </div>
        )}

        {experience.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">工作经历</h4>
            <div className="space-y-3">
              {experience.map((exp, i) => (
                <div key={i} className="bg-surface-50 rounded-lg p-3">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="font-medium text-surface-900">
                      {exp.position}{exp.department ? <span className="text-surface-400 font-normal"> · {exp.department}</span> : ''}
                    </span>
                    {exp.period && <span className="text-xs text-surface-400 shrink-0">{exp.period}</span>}
                  </div>
                  <div className="text-surface-500 text-xs mt-0.5">{exp.company}</div>
                  {exp.responsibilities?.length > 0 && (
                    <ul className="mt-2 space-y-1">
                      {exp.responsibilities.map((r: string, j: number) => (
                        <li key={j} className="text-surface-600 pl-3 relative before:content-['•'] before:absolute before:left-0 before:text-surface-300">{r}</li>
                      ))}
                    </ul>
                  )}
                  {exp.highlights?.length > 0 && (
                    <ul className="mt-2 space-y-1">
                      {exp.highlights.map((h: string, j: number) => (
                        <li key={j} className="text-primary-700 pl-4 relative before:content-['★'] before:absolute before:left-0 before:text-primary-400 text-xs">{h}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {projects.length > 0 && (
          <details open={projects.length <= 5} className="group">
            <summary className="text-xs font-semibold text-surface-400 uppercase tracking-wider cursor-pointer hover:text-surface-600 transition-colors list-none flex items-center gap-2 mb-3 select-none [&::-webkit-details-marker]:hidden">
              <svg className="w-3 h-3 text-surface-300 transition-transform group-open:rotate-90 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path d="M6 6l8 4-8 4V6z"/></svg>
              项目经历
              <span className="text-surface-300 font-normal">({projects.length})</span>
            </summary>
            <div className="space-y-2">
              {projects.map((p, i) => (
                <div key={i} className="bg-surface-50 rounded-lg p-3">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="font-medium text-surface-800">{p.name}</span>
                    {(p.start_date || p.end_date) && (
                      <span className="text-xs text-surface-400 shrink-0">
                        {[p.start_date, p.end_date].filter(Boolean).join(' – ')}
                      </span>
                    )}
                  </div>
                  {p.role && <div className="text-xs text-surface-500 mt-0.5">{p.role}</div>}
                  {p.description && <p className="text-surface-600 mt-1.5 text-xs leading-relaxed">{p.description}</p>}
                  {(p.situation || p.task || p.action || p.result) && (
                    <div className="mt-2 space-y-1 text-xs border-t border-surface-100 pt-2">
                      {p.situation && <div><span className="inline-block w-4 text-primary-500 font-semibold">S</span><span className="text-surface-600">{p.situation}</span></div>}
                      {p.task && <div><span className="inline-block w-4 text-primary-500 font-semibold">T</span><span className="text-surface-600">{p.task}</span></div>}
                      {p.action && <div><span className="inline-block w-4 text-primary-500 font-semibold">A</span><span className="text-surface-600">{p.action}</span></div>}
                      {p.result && <div><span className="inline-block w-4 text-primary-500 font-semibold">R</span><span className="text-surface-600">{p.result}</span></div>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </details>
        )}

        {skills.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">技能</h4>
            <div className="flex flex-wrap gap-1.5">
              {skills.map((s, i) => (
                <span key={i} className="px-2 py-0.5 bg-primary-50 text-primary-700 rounded text-xs border border-primary-100">{s}</span>
              ))}
            </div>
          </div>
        )}

        {education.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">教育经历</h4>
            <div className="space-y-1.5">
              {education.map((e, i) => (
                <div key={i} className="text-surface-700">
                  <span className="font-medium">{e.school}</span>
                  {e.major && <span className="text-surface-500"> · {e.major}</span>}
                  {e.degree && <span className="text-surface-400 text-xs"> ({e.degree})</span>}
                  {e.period && <span className="text-surface-400 text-xs ml-2">{e.period}</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        {highlights.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">职业亮点</h4>
            <ul className="space-y-1.5">
              {highlights.map((h, i) => (
                <li key={i} className="text-surface-600 pl-4 relative before:content-['•'] before:absolute before:left-0 before:text-primary-400">{h}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
      </div>
    </details>
  )
})


function ReviewSection({
  reviews,
  expandedReview,
  reviewDetails,
  onToggle,
  onFetchDetail,
  onCreateReview,
  creatingReview,
  onRegenerate,
  regeneratingReviewId,
  onDelete,
  emptyText,
}: {
  reviews: Review[]
  expandedReview: string | null
  reviewDetails: Record<string, any>
  onToggle: (id: string) => void
  onFetchDetail: (id: string) => void
  onCreateReview: () => void
  creatingReview: boolean
  onRegenerate: (id: string) => void
  regeneratingReviewId: string | null
  onDelete: (id: string) => void
  emptyText: string
}) {
  return (
    <div className="mt-2">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-surface-400 font-medium">评审记录 ({reviews.length})</span>
        <button
          onClick={onCreateReview}
          disabled={creatingReview}
          className="px-3 py-1.5 text-xs text-primary-600 hover:bg-primary-50 rounded-lg transition-all disabled:opacity-50 flex items-center gap-1.5"
        >
          {creatingReview ? <Spinner className="w-3 h-3" /> : <span>🔍</span>}
          {creatingReview ? '发起中...' : '发起评审'}
        </button>
      </div>
      {reviews.length === 0 ? (
        <div className="text-xs text-surface-400 py-2 text-center">{emptyText}</div>
      ) : (
        <div className="space-y-2">
          {reviews.map((review) => (
            <ReviewCard
              key={review.id}
              review={review}
              isExpanded={expandedReview === review.id}
              onToggle={() => onToggle(review.id)}
              details={reviewDetails[review.id]}
              onFetchDetail={() => onFetchDetail(review.id)}
              onRegenerate={review.resume_type === 'targeted' ? () => onRegenerate(review.id) : undefined}
              regenerating={regeneratingReviewId === review.id}
              onDelete={() => onDelete(review.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

const ReviewCard = memo(function ReviewCard({
  review,
  isExpanded,
  onToggle,
  details,
  onFetchDetail,
  onRegenerate,
  regenerating,
  onDelete,
}: {
  review: Review
  isExpanded: boolean
  onToggle: () => void
  details: any
  onFetchDetail: () => void
  onRegenerate?: () => void
  regenerating?: boolean
  onDelete?: () => void
}) {
  const st = REVIEW_STATUS[review.status] ?? REVIEW_STATUS.pending

  const renderRoleReview = (data: any) => {
    if (!data || typeof data === 'string') return <p className="text-sm text-surface-700 whitespace-pre-wrap">{data || '无数据'}</p>
    return (
      <div className="space-y-2">
        {data.key_insight && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-2.5">
            <p className="text-xs text-amber-600 font-medium mb-0.5">核心洞察</p>
            <p className="text-sm text-amber-800">{data.key_insight}</p>
          </div>
        )}
        {data.score_impact && (
          <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
            data.score_impact === 'positive' ? 'bg-emerald-50 text-emerald-600' :
            data.score_impact === 'negative' ? 'bg-red-50 text-red-600' :
            'bg-surface-100 text-surface-600'
          }`}>
            影响评估: {data.score_impact === 'positive' ? '正面' : data.score_impact === 'negative' ? '负面' : '中性'}
          </span>
        )}
        {Array.isArray(data.problems) && data.problems.length > 0 && (
          <div>
            <p className="text-xs text-red-500 font-medium mb-1">发现的问题</p>
            <ul className="space-y-1">{data.problems.map((p: string, i: number) => (
              <li key={i} className="text-sm text-surface-700 flex gap-2"><span className="text-red-400 shrink-0">•</span><span>{p}</span></li>
            ))}</ul>
          </div>
        )}
        {Array.isArray(data.suggestions) && data.suggestions.length > 0 && (
          <div>
            <p className="text-xs text-emerald-600 font-medium mb-1">改进建议</p>
            <ul className="space-y-1">{data.suggestions.map((s: string, i: number) => (
              <li key={i} className="text-sm text-surface-700 flex gap-2"><span className="text-emerald-400 shrink-0">•</span><span>{s}</span></li>
            ))}</ul>
          </div>
        )}
      </div>
    )
  }

  const renderSynthesis = (syn: any) => {
    if (!syn || typeof syn === 'string') return <p className="text-sm text-surface-700 whitespace-pre-wrap">{syn || '无数据'}</p>
    return (
      <div className="space-y-3">
        {syn.overall_assessment && (
          <div className="bg-primary-50 border border-primary-200 rounded-lg p-3">
            <p className="text-xs text-primary-600 font-medium mb-1">总体评估</p>
            <p className="text-sm text-surface-800 leading-relaxed">{syn.overall_assessment}</p>
          </div>
        )}
        {Array.isArray(syn.critical_fixes) && syn.critical_fixes.length > 0 && (
          <div>
            <p className="text-xs text-red-500 font-medium mb-1.5">⚠️ 必须修复</p>
            <ul className="space-y-1.5">{syn.critical_fixes.map((f: string, i: number) => (
              <li key={i} className="text-sm text-surface-700 bg-red-50/50 rounded-lg p-2 flex gap-2"><span className="text-red-400 shrink-0">{i+1}.</span><span>{f}</span></li>
            ))}</ul>
          </div>
        )}
        {Array.isArray(syn.recommended_improvements) && syn.recommended_improvements.length > 0 && (
          <div>
            <p className="text-xs text-blue-600 font-medium mb-1.5">💡 改进建议</p>
            <ul className="space-y-1.5">{syn.recommended_improvements.map((s: string, i: number) => (
              <li key={i} className="text-sm text-surface-700 bg-blue-50/50 rounded-lg p-2 flex gap-2"><span className="text-blue-400 shrink-0">{i+1}.</span><span>{s}</span></li>
            ))}</ul>
          </div>
        )}
        {syn.resume_revisions && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
            <p className="text-xs text-emerald-600 font-medium mb-1.5">✏️ 简历修改建议</p>
            {syn.resume_revisions.summary && (
              <div className="mb-2">
                <p className="text-xs text-surface-500 mb-0.5">建议简介</p>
                <p className="text-sm text-surface-800">{syn.resume_revisions.summary}</p>
              </div>
            )}
            {Array.isArray(syn.resume_revisions.key_additions) && syn.resume_revisions.key_additions.length > 0 && (
              <div className="mb-2">
                <p className="text-xs text-emerald-600 mb-0.5">需要增加</p>
                <ul className="space-y-1">{syn.resume_revisions.key_additions.map((a: string, i: number) => (
                  <li key={i} className="text-sm text-surface-700 flex gap-2"><span className="text-emerald-400 shrink-0">+</span><span>{a}</span></li>
                ))}</ul>
              </div>
            )}
            {Array.isArray(syn.resume_revisions.key_removals) && syn.resume_revisions.key_removals.length > 0 && (
              <div className="mb-2">
                <p className="text-xs text-red-500 mb-0.5">需要移除/弱化</p>
                <ul className="space-y-1">{syn.resume_revisions.key_removals.map((r: string, i: number) => (
                  <li key={i} className="text-sm text-surface-700 flex gap-2"><span className="text-red-400 shrink-0">−</span><span>{r}</span></li>
                ))}</ul>
              </div>
            )}
            {syn.resume_revisions.tone_adjustment && (
              <div>
                <p className="text-xs text-surface-500 mb-0.5">语调调整</p>
                <p className="text-sm text-surface-800">{syn.resume_revisions.tone_adjustment}</p>
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  const renderInterviewPlan = (plan: any) => {
    if (!plan || typeof plan === 'string') return <p className="text-sm text-surface-700 whitespace-pre-wrap">{plan || '无数据'}</p>
    return (
      <div className="space-y-2">
        {Array.isArray(plan.likely_questions) && plan.likely_questions.length > 0 && (
          <div>
            <p className="text-xs text-blue-600 font-medium mb-1">可能的面试问题</p>
            <ul className="space-y-1.5">{plan.likely_questions.map((q: string, i: number) => (
              <li key={i} className="text-sm text-surface-700 bg-blue-50/50 rounded-lg p-2 flex gap-2"><span className="text-blue-400 shrink-0">Q{i+1}.</span><span>{q}</span></li>
            ))}</ul>
          </div>
        )}
        {Array.isArray(plan.preparation_tips) && plan.preparation_tips.length > 0 && (
          <div>
            <p className="text-xs text-emerald-600 font-medium mb-1">准备建议</p>
            <ul className="space-y-1">{plan.preparation_tips.map((t: string, i: number) => (
              <li key={i} className="text-sm text-surface-700 flex gap-2"><span className="text-emerald-400 shrink-0">•</span><span>{t}</span></li>
            ))}</ul>
          </div>
        )}
      </div>
    )
  }

  const renderResults = () => {
    if (!details) return <div className="mt-3 text-sm text-surface-400">加载中...</div>

    const roles = [
      { key: 'hr_review', label: 'HR 视角', emoji: '👔' },
      { key: 'headhunter_review', label: '猎头视角', emoji: '🔍' },
      { key: 'interviewer_review', label: '面试官视角', emoji: '🎤' },
      { key: 'manager_review', label: '部门经理视角', emoji: '📋' },
      { key: 'expert_review', label: '行业专家视角', emoji: '🎓' },
    ]

    return (
      <div className="mt-4 pt-4 border-t border-surface-100 space-y-4">
        {details.synthesis && (
          <div>
            <p className="text-xs text-primary-600 font-semibold uppercase tracking-wider mb-2">综合分析</p>
            {renderSynthesis(details.synthesis)}
          </div>
        )}

        <div>
          <p className="text-xs text-surface-400 font-semibold uppercase tracking-wider mb-2">多角色评审</p>
          <div className="space-y-3">
            {roles.map(({ key, label, emoji }) => details[key] && (
              <details key={key} className="bg-surface-50 rounded-lg overflow-hidden">
                <summary className="px-3 py-2.5 cursor-pointer hover:bg-surface-100 transition-colors flex items-center gap-2">
                  <span>{emoji}</span>
                  <span className="text-sm font-medium text-surface-700">{label}</span>
                  {details[key].score_impact && (
                    <span className={`ml-auto px-1.5 py-0.5 rounded text-xs ${
                      details[key].score_impact === 'positive' ? 'bg-emerald-100 text-emerald-600' :
                      details[key].score_impact === 'negative' ? 'bg-red-100 text-red-600' :
                      'bg-surface-200 text-surface-500'
                    }`}>{details[key].score_impact === 'positive' ? '正面' : details[key].score_impact === 'negative' ? '负面' : '中性'}</span>
                  )}
                </summary>
                <div className="px-3 pb-3">
                  {renderRoleReview(details[key])}
                </div>
              </details>
            ))}
          </div>
        </div>

        {details.interview_plan && (
          <div>
            <p className="text-xs text-surface-400 font-semibold uppercase tracking-wider mb-2">面试沟通方案</p>
            <div className="bg-surface-50 rounded-lg p-3">
              {renderInterviewPlan(details.interview_plan)}
            </div>
          </div>
        )}

        {review.resume_type === 'targeted' && details.synthesis?.resume_revisions && onRegenerate && (
          <div className="pt-2 border-t border-surface-100">
            <button
              onClick={onRegenerate}
              disabled={regenerating}
              className="w-full px-4 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-500 transition-all font-medium text-sm disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {regenerating ? (
                <><Spinner className="w-4 h-4 border-white/50 border-t-white" /><span>正在基于评审重生成简历...</span></>
              ) : (
                <><span>✨</span><span>基于评审建议重生成定向简历</span></>
              )}
            </button>
            <p className="text-xs text-surface-400 mt-1.5 text-center">将根据评审的修改建议自动生成新版本定向简历</p>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="bg-surface-50 border border-surface-200 rounded-lg overflow-hidden">
      <div
        className="flex items-center justify-between cursor-pointer px-4 py-3 hover:bg-surface-100/50 transition-colors"
        onClick={() => {
          if (review.status === 'completed') {
            onToggle()
            if (!isExpanded) onFetchDetail()
          }
        }}
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className={`px-2 py-0.5 rounded text-xs flex items-center gap-1 shrink-0 ${st.color}`}>
            {st.spin && <Spinner className="w-3 h-3" />}
            {st.label}
          </span>
          <span className="text-sm text-surface-700 truncate">{formatDate(review.created_at)}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {onDelete && (
            <button
              onClick={(e) => { e.stopPropagation(); onDelete() }}
              className="px-2 py-1 text-xs text-surface-400 hover:text-red-500 hover:bg-red-50 rounded transition-all"
            >
              删除
            </button>
          )}
          {review.status === 'completed' && (
            <span className="text-xs text-surface-500">{isExpanded ? '收起 ▴' : '展开 ▾'}</span>
          )}
        </div>
      </div>

      {isExpanded && <div className="px-4 pb-4 border-t border-surface-200">{renderResults()}</div>}
    </div>
  )
})


export default function Resumes() {

  const [baseResume, setBaseResume] = useState<BaseResume | null>(null)
  const [targetedResumes, setTargetedResumes] = useState<TargetedResume[]>([])
  const [jds, setJds] = useState<JD[]>([])
  const [reviews, setReviews] = useState<Review[]>([])

  const [pageLoading, setPageLoading] = useState(true)
  const [generatingBase, setGeneratingBase] = useState(false)
  const [generatingTargeted, setGeneratingTargeted] = useState(false)
  const [creatingReview, setCreatingReview] = useState(false)
  const [regeneratingReviewId, setRegeneratingReviewId] = useState<string | null>(null)
  const [regeneratingResume, setRegeneratingResume] = useState(false)
  const [regenerateStage, setRegenerateStage] = useState(0)
  const [targetedStage, setTargetedStage] = useState(0)
  const [reviewStage, setReviewStage] = useState(0)

  const [editingBase, setEditingBase] = useState(false)
  const [baseContent, setBaseContent] = useState('')
  const [editingTargetedId, setEditingTargetedId] = useState<string | null>(null)
  const [targetedContent, setTargetedContent] = useState('')
  const [savingEdit, setSavingEdit] = useState(false)

  const [expandedReview, setExpandedReview] = useState<string | null>(null)
  const [expandedAdjReport, setExpandedAdjReport] = useState<string | null>(null)
  const [reviewDetails, setReviewDetails] = useState<Record<string, any>>({})
  const [confirmAction, setConfirmAction] = useState<{ message: string; onConfirm: () => void } | null>(null)
  const [previewData, setPreviewData] = useState<{ name: string; content: any } | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)

  const [renderForImage, setRenderForImage] = useState<{ id: string; content: any; name: string; jdTitle?: string } | null>(null)
  const imageRef = useRef<HTMLDivElement | null>(null)

  const [expandedJdId, setExpandedJdId] = useState<string | null>(null)
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null)
  const carouselRef = useRef<HTMLDivElement | null>(null)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)

  const jdMap = new Map(jds.map((j) => [j.id, j]))
  const basePollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const reviewsPollRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const jdGroups = useMemo(() => {
    const map = new Map<string, TargetedResume[]>()
    for (const r of targetedResumes) {
      const arr = map.get(r.jd_id) || []
      arr.push(r)
      map.set(r.jd_id, arr)
    }
    for (const [, arr] of map) {
      arr.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    }
    return Array.from(map.entries())
  }, [targetedResumes])

  const updateScrollButtons = useCallback(() => {
    const el = carouselRef.current
    if (!el) return
    setCanScrollLeft(el.scrollLeft > 4)
    setCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 4)
  }, [])

  const scrollCarousel = useCallback((direction: 'left' | 'right') => {
    carouselRef.current?.scrollBy({ left: direction === 'left' ? -380 : 380, behavior: 'smooth' })
  }, [])

  const fetchBase = useCallback(async () => {
    try {
      const res = await resumesApi.getBase()
      if (res.data?.exists) {
        const data = res.data
        const resume: BaseResume = {
          ...data,
          generation_status: data.generation_status || 'success',
          generation_error: data.generation_error || null,
          content: data.content ?? null,
        }
        setBaseResume(resume)
        return resume
      } else {
        setBaseResume(null)
        return null
      }
    } catch {
      setBaseResume(null)
      return null
    }
  }, [])

  const fetchTargeted = useCallback(async () => {
    try {
      const res = await resumesApi.listTargeted()
      const d = res.data
      setTargetedResumes(Array.isArray(d) ? d : d.items ?? [])
    } catch {
      toastError('加载定向简历失败')
    }
  }, [])

  const fetchReviews = useCallback(async () => {
    try {
      const res = await reviewsApi.list()
      const d = res.data
      setReviews(Array.isArray(d) ? d : d.items ?? [])
    } catch {
      toastError('加载评审列表失败')
    }
  }, [])

  const fetchJds = useCallback(async () => {
    try {
      const res = await jdsApi.list()
      const d = res.data
      setJds(Array.isArray(d) ? d : d.items ?? [])
    } catch {
      setJds([])
    }
  }, [])

  const fetchReviewDetail = async (id: string) => {
    if (reviewDetails[id]) return
    try {
      const res = await reviewsApi.get(id)
      setReviewDetails((prev) => ({ ...prev, [id]: res.data }))
    } catch {
      toastError('评审详情加载失败')
    }
  }

  useEffect(() => {
    ;(async () => {
      setPageLoading(true)
      await Promise.all([fetchBase(), fetchTargeted(), fetchReviews(), fetchJds()])
      setPageLoading(false)
    })()
  }, [fetchBase, fetchTargeted, fetchReviews, fetchJds])

  useEffect(() => {
    const hasAnalyzing = reviews.some((r) => r.status === 'pending' || r.status === 'running')

    if (hasAnalyzing) {
      const delays = [3000, 5000, 8000, 12000]
      let count = 0

      const schedule = () => {
        const delay = delays[Math.min(count, delays.length - 1)]
        reviewsPollRef.current = setTimeout(async () => {
          try {
            const res = await reviewsApi.list()
            const d = res.data
            const updated = Array.isArray(d) ? d : d.items ?? []
            count++
            setReviews(updated)
          } catch {
          }
        }, delay)
      }

      schedule()
    }

    return () => {
      if (reviewsPollRef.current) {
        clearTimeout(reviewsPollRef.current)
        reviewsPollRef.current = null
      }
    }
  }, [reviews])

  const targetedPollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    const hasGenerating = targetedResumes.some(
      (t) => t.generation_status === 'pending' || t.generation_status === 'generating'
    )
    if (hasGenerating) {
      targetedPollRef.current = setInterval(async () => {
        await fetchTargeted()
      }, 5000)
    } else {
      if (targetedPollRef.current) clearInterval(targetedPollRef.current)
    }
    return () => {
      if (targetedPollRef.current) clearInterval(targetedPollRef.current)
    }
  }, [targetedResumes, fetchTargeted])

  useEffect(() => {
    const isGenerating = baseResume?.generation_status === 'pending' || baseResume?.generation_status === 'generating'
    if (isGenerating) {
      basePollRef.current = setInterval(async () => {
        const updated = await fetchBase()
        if (updated && (updated.generation_status === 'success' || updated.generation_status === 'failed')) {
          if (basePollRef.current) clearInterval(basePollRef.current)
          if (updated.generation_status === 'success') {
            toastSuccess('底版简历生成完成')
          } else {
            toastError(updated.generation_error || '底版简历生成失败')
          }
        }
      }, 5000)
    } else {
      if (basePollRef.current) clearInterval(basePollRef.current)
    }
    return () => {
      if (basePollRef.current) clearInterval(basePollRef.current)
    }
  }, [baseResume?.generation_status, fetchBase])

  useEffect(() => {
    if (!renderForImage || !imageRef.current) return
    const node = imageRef.current
    const timer = setTimeout(async () => {
      try {
        const dataUrl = await toPng(node, {
          pixelRatio: 2,
          quality: 0.95,
          backgroundColor: '#ffffff',
        })
        const res = await fetch(dataUrl)
        const blob = await res.blob()
        downloadBlob(blob, `${renderForImage.name}.png`)
        toastSuccess('PNG 导出成功')
      } catch {
        toastError('图片导出失败')
      } finally {
        setRenderForImage(null)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [renderForImage])

  const handleExportPng = async (resumeId: string, _resumeName: string, jdTitle?: string) => {
    try {
      const res = await resumesApi.getTargeted(resumeId)
      const content = res.data.content
      const personalName = content?.personal_info?.name || ''
      const cleanName = personalName ? `${personalName}_${jdTitle || '简历'}` : (jdTitle || '简历')
      setRenderForImage({ id: resumeId, content, name: cleanName, jdTitle })
    } catch {
      toastError('加载简历内容失败')
    }
  }

  const handleGenerateBase = async () => {
    setGeneratingBase(true)
    try {
      await resumesApi.generateBase()
      await fetchBase()
      toastSuccess('底版简历生成已开始，预计需要30-60秒')
    } catch (error: any) {
      toastError(error.response?.data?.detail || '生成底版简历失败')
    } finally {
      setGeneratingBase(false)
    }
  }

  const handleSaveBase = async () => {
    setSavingEdit(true)
    try {
      JSON.parse(baseContent)
      await resumesApi.updateBase({ content: baseContent })
      await fetchBase()
      setEditingBase(false)
    } catch {
      toastError('保存失败，请检查 JSON 格式')
    } finally {
      setSavingEdit(false)
    }
  }

  const handleStartEditBase = () => {
    if (baseResume) {
      setBaseContent(JSON.stringify(baseResume.content, null, 2))
      setEditingBase(true)
    }
  }

  const handleGenerateTargeted = async (jdId: string) => {
    setGeneratingTargeted(true)
    setTargetedStage(0)

    const stageTimer = setInterval(() => {
      setTargetedStage(prev => Math.min(prev + 1, 2))
    }, 15000)

    try {
      const res = await resumesApi.generateTargeted({ jd_id: jdId })
      const newId = (res.data as any).id

      const pollGeneration = () => {
        const delay = 3000
        const tid = setTimeout(async () => {
          try {
            const checkRes = await resumesApi.getTargeted(newId)
            const status = checkRes.data.generation_status
            if (status === 'success') {
              clearInterval(stageTimer)
              setTargetedStage(2)
              await new Promise(r => setTimeout(r, 500))
              setGeneratingTargeted(false)
              setTargetedStage(0)
              await fetchTargeted()
              toastSuccess('定向简历生成完成')
            } else if (status === 'failed') {
              clearInterval(stageTimer)
              setGeneratingTargeted(false)
              setTargetedStage(0)
              toastError('生成失败: ' + (checkRes.data.generation_error || '请重试'))
              await fetchTargeted()
            } else {
              pollGeneration()
            }
          } catch {
            clearInterval(stageTimer)
            setGeneratingTargeted(false)
            setTargetedStage(0)
          }
        }, delay)
        return tid
      }
      pollGeneration()

      setTimeout(() => {
        clearInterval(stageTimer)
        setGeneratingTargeted(false)
        setTargetedStage(0)
      }, 300000)

    } catch (e: any) {
      clearInterval(stageTimer)
      toastError('生成定向简历失败: ' + (e?.response?.data?.detail || '请重试'))
      setGeneratingTargeted(false)
      setTargetedStage(0)
    }
  }

  const handleDeleteTargeted = async (id: string) => {
    setConfirmAction({
      message: '确定删除这份定向简历？删除后无法恢复。',
      onConfirm: async () => {
        setConfirmAction(null)
        try {
          await resumesApi.deleteTargeted(id)
          setTargetedResumes((prev) => prev.filter((r) => r.id !== id))
        } catch {
          toastError('删除失败')
        }
      },
    })
  }

  const handleStartEditTargeted = async (r: TargetedResume) => {
    setEditingTargetedId(r.id)
    try {
      const res = await resumesApi.getTargeted(r.id)
      setTargetedContent(JSON.stringify(res.data.content ?? {}, null, 2))
    } catch {
      toastError('加载简历内容失败')
      setEditingTargetedId(null)
    }
  }

  const handleSaveTargeted = async () => {
    if (!editingTargetedId) return
    setSavingEdit(true)
    try {
      JSON.parse(targetedContent)
      await resumesApi.updateTargeted(editingTargetedId, { content: targetedContent })
      await fetchTargeted()
      setEditingTargetedId(null)
    } catch {
      toastError('保存失败，请检查 JSON 格式')
    } finally {
      setSavingEdit(false)
    }
  }

  const handleCreateReview = async (resumeId: string, resumeType: 'base' | 'targeted') => {
    setCreatingReview(true)
    setReviewStage(0)

    const stageTimer = setInterval(() => {
      setReviewStage(prev => Math.min(prev + 1, 2))
    }, 10000)

    try {
      await reviewsApi.create({ resume_id: resumeId, resume_type: resumeType })
      clearInterval(stageTimer)
      await fetchReviews()
    } catch {
      clearInterval(stageTimer)
      toastError('发起评审失败')
    } finally {
      setCreatingReview(false)
      setReviewStage(0)
    }
  }

  const handleRegenerateFromReview = async (reviewId: string) => {
    setRegeneratingReviewId(reviewId)
    setRegeneratingResume(true)
    setRegenerateStage(0)

    const stageTimer = setInterval(() => {
      setRegenerateStage(prev => Math.min(prev + 1, 2))
    }, 15000)

    try {
      const res = await reviewsApi.regenerateResume(reviewId)
      clearInterval(stageTimer)
      setRegenerateStage(2)
      await new Promise(r => setTimeout(r, 500))
      toastSuccess(`已生成新版本定向简历: ${res.data.name || '定向简历'}`)
      await fetchTargeted()
    } catch {
      clearInterval(stageTimer)
      toastError('基于评审重生成失败')
    } finally {
      setRegeneratingReviewId(null)
      setRegeneratingResume(false)
      setRegenerateStage(0)
    }
  }

  const handleDeleteReview = async (reviewId: string) => {
    try {
      await reviewsApi.delete(reviewId)
      toastSuccess('评审已删除')
      setExpandedReview(null)
      await fetchReviews()
    } catch {
      toastError('删除评审失败')
    }
  }


  if (pageLoading) {
    return <PageLoader />
  }

  return (
    <div className="min-h-screen bg-surface-50">
      <AppHeader title="简历管理" activeNav="resumes" />

      <main className="max-w-5xl mx-auto p-4 sm:p-6 space-y-10">
        <section>
          <SectionHeading title="底版简历">
            <div className="flex items-center gap-2">
              {baseResume && baseResume.generation_status === 'success' && (
                <button
                  onClick={handleStartEditBase}
                  className="px-4 py-2 text-sm text-primary-400 hover:bg-primary-500/10 rounded-lg transition-all"
                >
                  编辑
                </button>
              )}
              <button
                onClick={handleGenerateBase}
                disabled={generatingBase || baseResume?.generation_status === 'generating' || baseResume?.generation_status === 'pending'}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 text-sm transition-all shadow-lg shadow-primary-600/20 disabled:opacity-50 flex items-center gap-2"
              >
                {generatingBase || baseResume?.generation_status === 'generating' || baseResume?.generation_status === 'pending' ? <Spinner /> : null}
                {baseResume?.generation_status === 'generating' || baseResume?.generation_status === 'pending' ? '生成中...' : baseResume ? '重新生成' : '生成底版简历'}
              </button>
            </div>
          </SectionHeading>

          {editingBase ? (
            <div className="bg-white border border-surface-200 rounded-xl p-5 space-y-3">
              <textarea
                value={baseContent}
                onChange={(e) => setBaseContent(e.target.value)}
                rows={20}
                className="w-full bg-surface-50 text-surface-700 text-sm font-mono p-4 rounded-lg border border-surface-200 focus:border-primary-500/50 focus:outline-none resize-y"
              />
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setEditingBase(false)}
                  className="px-4 py-2 text-sm text-surface-500 hover:text-surface-800 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleSaveBase}
                  disabled={savingEdit}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 text-sm transition-all shadow-sm shadow-primary-500/10 disabled:opacity-50 flex items-center gap-2"
                >
                  {savingEdit ? <Spinner /> : null}
                  保存
                </button>
              </div>
            </div>
          ) : baseResume?.generation_status === 'pending' || baseResume?.generation_status === 'generating' ? (
            <div className="bg-white border border-surface-200 rounded-xl p-5 text-center py-8">
              <Spinner className="w-5 h-5 mx-auto mb-2" />
              <p className="text-sm text-surface-500">简历生成中，请稍候...</p>
            </div>
          ) : baseResume?.generation_status === 'failed' ? (
            <div className="bg-white border border-surface-200 rounded-xl p-5 border border-red-500/20 text-center py-12">
              <div className="text-5xl mb-3">⚠️</div>
              <p className="text-red-400 font-medium mb-2">生成失败</p>
              <p className="text-surface-500 text-sm">{baseResume.generation_error || '请重试'}</p>
            </div>
          ) : baseResume?.generation_status === 'success' && baseResume.content ? (
            <BaseResumeCard content={baseResume.content} updatedAt={baseResume.updated_at} />
          ) : (
            <div className="bg-white border border-surface-200 rounded-xl p-5 text-center py-12">
              <div className="text-5xl mb-3">📄</div>
              <p className="text-surface-500">你还没有底版简历，请先上传并分析资料后生成</p>
            </div>
          )}
          {baseResume && baseResume.generation_status === 'success' && (
            <ReviewSection
              reviews={reviews.filter((r) => r.resume_type === 'base' && r.resume_id === baseResume.id)}
              expandedReview={expandedReview}
              reviewDetails={reviewDetails}
              onToggle={(id) => setExpandedReview(expandedReview === id ? null : id)}
              onFetchDetail={fetchReviewDetail}
              onCreateReview={() => handleCreateReview(baseResume.id, 'base')}
              creatingReview={creatingReview}
              onRegenerate={handleRegenerateFromReview}
              regeneratingReviewId={regeneratingReviewId}
              onDelete={handleDeleteReview}
              emptyText="对底版简历发起 AI 多角色评审"
            />
          )}
        </section>

        <section className="-mx-4 sm:-mx-6 px-4 sm:px-6 py-8 bg-surface-100/60 border-t border-surface-200">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h2 className="text-lg font-semibold text-surface-900">定向简历</h2>
                <p className="text-xs text-surface-400 mt-0.5">针对目标岗位 AI 优化的简历版本</p>
              </div>
              <Dropdown
                items={jds.map((j) => ({ id: j.id, label: j.title, sublabel: j.company ?? undefined }))}
                placeholder={generatingTargeted ? '生成中...' : '生成定向简历'}
                onSelect={handleGenerateTargeted}
                disabled={generatingTargeted}
              />
            </div>

          {targetedResumes.length === 0 ? (
            <div className="bg-white border border-surface-200 rounded-xl p-5 text-center py-12">
              <div className="text-5xl mb-3">🎯</div>
              <p className="text-surface-500">还没有定向简历，选择 JD 生成你的第一份</p>
            </div>
          ) : expandedJdId ? (
            (() => {
              const group = jdGroups.find(([jid]) => jid === expandedJdId)
              if (!group) return null
              const [jdId, versions] = group
              const jd = jdMap.get(jdId)
              const selectedVersion = versions.find((v) => v.id === selectedVersionId) || versions[0]
              if (!selectedVersion) return null
              const latestVersion = versions[0]
              const latestGrade = latestVersion.grade || null
              const gradeStyle = latestGrade ? GRADE_STYLES[latestGrade] ?? '' : ''
              return (
                <div className="bg-white border border-surface-200 rounded-xl">
                  <div className="px-5 pt-5 pb-4 border-b border-surface-100">
                    <div className="flex items-center justify-between gap-3">
                      <button
                        onClick={() => { setExpandedJdId(null); setSelectedVersionId(null) }}
                        className="flex items-center gap-1.5 text-sm text-surface-500 hover:text-surface-800 transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
                        返回列表
                      </button>
                      <div className="flex items-center gap-2">
                        {latestGrade && (
                          <span className={`px-2.5 py-1 rounded text-xs font-semibold ${gradeStyle}`}>
                            {latestGrade}
                          </span>
                        )}
                      </div>
                    </div>
                    <h3 className="text-lg font-semibold text-surface-900 mt-3 line-clamp-2">{jd ? jd.title : '未知 JD'}</h3>
                    {jd?.company && <p className="text-sm text-surface-500 mt-0.5">{jd.company}</p>}
                  </div>

                  {versions.length > 1 && (
                    <div className="px-5 py-3 border-b border-surface-100 flex items-center gap-2 overflow-x-auto">
                      {versions.map((v, i) => (
                        <button
                          key={v.id}
                          onClick={() => setSelectedVersionId(v.id)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
                            selectedVersion.id === v.id
                              ? 'bg-primary-600 text-white shadow-sm shadow-primary-500/10'
                              : 'bg-surface-100 text-surface-600 hover:bg-surface-200'
                          }`}
                        >
                          v{versions.length - i}{v.id === latestVersion.id ? ' (最新)' : ''}
                        </button>
                      ))}
                    </div>
                  )}

                  <div className="p-5">
                    {editingTargetedId === selectedVersion.id ? (
                      <div className="space-y-3">
                        <textarea
                          value={targetedContent}
                          onChange={(e) => setTargetedContent(e.target.value)}
                          rows={16}
                          className="w-full bg-surface-50 text-surface-700 text-sm font-mono p-4 rounded-lg border border-surface-200 focus:border-primary-500/50 focus:outline-none resize-y"
                        />
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => setEditingTargetedId(null)}
                            className="px-4 py-2 text-sm text-surface-500 hover:text-surface-800 transition-colors"
                          >
                            取消
                          </button>
                          <button
                            onClick={handleSaveTargeted}
                            disabled={savingEdit}
                            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 text-sm transition-all shadow-sm shadow-primary-500/10 disabled:opacity-50 flex items-center gap-2"
                          >
                            {savingEdit ? <Spinner /> : null}
                            保存
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        {selectedVersion.recommendation && (
                          <div className="bg-primary-50/50 border-l-2 border-primary-400 rounded-r-lg px-4 py-3 mb-4">
                            <p className="text-xs text-primary-600 font-medium mb-1">AI 推荐</p>
                            <p className="text-sm text-surface-700 leading-relaxed">{selectedVersion.recommendation}</p>
                          </div>
                        )}

                        {selectedVersion.adjustment_report && (
                          <div className="mb-4">
                            <button
                              onClick={() => setExpandedAdjReport(expandedAdjReport === selectedVersion.id ? null : selectedVersion.id)}
                              className="w-full flex items-center justify-between text-left"
                            >
                              <p className="text-xs text-primary-600 font-medium uppercase tracking-wider">调整说明</p>
                              <span className="text-xs text-surface-400">{expandedAdjReport === selectedVersion.id ? '收起 ▴' : '展开 ▾'}</span>
                            </button>
                            {expandedAdjReport === selectedVersion.id && (
                              <div className="mt-3">
                                <p className="text-sm text-surface-700 mb-3">{selectedVersion.adjustment_report.summary}</p>
                                {selectedVersion.adjustment_report.adjustments?.length > 0 && (
                                  <div className="space-y-2">
                                    {selectedVersion.adjustment_report.adjustments.map((adj, i) => (
                                      <div key={i} className="bg-surface-50 rounded-lg p-3">
                                        <div className="flex items-center gap-2 mb-1">
                                          <span className="px-1.5 py-0.5 rounded text-xs bg-primary-500/10 text-primary-600 font-medium">{adj.area}</span>
                                        </div>
                                        <p className="text-sm text-surface-800">{adj.action}</p>
                                        <p className="text-xs text-surface-500 mt-1">{adj.reason}</p>
                                        {adj.emphasis && (
                                          <p className="text-xs text-amber-600/80 mt-1">⚡ {adj.emphasis}</p>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                )}
                                {selectedVersion.adjustment_report.packaging && (
                                  <div className="mt-3 bg-blue-50/50 rounded-lg p-3 border border-blue-100">
                                    <p className="text-xs text-blue-600 font-medium mb-1">包装策略</p>
                                    <p className="text-sm text-surface-700">{selectedVersion.adjustment_report.packaging}</p>
                                  </div>
                                )}
                                {selectedVersion.adjustment_report.risk_note && (
                                  <div className="mt-2 bg-amber-50/50 rounded-lg p-3 border border-amber-100">
                                    <p className="text-xs text-amber-600 font-medium mb-1">风险提示</p>
                                    <p className="text-sm text-surface-700">{selectedVersion.adjustment_report.risk_note}</p>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}

                        <div className="flex items-center gap-1 flex-wrap mb-4">
                          <button
                            onClick={async () => {
                              setPreviewLoading(true)
                              try {
                                const res = await resumesApi.getTargeted(selectedVersion.id)
                                setPreviewData({ name: selectedVersion.name || '定向简历', content: res.data.content })
                              } catch {
                                toastError('加载简历内容失败')
                              } finally {
                                setPreviewLoading(false)
                              }
                            }}
                            className="px-4 py-2 text-sm text-primary-600 hover:bg-primary-50 rounded-lg transition-all"
                          >
                            预览
                          </button>
                          <button
                            onClick={() => handleStartEditTargeted(selectedVersion)}
                            className="px-4 py-2 text-sm text-primary-600 hover:bg-primary-50 rounded-lg transition-all"
                          >
                            编辑
                          </button>
                          <ExportMenu onResumeId={selectedVersion.id} onResumeName={selectedVersion.name || '简历'} onExportPng={() => handleExportPng(selectedVersion.id, selectedVersion.name || '简历', jd?.title)} />
                          <button
                            onClick={() => handleDeleteTargeted(selectedVersion.id)}
                            className="px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
                          >
                            删除
                          </button>
                        </div>

                        <p className="text-xs text-surface-300">
                          版本 v{versions.length - versions.findIndex((v) => v.id === selectedVersion.id)} · {formatDate(selectedVersion.created_at)}
                        </p>
                      </>
                    )}
                  </div>

                  {selectedVersion.generation_status === 'success' && (
                    <div className="px-5 pb-5 border-t border-surface-100 pt-4">
                      <ReviewSection
                        reviews={reviews.filter((rv) => rv.resume_type === 'targeted' && rv.resume_id === selectedVersion.id)}
                        expandedReview={expandedReview}
                        reviewDetails={reviewDetails}
                        onToggle={(id) => setExpandedReview(expandedReview === id ? null : id)}
                        onFetchDetail={fetchReviewDetail}
                        onCreateReview={() => handleCreateReview(selectedVersion.id, 'targeted')}
                        creatingReview={creatingReview}
                        onRegenerate={handleRegenerateFromReview}
                        regeneratingReviewId={regeneratingReviewId}
                        onDelete={handleDeleteReview}
                        emptyText="对此定向简历发起 AI 评审"
                      />
                    </div>
                  )}
                </div>
              )
            })()
          ) : (
            <div className="relative">
              {canScrollLeft && (
                <button
                  onClick={() => scrollCarousel('left')}
                  className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-9 h-9 rounded-full bg-white/80 backdrop-blur-sm shadow-md border border-surface-200 flex items-center justify-center hover:bg-white transition-all -ml-1"
                >
                  <svg className="w-4 h-4 text-surface-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
                </button>
              )}
              {canScrollRight && (
                <button
                  onClick={() => scrollCarousel('right')}
                  className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-9 h-9 rounded-full bg-white/80 backdrop-blur-sm shadow-md border border-surface-200 flex items-center justify-center hover:bg-white transition-all -mr-1"
                >
                  <svg className="w-4 h-4 text-surface-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" /></svg>
                </button>
              )}

              <div
                ref={carouselRef}
                onScroll={updateScrollButtons}
                className="flex gap-4 overflow-x-auto scroll-smooth snap-x snap-mandatory pb-2 px-1 [&::-webkit-scrollbar]:hidden"
                style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
              >
                {jdGroups.map(([jdId, versions]) => {
                  const jd = jdMap.get(jdId)
                  const latest = versions[0]
                  const grade = latest.grade || null
                  const gradeStyle = grade ? GRADE_STYLES[grade] ?? '' : ''
                  const isGenerating = latest.generation_status === 'pending' || latest.generation_status === 'generating'
                  return (
                    <div
                      key={jdId}
                      className="snap-start shrink-0 min-w-[320px] max-w-[380px] sm:min-w-[360px] sm:max-w-[420px] bg-white border border-surface-200 rounded-xl p-4 hover:border-primary-200 hover:shadow-md transition-all duration-200 flex flex-col"
                      style={{ height: 'fit-content', minHeight: '220px' }}
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div className="min-w-0 flex-1">
                          <h4 className="font-medium text-surface-900 text-sm line-clamp-2 leading-snug">
                            {jd ? jd.title : '未知 JD'}
                          </h4>
                          {jd?.company && (
                            <p className="text-xs text-surface-400 mt-0.5 truncate">{jd.company}</p>
                          )}
                        </div>
                        {grade && (
                          <span className={`px-2 py-0.5 rounded text-xs font-semibold shrink-0 ${gradeStyle}`}>
                            {grade}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-0.5 rounded text-xs bg-surface-100 text-surface-500 font-medium">
                          v{latest.version || versions.length}
                        </span>
                        <span className="text-xs text-surface-300">{formatDate(latest.created_at)}</span>
                        {versions.length > 1 && (
                          <span className="text-xs text-surface-400">共 {versions.length} 个版本</span>
                        )}
                      </div>

                      {latest.recommendation && (
                        <p className="text-xs text-surface-500 line-clamp-2 mb-3 flex-1">
                          {latest.recommendation}
                        </p>
                      )}
                      {!latest.recommendation && <div className="flex-1" />}

                      {isGenerating && (
                        <div className="flex items-center gap-2 mb-3 text-xs text-primary-600">
                          <Spinner className="w-3.5 h-3.5" />
                          <span>生成中...</span>
                        </div>
                      )}

                      <div className="flex items-center gap-1 border-t border-surface-100 pt-3">
                        {latest.generation_status === 'success' && (
                          <button
                            onClick={async () => {
                              setPreviewLoading(true)
                              try {
                                const res = await resumesApi.getTargeted(latest.id)
                                setPreviewData({ name: latest.name || '定向简历', content: res.data.content })
                              } catch {
                                toastError('加载简历内容失败')
                              } finally {
                                setPreviewLoading(false)
                              }
                            }}
                            className="px-3 py-1.5 text-xs text-primary-600 hover:bg-primary-50 rounded-lg transition-all"
                          >
                            预览
                          </button>
                        )}
                        <button
                          onClick={() => {
                            setExpandedJdId(jdId)
                            setSelectedVersionId(latest.id)
                          }}
                          className="ml-auto px-3 py-1.5 text-xs text-surface-500 hover:bg-surface-50 rounded-lg transition-all flex items-center gap-1"
                        >
                          展开详情
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
          </div>
        </section>

      </main>

      {(baseResume?.generation_status === 'pending' || baseResume?.generation_status === 'generating') && (
        <GeneratingOverlay
          title="正在生成底版简历"
          subtitle="AI 正在分析你的资料并构建简历"
          stage={baseResume?.generation_status === 'generating' ? 1 : 0}
          stages={[
            { label: '分析资料', desc: '提取工作经历、技能、项目等关键信息' },
            { label: '生成简历', desc: '组织内容并优化表达方式' },
            { label: '格式校验', desc: '确保简历结构完整、内容准确' },
          ]}
        />
      )}

      {generatingTargeted && (
        <GeneratingOverlay
          title="正在生成定向简历"
          subtitle="AI 正在针对目标岗位优化你的简历"
          stage={targetedStage}
          stages={[
            { label: '分析岗位要求', desc: '提取JD中的关键技能和经验要求' },
            { label: '优化简历内容', desc: '调整经历和技能匹配目标岗位' },
            { label: '匹配度评估', desc: '评估简历与岗位的匹配程度' },
          ]}
        />
      )}

      {creatingReview && (
        <GeneratingOverlay
          title="正在发起简历评审"
          subtitle="5位 AI 角色将从不同角度评审你的简历"
          stage={reviewStage}
          stages={[
            { label: '初始化评审', desc: '准备简历内容和评审框架' },
            { label: '多角色分析', desc: 'HR、猎头、面试官、经理、专家分别评审' },
            { label: '综合诊断', desc: '汇总分析结果并给出优化建议' },
          ]}
        />
      )}

      {regeneratingResume && (
        <GeneratingOverlay
          title="正在基于评审优化简历"
          subtitle="AI 正在根据评审建议重新生成更优的定向简历"
          stage={regenerateStage}
          stages={[
            { label: '分析评审建议', desc: '提取关键修改意见和优化方向' },
            { label: '重写简历内容', desc: '按评审建议调整简介、经历和技能' },
            { label: '生成优化版本', desc: '生成新版本定向简历并对比变更' },
          ]}
        />
      )}

      <ConfirmDialog open={!!confirmAction} message={confirmAction?.message || ''} onConfirm={confirmAction?.onConfirm || (() => {})} onCancel={() => setConfirmAction(null)} />

      {previewLoading && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl p-8 flex items-center gap-3 shadow-xl">
            <Spinner className="w-5 h-5" />
            <span className="text-surface-600">加载简历内容...</span>
          </div>
        </div>
      )}

      {previewData && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setPreviewData(null)}>
          <div className="bg-white rounded-xl p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-surface-900">{previewData.name}</h2>
              <button onClick={() => setPreviewData(null)} className="text-surface-400 hover:text-surface-600 text-xl">&times;</button>
            </div>
            {(() => {
              const c = previewData.content
              if (!c) return <p className="text-surface-400">暂无内容</p>
              const summary = c.summary || ''
              const experience = Array.isArray(c.experience) ? c.experience : []
              const projects = Array.isArray(c.projects) ? c.projects : []
              const skills = Array.isArray(c.skills) ? c.skills : []
              const education = Array.isArray(c.education) ? c.education : []
              return (
                <div className="space-y-4 text-sm">
                  {summary && (
                    <div className="bg-primary-50/50 border-l-2 border-primary-400 rounded-r-lg px-4 py-3">
                      <p className="text-surface-700 leading-relaxed">{summary}</p>
                    </div>
                  )}
                  {experience.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">工作经历</h4>
                      <div className="space-y-2">
                        {experience.map((exp: any, i: number) => (
                          <div key={i} className="bg-surface-50 rounded-lg p-3">
                            <div className="flex justify-between gap-2">
                              <span className="font-medium text-surface-900">{exp.position}{exp.department ? ` · ${exp.department}` : ''}</span>
                              {exp.period && <span className="text-xs text-surface-400 shrink-0">{exp.period}</span>}
                            </div>
                            <div className="text-surface-500 text-xs">{exp.company}</div>
                            {exp.highlights?.length > 0 && (
                              <ul className="mt-1 space-y-0.5">
                                {exp.highlights.map((h: string, j: number) => (
                                  <li key={j} className="text-primary-700 text-xs pl-3 relative before:content-['★'] before:absolute before:left-0 before:text-primary-400">{h}</li>
                                ))}
                              </ul>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {projects.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">项目经历</h4>
                      <div className="space-y-2">
                        {projects.map((p: any, i: number) => (
                          <div key={i} className="bg-surface-50 rounded-lg p-3 border-l-2 border-blue-400">
                            <div className="flex justify-between gap-2">
                              <span className="font-medium text-surface-900">{p.name}</span>
                              {(p.start_date || p.end_date) && <span className="text-xs text-surface-400 shrink-0">{p.start_date}{p.start_date && p.end_date ? ' - ' : ''}{p.end_date}</span>}
                            </div>
                            {p.role && <div className="text-surface-500 text-xs">{p.role}</div>}
                            {p.description && <p className="text-surface-600 text-xs mt-1">{p.description}</p>}
                            {(p.situation || p.task || p.action || p.result) && (
                              <div className="mt-1 space-y-0.5 text-xs">
                                {p.situation && <p><span className="text-surface-400">背景:</span> <span className="text-surface-600">{p.situation}</span></p>}
                                {p.task && <p><span className="text-surface-400">任务:</span> <span className="text-surface-600">{p.task}</span></p>}
                                {p.action && <p><span className="text-surface-400">行动:</span> <span className="text-surface-600">{p.action}</span></p>}
                                {p.result && <p><span className="text-surface-400">成果:</span> <span className="text-surface-600">{p.result}</span></p>}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {skills.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">技能</h4>
                      <div className="flex flex-wrap gap-1.5">
                        {skills.map((s: any, i: number) => (
                          <span key={i} className="px-2 py-0.5 bg-primary-50 text-primary-700 rounded text-xs border border-primary-100">{typeof s === 'string' ? s : JSON.stringify(s)}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {education.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">教育经历</h4>
                      {education.map((e: any, i: number) => (
                        <div key={i} className="text-surface-700">
                          <span className="font-medium">{e.school}</span>
                          {e.major && <span className="text-surface-500"> · {e.major}</span>}
                          {e.degree && <span className="text-surface-400 text-xs"> ({e.degree})</span>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })()}
          </div>
        </div>
      )}

      {renderForImage && (
        <div style={{ position: 'fixed', left: '-9999px', top: 0, zIndex: -1 }}>
          <ResumeImageRenderer
            ref={imageRef}
            content={renderForImage.content}
            name={renderForImage.name}
            jdTitle={renderForImage.jdTitle}
          />
        </div>
      )}
    </div>
  )
}
