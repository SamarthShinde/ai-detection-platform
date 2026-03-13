import { useAuthStore } from '../store/authStore'
import api from '../utils/api'

interface LoginCredentials {
  email: string
  password: string
}

interface RegisterData {
  email: string
  password: string
  full_name: string
}

export interface TwoFactorChallenge {
  requires2fa: true
  tempToken: string
  email: string
}

import type { User } from '../store/authStore'

interface AuthHookReturn {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void | TwoFactorChallenge>
  logout: () => void
  register: (data: RegisterData) => Promise<void>
  refreshUser: () => Promise<void>
  verify2FA: (otp: string, tempToken: string) => Promise<void>
}

export function useAuth(): AuthHookReturn {
  const { user, token, isAuthenticated, setToken, setUser, logout: storeLogout } = useAuthStore()

  const login = async (email: string, password: string): Promise<void | TwoFactorChallenge> => {
    const response = await api.post<{ access_token?: string; requires_2fa?: boolean; temp_token?: string }>(
      '/auth/login',
      { email, password }
    )

    // 2FA required — return challenge info to the caller
    if (response.data.requires_2fa && response.data.temp_token) {
      return { requires2fa: true, tempToken: response.data.temp_token, email }
    }

    const access_token = response.data.access_token
    if (!access_token) throw new Error('No access token received')
    setToken(access_token)

    // Fetch user profile
    const userResponse = await api.get('/auth/me', {
      headers: { Authorization: `Bearer ${access_token}` },
    })
    setUser(userResponse.data)
  }

  const verify2FA = async (otp: string, tempToken: string): Promise<void> => {
    const response = await api.post<{ access_token: string }>(
      '/auth/verify-2fa',
      { otp },
      { headers: { Authorization: `Bearer ${tempToken}` } }
    )
    const access_token = response.data.access_token
    setToken(access_token)
    const userResponse = await api.get('/auth/me', {
      headers: { Authorization: `Bearer ${access_token}` },
    })
    setUser(userResponse.data)
  }

  const register = async (data: RegisterData): Promise<void> => {
    await api.post('/auth/register', data)
  }

  const refreshUser = async (): Promise<void> => {
    const response = await api.get('/auth/me')
    setUser(response.data)
  }

  const logout = (): void => {
    storeLogout()
  }

  return {
    user,
    token,
    isAuthenticated,
    login,
    logout,
    register,
    refreshUser,
    verify2FA,
  }
}
