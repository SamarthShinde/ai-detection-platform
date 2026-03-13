import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

interface UIState {
  darkMode: boolean
  sidebarOpen: boolean
  toasts: Toast[]
  toggleDarkMode: () => void
  setSidebarOpen: (open: boolean) => void
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      darkMode: true,
      sidebarOpen: true,
      toasts: [],

      toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),

      setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),

      addToast: (toast: Omit<Toast, 'id'>) => {
        const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`
        const newToast: Toast = { ...toast, id }
        set((state) => ({ toasts: [...state.toasts, newToast] }))

        // Auto-dismiss
        const duration = toast.duration ?? 5000
        if (duration > 0) {
          setTimeout(() => {
            get().removeToast(id)
          }, duration)
        }
      },

      removeToast: (id: string) =>
        set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
    }),
    {
      name: 'ui-store',
      partialize: (state) => ({ darkMode: state.darkMode, sidebarOpen: state.sidebarOpen }),
    }
  )
)
