import { create } from 'zustand'

export interface User {
  id: number
  email: string
  full_name: string
  tier: string
  is_verified: boolean
}

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  setToken: (token: string) => void
  setUser: (user: User) => void
  logout: () => void
}

// Initialize token from localStorage
const storedToken = localStorage.getItem('auth_token')
const storedUser = (() => {
  try {
    const raw = localStorage.getItem('auth_user')
    return raw ? (JSON.parse(raw) as User) : null
  } catch {
    return null
  }
})()

export const useAuthStore = create<AuthState>((set) => ({
  token: storedToken,
  user: storedUser,
  isAuthenticated: !!storedToken,

  setToken: (token: string) => {
    localStorage.setItem('auth_token', token)
    set({ token, isAuthenticated: true })
  },

  setUser: (user: User) => {
    localStorage.setItem('auth_user', JSON.stringify(user))
    set({ user })
  },

  logout: () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    set({ token: null, user: null, isAuthenticated: false })
  },
}))
