import { useEffect, useState, useCallback } from 'react'
import { jdsApi } from '../api/client'
import { toastError } from '../stores/toastStore'
import AppHeader from '../components/AppHeader'
import ConfirmDialog from '../components/ConfirmDialog'
import { PageLoader, PageError } from '../components/PageState'
import { formatDate } from '../utils/format'
import type { JD } from '../types'

function getJdParseStatus(jd: JD): 'pending' | 'done' {
  return jd.is_parsed ? 'done' : 'pending'
}

const STATUS_LABELS: Record<string, { text: string; color: string }> = {
  pending: { text: '待解析', color: 'bg-surface-100 text-surface-500 border border-surface-200' },
  done: { text: '已解析', color: 'bg-emerald-50 text-emerald-600 border border-emerald-200' },
}

interface EditFields {
  title: string
  company: string
  jd_text: string
}

export default function JDs() {
  const [jds, setJds] = useState<JD[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const [showForm, setShowForm] = useState(false)
  const [formTitle, setFormTitle] = useState('')
  const [formCompany, setFormCompany] = useState('')
  const [formJdText, setFormJdText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editFields, setEditFields] = useState<EditFields>({ title: '', company: '', jd_text: '' })
  const [savingEdit, setSavingEdit] = useState(false)

  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const [confirmAction, setConfirmAction] = useState<{ message: string; onConfirm: () => void } | null>(null)

  const fetchJDs = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      const response = await jdsApi.list()
      const data = response.data
      setJds(Array.isArray(data) ? data : data.items || [])
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchJDs()
  }, [fetchJDs])

  const handleCreate = async () => {
    if (!formTitle.trim()) {
      toastError('请填写岗位标题')
      return
    }
    if (!formJdText.trim() || formJdText.trim().length < 50) {
      toastError('岗位描述至少需要 50 个字符')
      return
    }
    setSubmitting(true)
    try {
      await jdsApi.create({
        title: formTitle.trim(),
        company: formCompany.trim(),
        jd_text: formJdText.trim(),
      })
      setFormTitle('')
      setFormCompany('')
      setFormJdText('')
      setShowForm(false)
      fetchJDs()
    } catch {
      toastError('创建失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: string) => {
    setConfirmAction({
      message: '确定删除这个岗位描述？删除后无法恢复。',
      onConfirm: async () => {
        setConfirmAction(null)
        try {
          await jdsApi.delete(id)
          setJds((prev) => prev.filter((jd) => jd.id !== id))
        } catch {
          toastError('删除失败')
        }
      },
    })
  }

  const handleParse = async (id: string) => {
    try {
      const res = await jdsApi.parse(id)
      setJds((prev) =>
        prev.map((jd) => jd.id === id ? {
          ...jd,
          is_parsed: res.data.is_parsed,
          parsed_data: res.data.parsed_data,
        } : jd)
      )
    } catch {
      toastError('解析失败')
    }
  }

  const startEditing = (jd: JD) => {
    setEditingId(jd.id)
    setEditFields({
      title: jd.title,
      company: jd.company || '',
      jd_text: jd.jd_text,
    })
  }

  const cancelEditing = () => {
    setEditingId(null)
    setEditFields({ title: '', company: '', jd_text: '' })
  }

  const saveEditing = async (id: string) => {
    if (!editFields.title.trim()) {
      toastError('岗位标题不能为空')
      return
    }
    if (!editFields.jd_text.trim() || editFields.jd_text.trim().length < 50) {
      toastError('岗位描述至少需要 50 个字符')
      return
    }
    setSavingEdit(true)
    try {
      await jdsApi.update(id, {
        title: editFields.title.trim(),
        company: editFields.company.trim(),
        jd_text: editFields.jd_text.trim(),
      })
      setJds((prev) =>
        prev.map((jd) =>
          jd.id === id
            ? {
                ...jd,
                title: editFields.title.trim(),
                company: editFields.company.trim() || null,
                jd_text: editFields.jd_text.trim(),
              }
            : jd
        )
      )
      setEditingId(null)
    } catch {
      toastError('保存失败')
    } finally {
      setSavingEdit(false)
    }
  }

  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  if (loading) {
    return <PageLoader />
  }

  if (error) {
    return <PageError title="岗位管理" activeNav="jds" message="无法加载岗位列表，请检查网络连接后重试" onRetry={fetchJDs} />
  }

  return (
    <div className="min-h-screen bg-surface-50">
      <AppHeader
        title="岗位管理"
        activeNav="jds"
        actions={
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 text-sm transition-all shadow-sm shadow-primary-500/10"
          >
            + 添加岗位
          </button>
        }
      />

      <main className="max-w-5xl mx-auto p-4 sm:p-6">
        {/* Add form */}
        {showForm && (          <div className="bg-white border border-surface-200 rounded-xl p-5 mb-6">
            <h2 className="text-sm font-medium text-surface-900 mb-4">添加新岗位</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-surface-500 mb-1">
                    岗位标题 <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                    className="w-full bg-white border border-surface-200 rounded-lg px-3 py-2 text-surface-900 placeholder:text-surface-400 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
                    placeholder="e.g. 高级前端工程师"
                  />
                </div>
                <div>
                  <label className="block text-sm text-surface-500 mb-1">公司</label>
                  <input
                    type="text"
                    value={formCompany}
                    onChange={(e) => setFormCompany(e.target.value)}
                    className="w-full bg-white border border-surface-200 rounded-lg px-3 py-2 text-surface-900 placeholder:text-surface-400 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
                    placeholder="e.g. 字节跳动"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm text-surface-500 mb-1">
                  岗位描述 <span className="text-red-400">*</span>
                  <span className="text-surface-400 ml-2">（至少 50 个字符）</span>
                </label>
                <textarea
                  value={formJdText}
                  onChange={(e) => setFormJdText(e.target.value)}
                  rows={6}
                  className="w-full bg-white border border-surface-200 rounded-lg px-3 py-2 text-surface-900 placeholder:text-surface-400 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none resize-none"
                  placeholder="粘贴完整的岗位描述..."
                />
              </div>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => {
                    setShowForm(false)
                    setFormTitle('')
                    setFormCompany('')
                    setFormJdText('')
                  }}
                  className="px-4 py-2 text-sm text-surface-500 hover:text-surface-700 hover:bg-surface-50 rounded-lg transition-all"
                >
                  取消
                </button>
                <button
                  onClick={handleCreate}
                  disabled={submitting}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 text-sm transition-all shadow-sm shadow-primary-500/10 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? '提交中...' : '确定'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Empty state */}
        {jds.length === 0 && !showForm ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">&#x1F4C4;</div>
            <h2 className="text-lg font-semibold text-surface-900 mb-2">
              还没有添加岗位描述
            </h2>
            <p className="text-surface-400 mb-6">
              添加感兴趣的岗位，AI 将为你解析关键信息
            </p>
            <button
              onClick={() => setShowForm(true)}
              className="px-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-500 transition-all shadow-sm shadow-primary-500/10"
            >
              添加第一个岗位
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {jds.map((jd) => {
              const status = STATUS_LABELS[getJdParseStatus(jd)] || STATUS_LABELS.pending
              const isEditing = editingId === jd.id
              const isExpanded = expandedIds.has(jd.id)
              const truncatedText =
                jd.jd_text.length > 150 ? jd.jd_text.slice(0, 150) + '...' : jd.jd_text

              return (
                <div
                  key={jd.id}
                  className="bg-white border border-surface-200 rounded-xl p-5 hover:border-surface-300 transition-all duration-200 group"
                >
                  {isEditing ? (
                    /* ---- Inline edit mode ---- */
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm text-surface-500 mb-1">岗位标题</label>
                          <input
                            type="text"
                            value={editFields.title}
                            onChange={(e) =>
                              setEditFields((prev) => ({ ...prev, title: e.target.value }))
                            }
                            className="w-full bg-white border border-surface-200 rounded-lg px-3 py-2 text-surface-900 placeholder:text-surface-400 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
                          />
                        </div>
                        <div>
                          <label className="block text-sm text-surface-500 mb-1">公司</label>
                          <input
                            type="text"
                            value={editFields.company}
                            onChange={(e) =>
                              setEditFields((prev) => ({ ...prev, company: e.target.value }))
                            }
                            className="w-full bg-white border border-surface-200 rounded-lg px-3 py-2 text-surface-900 placeholder:text-surface-400 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none"
                            placeholder="可选"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm text-surface-500 mb-1">
                          岗位描述 <span className="text-surface-400">（至少 50 个字符）</span>
                        </label>
                        <textarea
                          value={editFields.jd_text}
                          onChange={(e) =>
                            setEditFields((prev) => ({ ...prev, jd_text: e.target.value }))
                          }
                          rows={5}
                          className="w-full bg-white border border-surface-200 rounded-lg px-3 py-2 text-surface-900 placeholder:text-surface-400 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none resize-none"
                        />
                      </div>
                      <div className="flex gap-3 justify-end">
                        <button
                          onClick={cancelEditing}
                          className="px-4 py-2 text-sm text-surface-500 hover:text-surface-700 hover:bg-surface-50 rounded-lg transition-all"
                        >
                          取消
                        </button>
                        <button
                          onClick={() => saveEditing(jd.id)}
                          disabled={savingEdit}
                          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 text-sm transition-all shadow-sm shadow-primary-500/10 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {savingEdit ? '保存中...' : '保存'}
                        </button>
                      </div>
                    </div>
                  ) : (
                    /* ---- View mode ---- */
                    <>
                       <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 flex-wrap">
                            <h3 className="font-medium text-surface-900 group-hover:text-primary-500 transition-colors truncate">
                              {jd.title}
                            </h3>
                            {jd.company && (
                              <span className="bg-surface-100 text-surface-600 px-2 py-0.5 rounded text-xs truncate max-w-[200px] inline-block align-middle">
                                {jd.company}
                              </span>
                            )}
                            <span className={`px-2 py-0.5 rounded text-xs ${status.color}`}>
                              {status.text}
                            </span>
                          </div>
                          <p className="text-sm text-surface-400 mt-1">
                            创建于 {formatDate(jd.created_at)}
                          </p>
                          <p className="text-sm text-surface-500 mt-2 line-clamp-2">
                            {truncatedText}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 ml-4 shrink-0 flex-wrap">
                          {!jd.is_parsed && (
                            <button
                              onClick={() => handleParse(jd.id)}
                              className="px-4 py-2 text-sm text-primary-600 hover:bg-primary-50 rounded-lg transition-all"
                            >
                              解析
                            </button>
                          )}
                          {jd.is_parsed && (
                            <button
                              onClick={() => toggleExpanded(jd.id)}
                              className="px-4 py-2 text-sm text-primary-600 hover:bg-primary-50 rounded-lg transition-all"
                            >
                              {isExpanded ? '收起解析' : '查看解析'}
                            </button>
                          )}
                          <button
                            onClick={() => startEditing(jd)}
                            className="px-4 py-2 text-sm text-surface-500 hover:text-surface-700 hover:bg-surface-50 rounded-lg transition-all"
                          >
                            编辑
                          </button>
                          <button
                            onClick={() => handleDelete(jd.id)}
                            className="px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
                          >
                            删除
                          </button>
                        </div>
                      </div>

                      {/* Parsed data — structured card layout */}
                      {jd.is_parsed && isExpanded && jd.parsed_data && (() => {
                        const d = typeof jd.parsed_data === 'string' ? JSON.parse(jd.parsed_data) : jd.parsed_data
                        const seniorityLabels: Record<string, string> = { junior: '初级', mid: '中级', senior: '高级', staff: '专家' }

                        return (
                          <div className="mt-4 pt-4 border-t border-surface-100 space-y-5">
                            {/* 岗位概括 */}
                            {d.role_summary && (
                              <div className="bg-primary-50/50 border border-primary-100 rounded-lg p-4">
                                <p className="text-sm text-surface-700 leading-relaxed">{d.role_summary}</p>
                              </div>
                            )}

                            {/* 三列信息卡 */}
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                              {d.seniority_level && (
                                <div className="bg-surface-50 rounded-lg p-3 text-center">
                                  <p className="text-xs text-surface-400 mb-1">层级</p>
                                  <p className="text-sm font-medium text-surface-900">{seniorityLabels[d.seniority_level] || d.seniority_level}</p>
                                </div>
                              )}
                              {d.experience_years && (
                                <div className="bg-surface-50 rounded-lg p-3 text-center">
                                  <p className="text-xs text-surface-400 mb-1">经验要求</p>
                                  <p className="text-sm font-medium text-surface-900">{d.experience_years}</p>
                                </div>
                              )}
                              {d.education_requirements && (
                                <div className="bg-surface-50 rounded-lg p-3 text-center">
                                  <p className="text-xs text-surface-400 mb-1">学历</p>
                                  <p className="text-sm font-medium text-surface-900">{d.education_requirements}</p>
                                </div>
                              )}
                            </div>

                            {/* 人才侧重 */}
                            {d.talent_focus && (
                              <div>
                                <p className="text-xs font-medium text-surface-400 uppercase tracking-wider mb-1.5">🎯 人才侧重</p>
                                <p className="text-sm text-surface-700 leading-relaxed">{d.talent_focus}</p>
                              </div>
                            )}

                            {/* 薪资洞察 */}
                            {d.salary_insight && (
                              <div>
                                <p className="text-xs font-medium text-surface-400 uppercase tracking-wider mb-1.5">💰 薪资洞察</p>
                                <p className="text-sm text-surface-700 leading-relaxed">{d.salary_insight}</p>
                              </div>
                            )}

                            {/* 发展路径 */}
                            {d.career_growth && (
                              <div>
                                <p className="text-xs font-medium text-surface-400 uppercase tracking-wider mb-1.5">📈 发展路径</p>
                                <p className="text-sm text-surface-700 leading-relaxed">{d.career_growth}</p>
                              </div>
                            )}

                            {/* 特殊门槛 */}
                            {d.special_barriers && d.special_barriers.length > 0 && (
                              <div>
                                <p className="text-xs font-medium text-surface-400 uppercase tracking-wider mb-1.5">🚧 特殊门槛</p>
                                <div className="flex flex-wrap gap-2">
                                  {d.special_barriers.map((b: string, i: number) => (
                                    <span key={i} className="bg-red-50 text-red-700 px-2.5 py-1 rounded-md text-xs border border-red-100 truncate max-w-[200px] inline-block">{b}</span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* 面试侧重 */}
                            {d.interview_focus && d.interview_focus.length > 0 && (
                              <div>
                                <p className="text-xs font-medium text-surface-400 uppercase tracking-wider mb-1.5">🎤 面试侧重</p>
                                <div className="flex flex-wrap gap-2">
                                  {d.interview_focus.map((f: string, i: number) => (
                                    <span key={i} className="bg-amber-50 text-amber-700 px-2.5 py-1 rounded-md text-xs border border-amber-100 truncate max-w-[200px] inline-block">{f}</span>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* 技能标签 */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                              {d.required_skills && d.required_skills.length > 0 && (
                                <div>
                                  <p className="text-xs font-medium text-surface-400 uppercase tracking-wider mb-1.5">🔧 必备技能</p>
                                  <div className="flex flex-wrap gap-1.5">
                                    {d.required_skills.map((s: string, i: number) => (
                                      <span key={i} className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs border border-blue-100 truncate max-w-[200px] inline-block">{s}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {d.preferred_skills && d.preferred_skills.length > 0 && (
                                <div>
                                  <p className="text-xs font-medium text-surface-400 uppercase tracking-wider mb-1.5">✨ 加分技能</p>
                                  <div className="flex flex-wrap gap-1.5">
                                    {d.preferred_skills.map((s: string, i: number) => (
                                      <span key={i} className="bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded text-xs border border-emerald-100 truncate max-w-[200px] inline-block">{s}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* 软性要求 + 行业 */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                              {d.soft_skills && d.soft_skills.length > 0 && (
                                <div>
                                  <p className="text-xs font-medium text-surface-400 uppercase tracking-wider mb-1.5">💬 软性要求</p>
                                  <div className="flex flex-wrap gap-1.5">
                                    {d.soft_skills.map((s: string, i: number) => (
                                      <span key={i} className="bg-purple-50 text-purple-700 px-2 py-0.5 rounded text-xs border border-purple-100 truncate max-w-[200px] inline-block">{s}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {d.industry_keywords && d.industry_keywords.length > 0 && (
                                <div>
                                  <p className="text-xs font-medium text-surface-400 uppercase tracking-wider mb-1.5">🏢 行业领域</p>
                                  <div className="flex flex-wrap gap-1.5">
                                    {d.industry_keywords.map((k: string, i: number) => (
                                      <span key={i} className="bg-surface-100 text-surface-600 px-2 py-0.5 rounded text-xs truncate max-w-[200px] inline-block">{k}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* 招聘动因 */}
                            {d.hiring_motivation && (
                              <div>
                                <p className="text-xs font-medium text-surface-400 uppercase tracking-wider mb-1.5">💡 招聘动因</p>
                                <p className="text-sm text-surface-600">{d.hiring_motivation}</p>
                              </div>
                            )}
                          </div>
                        )
                      })()}
                    </>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </main>
      <ConfirmDialog open={!!confirmAction} message={confirmAction?.message || ''} onConfirm={confirmAction?.onConfirm || (() => {})} onCancel={() => setConfirmAction(null)} />
    </div>
  )
}
