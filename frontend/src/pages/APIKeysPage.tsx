import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Key, Plus, Copy, Trash2, Check, AlertTriangle } from 'lucide-react'
import Layout from '../components/Layout'
import Badge from '../components/Badge'
import { Skeleton } from '../components/LoadingStates'
import { useToast } from '../components/Toast'
import api from '../utils/api'
import { formatDate } from '../utils/formatting'

interface APIKey {
  id: number
  name: string
  key_preview?: string
  created_at: string
  last_used_at?: string
  is_active: boolean
}

interface NewKeyResult {
  id: number
  key: string
  name: string
}

export default function APIKeysPage() {
  const [keys, setKeys] = useState<APIKey[]>([])
  const [loading, setLoading] = useState(true)
  const [keyName, setKeyName] = useState('')
  const [creating, setCreating] = useState(false)
  const [newKey, setNewKey] = useState<NewKeyResult | null>(null)
  const [copied, setCopied] = useState(false)
  const [revokingId, setRevokingId] = useState<number | null>(null)
  const { success, error } = useToast()

  const fetchKeys = useCallback(async () => {
    try {
      const r = await api.get('/api-keys')
      setKeys(r.data.keys ?? r.data ?? [])
    } catch {
      error('Failed to load API keys')
    } finally {
      setLoading(false)
    }
  }, [error])

  useEffect(() => { fetchKeys() }, [fetchKeys])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!keyName.trim()) return
    setCreating(true)
    try {
      const r = await api.post('/api-keys', { name: keyName.trim() })
      setNewKey({ id: r.data.id, key: r.data.key ?? r.data.api_key, name: keyName.trim() })
      setKeyName('')
      fetchKeys()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Failed to create key'
      error('Creation failed', msg)
    } finally {
      setCreating(false)
    }
  }

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    success('Copied!', 'API key copied to clipboard')
    setTimeout(() => setCopied(false), 2000)
  }

  const handleRevoke = async (id: number) => {
    if (!confirm('Revoke this API key? This cannot be undone.')) return
    setRevokingId(id)
    try {
      await api.delete(`/api-keys/${id}`)
      success('Revoked', 'API key has been revoked')
      fetchKeys()
    } catch {
      error('Revoke failed', 'Please try again')
    } finally {
      setRevokingId(null)
    }
  }

  const activeKeys = keys.filter((k) => k.is_active)
  const revokedKeys = keys.filter((k) => !k.is_active)

  return (
    <Layout>
      <div className="max-w-3xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">API Keys</h1>
          <p className="text-slate-400 text-sm mt-1">Manage authentication keys for API access</p>
        </div>

        {/* New key revealed modal */}
        {newKey && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-green-500/10 border border-green-500/30 rounded-xl p-5 mb-6"
          >
            <div className="flex items-start gap-3 mb-3">
              <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-white">Save your API key now</p>
                <p className="text-sm text-slate-400">This key will only be shown once. Copy it to a safe place.</p>
              </div>
            </div>
            <div className="flex items-center gap-2 bg-slate-900 rounded-lg p-3">
              <code className="flex-1 text-sm font-mono text-green-400 break-all">{newKey.key}</code>
              <button
                onClick={() => handleCopy(newKey.key)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600/20 hover:bg-green-600/30 border border-green-500/30 text-green-400 text-xs rounded-lg transition-colors flex-shrink-0"
              >
                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <button
              onClick={() => setNewKey(null)}
              className="mt-3 text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              I've saved the key, dismiss
            </button>
          </motion.div>
        )}

        {/* Create key form */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-5 mb-6">
          <h2 className="font-semibold text-white mb-4">Create New Key</h2>
          <form onSubmit={handleCreate} className="flex gap-3">
            <input
              type="text"
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              placeholder='Key name (e.g. "Production", "Testing")'
              className="flex-1 px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm transition-colors"
              required
            />
            <button
              type="submit"
              disabled={creating || !keyName.trim()}
              className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-xl transition-colors whitespace-nowrap"
            >
              {creating ? (
                <span className="animate-spin">⋯</span>
              ) : (
                <Plus className="w-4 h-4" />
              )}
              Generate Key
            </button>
          </form>
        </div>

        {/* Active keys */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 mb-4">
          <div className="px-5 py-4 border-b border-slate-700">
            <h2 className="font-semibold text-white">Active Keys ({activeKeys.length})</h2>
          </div>
          {loading ? (
            <div className="p-5 space-y-4">
              {[1, 2].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : activeKeys.length === 0 ? (
            <div className="py-12 text-center">
              <Key className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400 text-sm">No active API keys</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-700/50">
              {activeKeys.map((key) => (
                <div key={key.id} className="px-5 py-4 flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white text-sm">{key.name}</span>
                      <Badge variant="success" size="sm">Active</Badge>
                    </div>
                    <p className="text-xs text-slate-500 font-mono">
                      {key.key_preview ?? '••••••••••••••••'}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      Created {formatDate(key.created_at)}
                      {key.last_used_at && ` · Last used ${formatDate(key.last_used_at)}`}
                    </p>
                  </div>
                  <button
                    onClick={() => handleRevoke(key.id)}
                    disabled={revokingId === key.id}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-400 text-xs rounded-lg transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                    Revoke
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Revoked keys */}
        {revokedKeys.length > 0 && (
          <div className="bg-slate-800/50 rounded-xl border border-slate-700/50">
            <div className="px-5 py-4 border-b border-slate-700/50">
              <h2 className="text-sm font-medium text-slate-400">Revoked Keys ({revokedKeys.length})</h2>
            </div>
            <div className="divide-y divide-slate-700/30">
              {revokedKeys.map((key) => (
                <div key={key.id} className="px-5 py-3 flex items-center gap-4 opacity-50">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-slate-400">{key.name}</span>
                      <Badge variant="error" size="sm">Revoked</Badge>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">Created {formatDate(key.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
