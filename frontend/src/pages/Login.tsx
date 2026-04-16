import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authApi } from '../api/client'
import { useAuthStore } from '../stores/authStore'
import { toastError } from '../stores/toastStore'

export default function Login() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password) return

    setLoading(true)
    try {
      const res = await authApi.login(email.trim(), password)
      setAuth(res.data.access_token, res.data.user)
      navigate('/materials')
    } catch (error: any) {
      toastError(error.response?.data?.detail || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-50 flex items-center justify-center p-4 relative overflow-hidden">

      <div className="max-w-md w-full relative z-10">
        <div className="text-center mb-8 animate-fade-in-up">
          <h1 className="text-3xl font-bold text-primary-600 mb-2">ResumeForge</h1>
          <p className="text-surface-500">登录你的账户</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white border border-surface-200 rounded-2xl p-8 space-y-5 shadow-lg animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          <div>
            <label className="block text-sm font-medium text-surface-700 mb-1.5">邮箱</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="请输入邮箱"
              required
              className="w-full px-4 py-3 bg-surface-50 border border-surface-200 rounded-xl text-surface-900 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-400 transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-surface-700 mb-1.5">密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="输入密码"
              required
              className="w-full px-4 py-3 bg-surface-50 border border-surface-200 rounded-xl text-surface-900 placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-400 transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !email.trim() || !password}
            className="w-full py-3 bg-primary-600 hover:bg-primary-500 text-white font-medium rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-primary-500/20"
          >
            {loading ? '登录中...' : '登录'}
          </button>

          <p className="text-center text-sm text-surface-400">
            还没有账户？{' '}
            <Link to="/register" className="text-primary-600 hover:text-primary-500 font-medium transition-colors">
              注册
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
