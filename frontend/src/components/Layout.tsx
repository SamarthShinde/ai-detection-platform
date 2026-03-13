import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload, History, Layers, Key, Settings, LogOut,
  Menu, X, Shield, Moon, Sun, HelpCircle, ChevronLeft,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useUIStore } from '../store/uiStore'
import ProgressBar from './ProgressBar'

interface NavItem {
  icon: React.ReactNode
  label: string
  path: string
}

const navItems: NavItem[] = [
  { icon: <Upload className="w-5 h-5" />, label: 'Upload', path: '/upload' },
  { icon: <History className="w-5 h-5" />, label: 'History', path: '/history' },
  { icon: <Layers className="w-5 h-5" />, label: 'Batch', path: '/batch' },
  { icon: <Key className="w-5 h-5" />, label: 'API Keys', path: '/api-keys' },
  { icon: <Settings className="w-5 h-5" />, label: 'Settings', path: '/settings' },
]

interface LayoutProps {
  children: React.ReactNode
  quotaUsed?: number
  quotaTotal?: number
}

export default function Layout({ children, quotaUsed = 0, quotaTotal = 100 }: LayoutProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { sidebarOpen, setSidebarOpen, darkMode, toggleDarkMode } = useUIStore()
  const [mobileOpen, setMobileOpen] = useState(false)

  const quotaPct = quotaTotal > 0 ? Math.round((quotaUsed / quotaTotal) * 100) : 0
  const quotaColor = quotaPct < 50 ? 'green' : quotaPct < 80 ? 'yellow' : 'red'

  const handleLogout = () => {
    logout()
    navigate('/auth')
  }

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-700/50">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
          <Shield className="w-5 h-5 text-white" />
        </div>
        {(sidebarOpen || mobileOpen) && (
          <span className="font-bold text-white text-lg">DeepDetect</span>
        )}
      </div>

      {/* Nav items */}
      <nav className="flex-1 py-4 px-2 space-y-1">
        {navItems.map((item) => {
          const active = location.pathname === item.path
          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                active
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <span className={active ? 'text-blue-400' : 'text-slate-400 group-hover:text-white'}>
                {item.icon}
              </span>
              {(sidebarOpen || mobileOpen) && (
                <span className="text-sm font-medium">{item.label}</span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Quota */}
      {(sidebarOpen || mobileOpen) && (
        <div className="px-4 py-3 border-t border-slate-700/50">
          <div className="flex justify-between text-xs text-slate-400 mb-1.5">
            <span>Quota used</span>
            <span className={quotaPct >= 80 ? 'text-red-400' : quotaPct >= 50 ? 'text-yellow-400' : 'text-green-400'}>
              {quotaUsed}/{quotaTotal}
            </span>
          </div>
          <ProgressBar value={quotaPct} color={quotaColor} size="sm" />
        </div>
      )}

      {/* User + logout */}
      <div className="p-3 border-t border-slate-700/50">
        {(sidebarOpen || mobileOpen) ? (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-white text-xs font-bold uppercase">
                {user?.full_name?.[0] ?? user?.email?.[0] ?? 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-200 truncate">{user?.full_name ?? 'User'}</p>
              <p className="text-xs text-slate-500 truncate">{user?.tier ?? 'free'}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 text-slate-500 hover:text-red-400 transition-colors rounded"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center p-2 text-slate-500 hover:text-red-400 transition-colors rounded-lg"
            title="Logout"
          >
            <LogOut className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  )

  return (
    <div className={`min-h-screen ${darkMode ? 'dark' : ''} bg-slate-900 text-white flex`}>
      {/* Desktop sidebar */}
      <div
        className={`hidden lg:flex flex-col bg-slate-800/50 border-r border-slate-700/50 transition-all duration-300 ${
          sidebarOpen ? 'w-60' : 'w-16'
        }`}
      >
        <SidebarContent />
      </div>

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-40 lg:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed left-0 top-0 h-full w-64 bg-slate-800 border-r border-slate-700 z-50 lg:hidden"
            >
              <SidebarContent />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-14 bg-slate-800/50 border-b border-slate-700/50 flex items-center gap-4 px-4">
          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen(true)}
            className="lg:hidden p-2 text-slate-400 hover:text-white rounded-lg"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Desktop sidebar toggle */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="hidden lg:flex p-2 text-slate-400 hover:text-white rounded-lg transition-colors"
          >
            {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>

          <div className="flex-1" />

          {/* Actions */}
          <button
            onClick={toggleDarkMode}
            className="p-2 text-slate-400 hover:text-white rounded-lg transition-colors"
            title="Toggle dark mode"
          >
            {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          <Link
            to="/upload"
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <Upload className="w-4 h-4" />
            Upload
          </Link>
          <button className="p-2 text-slate-400 hover:text-white rounded-lg transition-colors">
            <HelpCircle className="w-4 h-4" />
          </button>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
      </div>
    </div>
  )
}
