import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

export default function Home() {
  const navigate = useNavigate()
  const { isAuthenticated, user, logout } = useAuthStore()
  const authenticated = isAuthenticated()

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const delay = Number(entry.target.getAttribute('data-delay') || 0)
            setTimeout(() => {
              entry.target.classList.add('animate-fade-in-up')
            }, delay)
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.08, rootMargin: '0px 0px -40px 0px' }
    )
    document.querySelectorAll('[data-reveal]').forEach((el) => observer.observe(el))
    return () => observer.disconnect()
  }, [])

  const painPoints = [
    '材料太多太散，不知道哪些有价值',
    '做了很多事，不会用"简历语言"包装',
    '看到合适的岗位，不知道怎么调整简历',
    '十年没写简历，不知道从哪下手',
  ]

  return (
    <div className="min-h-screen bg-white relative overflow-x-hidden">
      <style>{`
        .forge-heading {
          font-family: 'Cormorant Garamond', Georgia, 'Times New Roman', serif;
          background: linear-gradient(135deg, #d97706 0%, #ea580c 32%, #dc2626 56%, #7c3aed 78%, #0891b2 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        @keyframes float-1 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(30px, -25px) scale(1.05); }
          66% { transform: translate(-20px, 18px) scale(0.95); }
        }
        @keyframes float-2 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(-28px, 22px) scale(0.96); }
          66% { transform: translate(18px, -28px) scale(1.04); }
        }
        @keyframes float-3 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(22px, 28px) scale(1.03); }
        }

        .animate-float-1 { animation: float-1 20s ease-in-out infinite; }
        .animate-float-2 { animation: float-2 25s ease-in-out infinite; }
        .animate-float-3 { animation: float-3 18s ease-in-out infinite; }

        [data-reveal] { opacity: 0; }
      `}</style>

      <div className="fixed top-0 left-0 right-0 h-px z-50 bg-gradient-to-r from-transparent via-primary-400/30 to-transparent" />

      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute -top-[300px] -right-[200px] w-[900px] h-[900px] rounded-full animate-float-1"
          style={{ background: 'radial-gradient(circle, rgba(251,191,36,0.045) 0%, transparent 65%)' }}
        />
        <div
          className="absolute top-[35%] -left-[250px] w-[700px] h-[700px] rounded-full animate-float-2"
          style={{ background: 'radial-gradient(circle, rgba(99,102,241,0.035) 0%, transparent 65%)' }}
        />
        <div
          className="absolute -bottom-[200px] right-[15%] w-[600px] h-[600px] rounded-full animate-float-3"
          style={{ background: 'radial-gradient(circle, rgba(6,182,212,0.03) 0%, transparent 65%)' }}
        />
      </div>

      <nav className="fixed top-0 left-0 right-0 z-30 mt-px">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex h-14 items-center justify-between px-5 bg-white/80 backdrop-blur-md border border-surface-200/50 rounded-b-xl">
            <div className="flex items-center gap-2.5">
              <div className="w-2 h-2 rounded-full bg-amber-400 shadow-lg shadow-amber-400/30" />
              <span className="font-semibold text-surface-900 text-sm tracking-[0.15em]">RESUMEFORGE</span>
            </div>
            {authenticated ? (
              <div className="flex items-center gap-4">
                <span className="text-xs text-surface-400 hidden sm:inline">{user?.name || user?.email}</span>
                <button
                  onClick={() => { logout(); navigate('/') }}
                  className="text-xs text-surface-400 hover:text-red-500 transition-colors duration-200"
                >
                  退出
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => navigate('/login')}
                  className="text-xs text-surface-600 hover:text-surface-900 transition-colors duration-200 px-4 py-2 rounded-lg hover:bg-surface-100"
                >
                  登录
                </button>
                <button
                  onClick={() => navigate('/register')}
                  className="text-xs text-white bg-primary-600 hover:bg-primary-700 px-4 py-1.5 rounded-lg transition-colors duration-200"
                >
                  注册
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>

      <section className="min-h-screen flex items-center justify-center relative pt-16 pb-24">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <div className="animate-fade-in-up mb-10 flex justify-center">
            <div className="relative">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-400/20 via-orange-500/15 to-primary-500/15 border border-surface-200 flex items-center justify-center">
                <svg className="w-7 h-7 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
              </div>
              <div className="absolute -inset-3 rounded-3xl bg-amber-400/[0.06] blur-xl" />
            </div>
          </div>

          <h1
            className="animate-fade-in-up text-6xl sm:text-7xl md:text-8xl font-bold tracking-tight mb-5 forge-heading leading-[1.1]"
            style={{ animationDelay: '0.08s' }}
          >
            ResumeForge
          </h1>

          <p
            className="animate-fade-in-up text-xl sm:text-2xl font-extralight text-surface-900 mb-3 tracking-[0.3em]"
            style={{ animationDelay: '0.16s' }}
          >
            简历锻造工坊
          </p>

          <p
            className="animate-fade-in-up text-base sm:text-lg text-surface-500 max-w-md mx-auto mb-14"
            style={{ animationDelay: '0.24s' }}
          >
            把十年经历丢进来，锻造成一份好简历
          </p>

          <div className="animate-fade-in-up max-w-2xl mx-auto mb-12" style={{ animationDelay: '0.32s' }}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {painPoints.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 text-left px-4 py-3 rounded-xl bg-surface-50 border border-surface-200 hover:bg-surface-100 hover:border-surface-300 transition-colors duration-300"
                >
                  <div className="w-1 h-1 rounded-full bg-amber-400/70 flex-shrink-0" />
                  <span className="text-sm text-surface-500">{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
            {authenticated ? (
              <div className="space-y-5">
                <button
                  onClick={() => navigate('/materials')}
                  className="group relative inline-flex items-center gap-2.5 px-10 py-4 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-white font-medium rounded-xl transition-all duration-300 text-lg shadow-xl shadow-amber-600/15 hover:shadow-amber-500/25 hover:scale-[1.02] active:scale-[0.98]"
                >
                  开始锻造简历
                  <svg className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </button>
                <div className="flex items-center justify-center gap-2.5 flex-wrap">
                  <button
                    onClick={() => navigate('/materials')}
                    className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-surface-50 text-surface-600 hover:text-surface-900 text-sm rounded-lg transition-all duration-200 border border-surface-200 hover:border-surface-300"
                  >
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                    资料库
                  </button>
                  <button
                    onClick={() => navigate('/jds')}
                    className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-surface-50 text-surface-600 hover:text-surface-900 text-sm rounded-lg transition-all duration-200 border border-surface-200 hover:border-surface-300"
                  >
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
                      <path d="M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      <path d="M9 5a2 2 0 002 2h2a2 2 0 002-2" />
                    </svg>
                    岗位管理
                  </button>
                  <button
                    onClick={() => navigate('/resumes')}
                    className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-surface-50 text-surface-600 hover:text-surface-900 text-sm rounded-lg transition-all duration-200 border border-surface-200 hover:border-surface-300"
                  >
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    简历管理
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-center gap-3">
                  <button
                    onClick={() => navigate('/register')}
                    className="group inline-flex items-center gap-2 px-8 py-3.5 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-white font-medium rounded-xl transition-all duration-300 text-base shadow-xl shadow-amber-600/15 hover:shadow-amber-500/25 hover:scale-[1.02] active:scale-[0.98]"
                  >
                    注册新账户
                    <svg className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                  </button>
                  <button
                    onClick={() => navigate('/login')}
                    className="px-8 py-3.5 border border-primary-200 text-primary-600 hover:bg-primary-50 hover:border-primary-300 font-medium rounded-xl transition-all duration-300 text-base"
                  >
                    登录
                  </button>
                </div>
                <p className="text-xs text-surface-300">
                  AI 自动提炼经历，一键生成贴合岗位的简历
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="animate-fade-in-up absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1.5" style={{ animationDelay: '0.7s' }}>
          <span className="text-[10px] text-surface-300 tracking-[0.2em] uppercase">Scroll</span>
          <div className="w-px h-6 bg-gradient-to-b from-surface-300/60 to-transparent" />
        </div>
      </section>

      <div className="max-w-5xl mx-auto px-6">
        <div className="h-px bg-gradient-to-r from-transparent via-surface-200 to-transparent" />
      </div>

      <section className="py-28 sm:py-36 relative">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div data-reveal className="text-center mb-20 sm:mb-24">
            <p className="text-xs font-medium text-primary-500 tracking-[0.25em] uppercase mb-4">锻造流程</p>
            <h2 className="text-3xl sm:text-4xl font-light text-surface-900">从零散材料到精准简历</h2>
          </div>

          <div className="relative">
            <div className="hidden sm:block absolute top-6 left-[calc(12.5%+24px)] right-[calc(12.5%+24px)] h-px pointer-events-none">
              <div className="w-full h-full bg-gradient-to-r from-amber-500/15 via-rose-500/15 to-cyan-500/15" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-10 sm:gap-6">
              {[
                {
                  step: '01',
                  title: '上传材料',
                  desc: '将散落的经历材料全部上传，支持任意格式',
                  gradient: 'from-amber-400 to-orange-500',
                  icon: (
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                  ),
                },
                {
                  step: '02',
                  title: 'AI 分析提炼',
                  desc: 'GPT-4 自动识别价值信息，提炼核心成就与能力',
                  gradient: 'from-orange-400 to-rose-500',
                  icon: (
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 2L9.5 9.5 2 12l7.5 2.5L12 22l2.5-7.5L22 12l-7.5-2.5L12 2z" />
                    </svg>
                  ),
                },
                {
                  step: '03',
                  title: '锻造简历',
                  desc: '一键生成专业简历，精准匹配目标岗位要求',
                  gradient: 'from-primary-400 to-violet-500',
                  icon: (
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                    </svg>
                  ),
                },
                {
                  step: '04',
                  title: '精准投递',
                  desc: '针对不同岗位自动调整，提升面试通过率',
                  gradient: 'from-cyan-400 to-teal-500',
                  icon: (
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10" />
                      <circle cx="12" cy="12" r="6" />
                      <circle cx="12" cy="12" r="2" />
                    </svg>
                  ),
                },
              ].map((feature, i) => (
                <div
                  key={feature.step}
                  data-reveal
                  data-delay={String(i * 120)}
                  className="relative flex flex-col items-center text-center"
                >
                  <div className={`relative w-12 h-12 rounded-full bg-gradient-to-br ${feature.gradient} flex items-center justify-center text-white mb-7 shadow-lg z-10`}>
                    {feature.icon}
                  </div>
                  <span className="text-[10px] text-surface-300 font-mono tracking-wider mb-2">{feature.step}</span>
                  <h3 className="text-base font-medium text-surface-900 mb-2.5">{feature.title}</h3>
                  <p className="text-sm text-surface-500 leading-relaxed max-w-[220px]">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="max-w-5xl mx-auto px-6">
        <div className="h-px bg-gradient-to-r from-transparent via-surface-200 to-transparent" />
      </div>

      <section className="py-24 sm:py-28 relative">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
            {[
              {
                label: 'AI 引擎',
                value: 'GPT-4',
                icon: (
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="4" y="4" width="16" height="16" rx="2" />
                    <rect x="9" y="9" width="6" height="6" />
                    <line x1="9" y1="1" x2="9" y2="4" />
                    <line x1="15" y1="1" x2="15" y2="4" />
                    <line x1="9" y1="20" x2="9" y2="23" />
                    <line x1="15" y1="20" x2="15" y2="23" />
                    <line x1="20" y1="9" x2="23" y2="9" />
                    <line x1="20" y1="14" x2="23" y2="14" />
                    <line x1="1" y1="9" x2="4" y2="9" />
                    <line x1="1" y1="14" x2="4" y2="14" />
                  </svg>
                ),
              },
              {
                label: '格式支持',
                value: 'PDF / Word / PPT',
                icon: (
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="12 2 2 7 12 12 22 7 12 2" />
                    <polyline points="2 17 12 22 22 17" />
                    <polyline points="2 12 12 17 22 12" />
                  </svg>
                ),
              },
              {
                label: '锻造速度',
                value: '分钟级生成',
                icon: (
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                  </svg>
                ),
              },
              {
                label: '隐私保护',
                value: '数据安全',
                icon: (
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  </svg>
                ),
              },
            ].map((stat, i) => (
              <div
                key={stat.label}
                data-reveal
                data-delay={String(i * 80)}
                className="bg-white border border-surface-200 rounded-xl p-5 sm:p-6 text-center hover:bg-surface-50 transition-colors duration-300"
              >
                <div className="inline-flex items-center justify-center w-9 h-9 rounded-lg bg-primary-50 text-primary-500 mb-3.5">
                  {stat.icon}
                </div>
                <div className="text-base font-semibold text-surface-900 mb-1">{stat.value}</div>
                <div className="text-[11px] text-surface-500 tracking-wide">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="py-10 border-t border-surface-100">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-amber-400/60" />
            <span className="text-xs text-surface-300 tracking-wider">RESUMEFORGE</span>
          </div>
          <p className="text-[11px] text-surface-300">支持 PDF / PPT / Word / 图片 / 文本</p>
        </div>
      </footer>
    </div>
  )
}
