import axios from 'axios'
import { API_BASE_URL } from './constants'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: attach Authorization header
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: handle 401 unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear both localStorage and Zustand in-memory state
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      // Dynamically import to avoid circular dependency
      import('../store/authStore').then(({ useAuthStore }) => {
        useAuthStore.getState().logout()
      })
      if (!window.location.pathname.includes('/auth')) {
        window.location.href = '/auth'
      }
    }
    return Promise.reject(error)
  }
)

export default api
