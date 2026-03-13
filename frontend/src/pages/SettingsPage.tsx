import { useState } from 'react'
import { motion } from 'framer-motion'
import { User, Lock, Bell, Trash2, Moon, Sun, Shield, AlertTriangle } from 'lucide-react'
import Layout from '../components/Layout'
import { useToast } from '../components/Toast'
import { useUIStore } from '../store/uiStore'
import { useAuth } from '../hooks/useAuth'
import api from '../utils/api'

export default function SettingsPage() {
  const { user, logout, refreshUser } = useAuth()
  const { darkMode, toggleDarkMode } = useUIStore()
  const { success, error } = useToast()

  const [fullName, setFullName] = useState(user?.full_name ?? '')
  const [savingProfile, setSavingProfile] = useState(false)
  const [passwordForm, setPasswordForm] = useState({ current: '', new: '', confirm: '' })
  const [savingPassword, setSavingPassword] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleteText, setDeleteText] = useState('')
  const [deletingAccount, setDeletingAccount] = useState(false)

  const handleDeleteAccount = async () => {
    if (deleteText !== 'DELETE') return
    setDeletingAccount(true)
    try {
      await api.delete('/auth/me')
      logout()
      window.location.href = '/'
    } catch {
      error('Delete failed', 'Unable to delete account. Please try again.')
      setDeletingAccount(false)
    }
  }

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingProfile(true)
    try {
      await api.put('/auth/me', { full_name: fullName })
      await refreshUser()
      success('Profile updated', 'Your name has been saved')
    } catch {
      error('Update failed', 'Please try again')
    } finally {
      setSavingProfile(false)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (passwordForm.new !== passwordForm.confirm) {
      error('Passwords do not match', 'New password and confirmation must match')
      return
    }
    if (passwordForm.new.length < 8) {
      error('Password too short', 'Password must be at least 8 characters')
      return
    }
    setSavingPassword(true)
    try {
      await api.post('/auth/change-password', {
        current_password: passwordForm.current,
        new_password: passwordForm.new,
      })
      success('Password changed', 'Your password has been updated')
      setPasswordForm({ current: '', new: '', confirm: '' })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Failed to change password'
      error('Change failed', msg)
    } finally {
      setSavingPassword(false)
    }
  }

  const tierBadgeColor: Record<string, string> = {
    free: 'bg-slate-600 text-slate-200',
    pro: 'bg-blue-600 text-white',
    enterprise: 'bg-purple-600 text-white',
  }

  const sections = [
    { id: 'profile', icon: <User className="w-4 h-4" />, label: 'Profile' },
    { id: 'security', icon: <Lock className="w-4 h-4" />, label: 'Security' },
    { id: 'preferences', icon: <Bell className="w-4 h-4" />, label: 'Preferences' },
    { id: 'danger', icon: <AlertTriangle className="w-4 h-4" />, label: 'Danger Zone' },
  ]

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Settings</h1>
          <p className="text-slate-400 text-sm mt-1">Manage your account and preferences</p>
        </div>

        {/* Profile */}
        <section id="profile" className="bg-slate-800 rounded-xl border border-slate-700 p-6 mb-5">
          <h2 className="flex items-center gap-2 font-semibold text-white mb-5">
            <User className="w-4 h-4 text-blue-400" />
            Profile
          </h2>

          {/* Avatar */}
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-2xl font-bold text-white">
              {user?.full_name?.[0]?.toUpperCase() ?? user?.email?.[0]?.toUpperCase() ?? 'U'}
            </div>
            <div>
              <p className="font-medium text-white">{user?.full_name ?? 'User'}</p>
              <p className="text-sm text-slate-400">{user?.email}</p>
              <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium capitalize ${tierBadgeColor[user?.tier ?? 'free'] ?? tierBadgeColor['free']}`}>
                {user?.tier ?? 'free'}
              </span>
            </div>
          </div>

          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-xl text-white focus:outline-none focus:border-blue-500 text-sm transition-colors"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
              <input
                type="email"
                value={user?.email ?? ''}
                disabled
                className="w-full px-4 py-2.5 bg-slate-700/30 border border-slate-600/50 rounded-xl text-slate-500 text-sm cursor-not-allowed"
              />
              <p className="text-xs text-slate-500 mt-1">Email cannot be changed</p>
            </div>
            <button
              type="submit"
              disabled={savingProfile}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-xl transition-colors"
            >
              {savingProfile ? 'Saving...' : 'Save Changes'}
            </button>
          </form>
        </section>

        {/* Security */}
        <section id="security" className="bg-slate-800 rounded-xl border border-slate-700 p-6 mb-5">
          <h2 className="flex items-center gap-2 font-semibold text-white mb-5">
            <Lock className="w-4 h-4 text-green-400" />
            Security
          </h2>

          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Current Password</label>
              <input
                type="password"
                value={passwordForm.current}
                onChange={(e) => setPasswordForm({ ...passwordForm, current: e.target.value })}
                className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-xl text-white focus:outline-none focus:border-blue-500 text-sm transition-colors"
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">New Password</label>
              <input
                type="password"
                value={passwordForm.new}
                onChange={(e) => setPasswordForm({ ...passwordForm, new: e.target.value })}
                className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-xl text-white focus:outline-none focus:border-blue-500 text-sm transition-colors"
                placeholder="Minimum 8 characters"
                minLength={8}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Confirm New Password</label>
              <input
                type="password"
                value={passwordForm.confirm}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm: e.target.value })}
                className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-xl text-white focus:outline-none focus:border-blue-500 text-sm transition-colors"
                placeholder="Repeat new password"
              />
            </div>
            <button
              type="submit"
              disabled={savingPassword || !passwordForm.current || !passwordForm.new || !passwordForm.confirm}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-xl transition-colors"
            >
              {savingPassword ? 'Changing...' : 'Change Password'}
            </button>
          </form>

          <div className="mt-5 pt-5 border-t border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-300">Two-Factor Authentication</p>
                <p className="text-xs text-slate-500 mt-0.5">Add an extra layer of security</p>
              </div>
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-slate-500" />
                <span className="text-xs text-slate-500">Coming soon</span>
              </div>
            </div>
          </div>
        </section>

        {/* Preferences */}
        <section id="preferences" className="bg-slate-800 rounded-xl border border-slate-700 p-6 mb-5">
          <h2 className="flex items-center gap-2 font-semibold text-white mb-5">
            <Bell className="w-4 h-4 text-yellow-400" />
            Preferences
          </h2>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-300">Dark Mode</p>
              <p className="text-xs text-slate-500 mt-0.5">Switch between dark and light themes</p>
            </div>
            <div className="flex items-center gap-3">
              <Sun className="w-4 h-4 text-slate-400" />
              <button
                onClick={toggleDarkMode}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${darkMode ? 'bg-blue-600' : 'bg-slate-600'}`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${darkMode ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
              <Moon className="w-4 h-4 text-slate-400" />
            </div>
          </div>
        </section>

        {/* Danger zone */}
        <section id="danger" className="bg-slate-800 rounded-xl border border-red-500/20 p-6">
          <h2 className="flex items-center gap-2 font-semibold text-red-400 mb-5">
            <AlertTriangle className="w-4 h-4" />
            Danger Zone
          </h2>

          {!showDeleteConfirm ? (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-300">Delete Account</p>
                <p className="text-xs text-slate-500 mt-0.5">Permanently delete your account and all data</p>
              </div>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="flex items-center gap-2 px-4 py-2 bg-red-600/10 hover:bg-red-600/20 border border-red-500/20 text-red-400 text-sm rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Delete Account
              </button>
            </div>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
              <p className="text-sm text-slate-300">
                Type <span className="font-mono font-bold text-red-400">DELETE</span> to confirm account deletion.
                This cannot be undone.
              </p>
              <input
                type="text"
                value={deleteText}
                onChange={(e) => setDeleteText(e.target.value)}
                placeholder="Type DELETE to confirm"
                className="w-full px-4 py-2.5 bg-slate-700/50 border border-red-500/30 rounded-xl text-white text-sm focus:outline-none focus:border-red-500 transition-colors"
              />
              <div className="flex gap-3">
                <button
                  disabled={deleteText !== 'DELETE' || deletingAccount}
                  onClick={handleDeleteAccount}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-30 text-white text-sm font-medium rounded-xl transition-colors"
                >
                  {deletingAccount ? 'Deleting...' : 'Confirm Delete'}
                </button>
                <button
                  onClick={() => { setShowDeleteConfirm(false); setDeleteText('') }}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-xl transition-colors"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          )}
        </section>
      </div>
    </Layout>
  )
}
