import { create } from 'zustand'

interface AuthUser {
  id: string
  email: string
  name: string | null
  created_at: string
}

interface AuthStore {
  token: string | null
  user: AuthUser | null
  tokenExpiry: number | null
  isAuthenticated: () => boolean
  isTokenExpired: () => boolean
  setAuth: (token: string, user: AuthUser) => void
  logout: () => void
}

const TOKEN_KEY = 'resumeforge_token'
const USER_KEY = 'resumeforge_user'
const TOKEN_EXPIRY_KEY = 'resumeforge_token_expiry'

function decodeTokenExp(token: string): number | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = JSON.parse(atob(parts[1]))
    return typeof payload.exp === 'number' ? payload.exp : null
  } catch {
    return null
  }
}

function loadSavedAuth(): { token: string | null; user: AuthUser | null; tokenExpiry: number | null } {
  try {
    const token = localStorage.getItem(TOKEN_KEY)
    const userJson = localStorage.getItem(USER_KEY)
    const expiryStr = localStorage.getItem(TOKEN_EXPIRY_KEY)
    if (token && userJson) {
      const tokenExpiry = expiryStr ? parseInt(expiryStr, 10) : decodeTokenExp(token)
      if (tokenExpiry && Date.now() >= tokenExpiry * 1000) {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        localStorage.removeItem(TOKEN_EXPIRY_KEY)
        return { token: null, user: null, tokenExpiry: null }
      }
      return { token, user: JSON.parse(userJson), tokenExpiry }
    }
  } catch {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    localStorage.removeItem(TOKEN_EXPIRY_KEY)
  }
  return { token: null, user: null, tokenExpiry: null }
}

const saved = loadSavedAuth()

export const useAuthStore = create<AuthStore>((set, get) => ({
  token: saved.token,
  user: saved.user,
  tokenExpiry: saved.tokenExpiry,

  isTokenExpired: () => {
    const expiry = get().tokenExpiry
    if (!expiry) return true
    return Date.now() >= expiry * 1000
  },

  isAuthenticated: () => !!get().token && !get().isTokenExpired(),

  setAuth: (token, user) => {
    const tokenExpiry = decodeTokenExp(token)
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    if (tokenExpiry) {
      localStorage.setItem(TOKEN_EXPIRY_KEY, String(tokenExpiry))
    }
    set({ token, user, tokenExpiry })
  },

  logout: () => {
    const user = get().user
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    localStorage.removeItem(TOKEN_EXPIRY_KEY)
    localStorage.removeItem('resumeforge_device_id')
    if (user?.id) {
      localStorage.removeItem(`resumeforge_sessions_${user.id}`)
    }
    localStorage.removeItem('resumeforge_sessions')
    set({ token: null, user: null, tokenExpiry: null })
    window.location.href = '/login'
  },
}))
