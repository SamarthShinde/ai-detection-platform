import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Search, Trash2, Eye, RefreshCw, FileImage, FileVideo, ChevronLeft, ChevronRight } from 'lucide-react'
import Layout from '../components/Layout'
import Badge from '../components/Badge'
import { Skeleton } from '../components/LoadingStates'
import { useToast } from '../components/Toast'
import api from '../utils/api'
import { formatDate, formatProbability, getProbabilityColor } from '../utils/formatting'

interface Detection {
  detection_id: number
  file_hash: string
  file_type: string
  original_filename: string | null
  processing_status: string
  ai_probability: number | null
  uploaded_at: string
}

const STATUS_VARIANTS: Record<string, 'success' | 'info' | 'error' | 'warning' | 'default'> = {
  completed: 'success',
  processing: 'info',
  pending: 'warning',
  error: 'error',
}

export default function HistoryPage() {
  const [detections, setDetections] = useState<Detection[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [fileTypeFilter, setFileTypeFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(0)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [deletingIds, setDeletingIds] = useState<Set<number>>(new Set())
  const limit = 10
  const { success, error } = useToast()

  const fetchDetections = useCallback(async () => {
    setLoading(true)
    try {
      const r = await api.get(`/detections?skip=${page * limit}&limit=${limit}`)
      setDetections(r.data.detections ?? [])
      setTotal(r.data.total ?? 0)
    } catch {
      error('Failed to load detections')
    } finally {
      setLoading(false)
    }
  }, [page, error])

  useEffect(() => { fetchDetections() }, [fetchDetections])

  // Reset to page 0 when any filter changes
  useEffect(() => { setPage(0) }, [search, fileTypeFilter, statusFilter])

  const filtered = detections.filter((d) => {
    const name = (d.original_filename ?? '').toLowerCase()
    if (search && !name.includes(search.toLowerCase())) return false
    if (fileTypeFilter !== 'all' && d.file_type !== fileTypeFilter) return false
    if (statusFilter !== 'all' && d.processing_status !== statusFilter) return false
    return true
  })

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this detection?')) return
    setDeletingIds((prev) => new Set(prev).add(id))
    try {
      await api.delete(`/detections/${id}`)
      success('Deleted', 'Detection removed successfully')
      fetchDetections()
    } catch {
      error('Delete failed')
    } finally {
      setDeletingIds((prev) => { const s = new Set(prev); s.delete(id); return s })
    }
  }

  const handleBulkDelete = async () => {
    if (selected.size === 0) return
    if (!confirm(`Delete ${selected.size} detections?`)) return
    const ids = Array.from(selected)
    await Promise.all(ids.map((id) => api.delete(`/detections/${id}`).catch(() => {})))
    success('Deleted', `${ids.length} detections removed`)
    setSelected(new Set())
    fetchDetections()
  }

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const s = new Set(prev)
      if (s.has(id)) s.delete(id); else s.add(id)
      return s
    })
  }

  const pages = Math.ceil(total / limit)

  return (
    <Layout>
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Detection History</h1>
          <p className="text-slate-400 text-sm mt-1">{total} total detections</p>
        </div>
        <div className="sm:ml-auto flex items-center gap-2">
          {selected.size > 0 && (
            <button
              onClick={handleBulkDelete}
              className="flex items-center gap-1.5 px-3 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 text-red-400 text-sm rounded-lg transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              Delete {selected.size}
            </button>
          )}
          <button onClick={fetchDetections} className="p-2 text-slate-400 hover:text-white transition-colors rounded-lg">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by filename..."
            className="w-full pl-9 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>
        <select
          value={fileTypeFilter}
          onChange={(e) => setFileTypeFilter(e.target.value)}
          className="px-3 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-blue-500"
        >
          <option value="all">All types</option>
          <option value="image">Images</option>
          <option value="video">Videos</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-blue-500"
        >
          <option value="all">All status</option>
          <option value="completed">Completed</option>
          <option value="processing">Processing</option>
          <option value="pending">Pending</option>
          <option value="error">Error</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="w-10 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selected.size === filtered.length && filtered.length > 0}
                    onChange={(e) => {
                      if (e.target.checked) setSelected(new Set(filtered.map((d) => d.detection_id)))
                      else setSelected(new Set())
                    }}
                    className="rounded border-slate-600 bg-slate-700 text-blue-500"
                  />
                </th>
                <th className="px-4 py-3 text-left text-slate-400 font-medium">File</th>
                <th className="px-4 py-3 text-left text-slate-400 font-medium hidden sm:table-cell">Type</th>
                <th className="px-4 py-3 text-left text-slate-400 font-medium">AI Probability</th>
                <th className="px-4 py-3 text-left text-slate-400 font-medium hidden md:table-cell">Date</th>
                <th className="px-4 py-3 text-left text-slate-400 font-medium">Status</th>
                <th className="px-4 py-3 text-right text-slate-400 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading
                ? Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="border-b border-slate-700/50">
                      {Array.from({ length: 7 }).map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <Skeleton className="h-4 w-full" />
                        </td>
                      ))}
                    </tr>
                  ))
                : filtered.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-16 text-center text-slate-400">
                        No detections found.{' '}
                        <Link to="/upload" className="text-blue-400 hover:text-blue-300">Upload a file</Link>
                      </td>
                    </tr>
                  ) : (
                    filtered.map((d) => (
                      <motion.tr
                        key={d.detection_id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors group"
                      >
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            checked={selected.has(d.detection_id)}
                            onChange={() => toggleSelect(d.detection_id)}
                            className="rounded border-slate-600 bg-slate-700 text-blue-500"
                          />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 bg-slate-700 rounded flex items-center justify-center flex-shrink-0">
                              {d.file_type === 'video' ? (
                                <FileVideo className="w-3.5 h-3.5 text-slate-400" />
                              ) : (
                                <FileImage className="w-3.5 h-3.5 text-slate-400" />
                              )}
                            </div>
                            <span className="text-slate-200 truncate max-w-[140px]">
                              {d.original_filename ?? `#${d.detection_id}`}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 hidden sm:table-cell">
                          <Badge variant="default" size="sm">{d.file_type}</Badge>
                        </td>
                        <td className="px-4 py-3">
                          {d.ai_probability != null ? (
                            <span className={`font-bold ${getProbabilityColor(d.ai_probability)}`}>
                              {formatProbability(d.ai_probability)}
                            </span>
                          ) : (
                            <span className="text-slate-500">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 hidden md:table-cell text-slate-400">
                          {formatDate(d.uploaded_at)}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={STATUS_VARIANTS[d.processing_status] ?? 'default'}>
                            {d.processing_status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-end gap-1">
                            <Link
                              to={`/results/${d.detection_id}`}
                              className="p-1.5 text-slate-500 hover:text-blue-400 transition-colors rounded"
                              title="View"
                            >
                              <Eye className="w-4 h-4" />
                            </Link>
                            <button
                              onClick={() => handleDelete(d.detection_id)}
                              disabled={deletingIds.has(d.detection_id)}
                              className="p-1.5 text-slate-500 hover:text-red-400 transition-colors rounded disabled:opacity-50"
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </motion.tr>
                    ))
                  )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-slate-400">
            Page {page + 1} of {pages} ({total} total)
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="p-2 text-slate-400 hover:text-white disabled:opacity-30 rounded-lg"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}
              disabled={page >= pages - 1}
              className="p-2 text-slate-400 hover:text-white disabled:opacity-30 rounded-lg"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </Layout>
  )
}
