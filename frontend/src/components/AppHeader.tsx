import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

type ActiveNav = 'materials' | 'jds' | 'resumes'

interface AppHeaderProps {
  title: string
  activeNav: ActiveNav
  actions?: React.ReactNode
}

const NAV_ITEMS: { key: ActiveNav; label: string; path: string }[] = [
  { key: 'materials', label: '资料库', path: '/materials' },
  { key: 'jds', label: '岗位管理', path: '/jds' },
  { key: 'resumes', label: '简历管理', path: '/resumes' },
]

export default function AppHeader({ title, activeNav, actions }: AppHeaderProps) {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [menuOpen, setMenuOpen] = useState(false)

  const displayName = user?.name || user?.email

  return (
    <header className="bg-white/95 backdrop-blur-md border-b border-surface-200 px-4 sm:px-6 py-4">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2 sm:gap-4 min-w-0 flex-1">
          <button
            onClick={() => navigate('/')}
            className="text-surface-500 hover:text-surface-700 transition-colors py-2 flex-shrink-0"
          >
            <span className="hidden sm:inline">← 首页</span>
            <span className="sm:hidden">←</span>
          </button>
          <span className="text-surface-300 hidden sm:inline">|</span>
          <h1 className="text-lg sm:text-xl font-semibold text-surface-900 truncate">{title}</h1>
        </div>

        <div className="hidden sm:flex items-center gap-3 flex-shrink-0">
          <nav className="flex items-center gap-1 mr-2">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.key}
                onClick={() => navigate(item.path)}
                className={
                  item.key === activeNav
                    ? 'px-3 py-2 rounded-lg text-sm transition-all bg-primary-50 text-primary-600 font-medium'
                    : 'px-3 py-2 rounded-lg text-sm transition-all text-surface-500 hover:text-surface-700 hover:bg-surface-50'
                }
                aria-current={item.key === activeNav ? 'page' : undefined}
              >
                {item.label}
              </button>
            ))}
          </nav>
          <span className="text-surface-300">|</span>
          <span className="text-sm text-surface-500 truncate max-w-[160px]">{displayName}</span>
          <button
            onClick={() => { logout(); navigate('/') }}
            className="text-sm text-surface-400 hover:text-danger-500 transition-colors py-2"
            aria-label="退出登录"
          >
            退出
          </button>
          {actions}
        </div>

        <button
          onClick={() => setMenuOpen((v) => !v)}
          className="sm:hidden text-surface-600 hover:text-surface-900 py-2 px-1 -mr-1 transition-colors"
          aria-label="菜单"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {menuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {menuOpen && (
        <div className="sm:hidden border-t border-surface-200 mt-4 pt-3 pb-2 space-y-1">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              onClick={() => { navigate(item.path); setMenuOpen(false) }}
              className={
                item.key === activeNav
                  ? 'w-full text-left px-3 py-2.5 rounded-lg text-sm bg-primary-50 text-primary-600 font-medium transition-colors'
                  : 'w-full text-left px-3 py-2.5 rounded-lg text-sm text-surface-500 hover:text-surface-700 hover:bg-surface-50 transition-colors'
              }
              aria-current={item.key === activeNav ? 'page' : undefined}
            >
              {item.label}
            </button>
          ))}
          <div className="flex items-center justify-between pt-2 mt-2 border-t border-surface-100">
            <span className="text-sm text-surface-500 truncate max-w-[200px]">{displayName}</span>
            <button
              onClick={() => { logout(); navigate('/') }}
              className="text-sm text-surface-400 hover:text-danger-500 transition-colors py-2 px-3"
            >
              退出
            </button>
          </div>
        </div>
      )}
    </header>
  )
}
