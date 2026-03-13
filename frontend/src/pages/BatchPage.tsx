import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Layers, Plus, Download, RefreshCw, ChevronRight } from 'lucide-react'
import Layout from '../components/Layout'
import ProgressBar from '../components/ProgressBar'
import Badge from '../components/Badge'
import { Skeleton } from '../components/LoadingStates'
import { useToast } from '../components/Toast'
import api from '../utils/api'
import { formatDate } from '../utils/formatting'

interface Batch {
  batch_id: number
  batch_name: string
  status: string
  files_total: number
  files_completed: number
  files_failed: number
  progress_percent: number
  created_at: string | null
  completed_at: string | null
}

const STATUS_VARIANTS: Record<string, 'success' | 'info' | 'warning' | 'error' | 'default'> = {
  completed: 'success',
  processing: 'info',
  created: 'warning',
  error: 'error',
}

export default function BatchPage() {
  const [batches, setBatches] = useState<Batch[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const { error, success } = useToast()

  const fetchBatches = useCallback(async () => {
    try {
      const r = await api.get('/batches?limit=50')
      setBatches(r.data.batches ?? [])
    } catch {
      error('Failed to load batches')
    } finally {
      setLoading(false)
    }
  }, [error])

  useEffect(() => {
    fetchBatches()
    // Poll active batches
    const interval = setInterval(() => {
      if (batches.some((b) => b.status === 'processing' || b.status === 'created')) {
        fetchBatches()
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [fetchBatches, batches])

  const handleExport = async (batchId: number, fmt: 'json' | 'csv') => {
    try {
      const r = await api.get(`/batches/${batchId}/export?fmt=${fmt}`, {
        responseType: fmt === 'csv' ? 'blob' : 'json',
      })
      if (fmt === 'csv') {
        const blob = new Blob([r.data], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `batch-${batchId}.csv`
        a.click()
        URL.revokeObjectURL(url)
      } else {
        const blob = new Blob([JSON.stringify(r.data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `batch-${batchId}.json`
        a.click()
        URL.revokeObjectURL(url)
      }
      success('Export ready', `Batch exported as ${fmt.toUpperCase()}`)
    } catch {
      error('Export failed', 'Please try again')
    }
  }

  const active = batches.filter((b) => b.status !== 'completed' && b.status !== 'error')
  const completed = batches.filter((b) => b.status === 'completed' || b.status === 'error')

  return (
    <Layout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Batch Processing</h1>
          <p className="text-slate-400 text-sm mt-1">Group multiple files for bulk analysis</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchBatches} className="p-2 text-slate-400 hover:text-white transition-colors rounded-lg">
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link
            to="/upload"
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Batch
          </Link>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} variant="card" />)}
        </div>
      ) : batches.length === 0 ? (
        <div className="bg-slate-800 rounded-2xl border border-slate-700 py-20 text-center">
          <Layers className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-300 mb-2">No batches yet</h3>
          <p className="text-slate-500 text-sm mb-6">Use batch upload mode when uploading multiple files</p>
          <Link
            to="/upload"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create First Batch
          </Link>
        </div>
      ) : (
        <>
          {/* Active batches */}
          {active.length > 0 && (
            <div className="mb-8">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
                Active ({active.length})
              </h2>
              <div className="space-y-3">
                {active.map((batch) => (
                  <motion.div
                    key={batch.batch_id}
                    layout
                    className="bg-slate-800 rounded-xl border border-slate-700 p-5"
                  >
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div>
                        <h3 className="font-semibold text-white">{batch.batch_name}</h3>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {batch.files_completed} / {batch.files_total} files processed
                          {batch.created_at && ` · Created ${formatDate(batch.created_at)}`}
                        </p>
                      </div>
                      <Badge variant={STATUS_VARIANTS[batch.status] ?? 'default'}>{batch.status}</Badge>
                    </div>
                    <ProgressBar
                      value={batch.progress_percent}
                      color={batch.status === 'error' ? 'red' : 'blue'}
                      showLabel
                      size="md"
                    />
                    {batch.files_failed > 0 && (
                      <p className="text-xs text-red-400 mt-2">{batch.files_failed} files failed</p>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Completed batches */}
          {completed.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
                Completed ({completed.length})
              </h2>
              <div className="space-y-3">
                {completed.map((batch) => (
                  <motion.div key={batch.batch_id} layout className="bg-slate-800 rounded-xl border border-slate-700">
                    <button
                      onClick={() => setExpandedId(expandedId === batch.batch_id ? null : batch.batch_id)}
                      className="w-full flex items-center justify-between gap-4 p-5 text-left hover:bg-slate-700/30 transition-colors rounded-xl"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-white">{batch.batch_name}</span>
                          <Badge variant={STATUS_VARIANTS[batch.status] ?? 'default'} size="sm">{batch.status}</Badge>
                        </div>
                        <p className="text-xs text-slate-400">
                          {batch.files_completed} files · {batch.completed_at ? formatDate(batch.completed_at) : '—'}
                        </p>
                      </div>
                      <ChevronRight
                        className={`w-4 h-4 text-slate-400 transition-transform ${expandedId === batch.batch_id ? 'rotate-90' : ''}`}
                      />
                    </button>

                    {expandedId === batch.batch_id && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="px-5 pb-5"
                      >
                        <div className="grid grid-cols-3 gap-3 mb-4">
                          <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                            <div className="text-lg font-bold text-white">{batch.files_total}</div>
                            <div className="text-xs text-slate-400">Total files</div>
                          </div>
                          <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                            <div className="text-lg font-bold text-green-400">{batch.files_completed}</div>
                            <div className="text-xs text-slate-400">Completed</div>
                          </div>
                          <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                            <div className="text-lg font-bold text-red-400">{batch.files_failed}</div>
                            <div className="text-xs text-slate-400">Failed</div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleExport(batch.batch_id, 'json')}
                            className="flex items-center gap-1.5 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm rounded-lg transition-colors"
                          >
                            <Download className="w-3.5 h-3.5" />
                            JSON
                          </button>
                          <button
                            onClick={() => handleExport(batch.batch_id, 'csv')}
                            className="flex items-center gap-1.5 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm rounded-lg transition-colors"
                          >
                            <Download className="w-3.5 h-3.5" />
                            CSV
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </Layout>
  )
}
