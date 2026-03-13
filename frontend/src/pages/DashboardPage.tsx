import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Upload, Activity, Layers, TrendingUp, Eye, ArrowRight } from 'lucide-react'
import Layout from '../components/Layout'
import { Skeleton } from '../components/LoadingStates'
import Badge from '../components/Badge'
import api from '../utils/api'
import { useAuth } from '../hooks/useAuth'
import { formatDate, formatProbability, getProbabilityColor } from '../utils/formatting'
import { TIER_QUOTAS } from '../utils/constants'

interface Detection {
  detection_id: number
  file_type: string
  original_filename: string
  processing_status: string
  ai_probability: number | null
  uploaded_at: string
}

interface Stats {
  scansThisMonth: number
  processing: number
  batches: number
  avgProbability: number | null
}

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.4 } }),
}

export default function DashboardPage() {
  const { user, refreshUser } = useAuth()
  const [detections, setDetections] = useState<Detection[]>([])
  const [stats, setStats] = useState<Stats>({ scansThisMonth: 0, processing: 0, batches: 0, avgProbability: null })
  const [loading, setLoading] = useState(true)
  const [quotaUsed, setQuotaUsed] = useState(0)
  const [quotaTotal, setQuotaTotal] = useState(100)

  useEffect(() => {
    const load = async () => {
      try {
        await refreshUser()
        const [detectRes, batchRes] = await Promise.all([
          api.get('/detections?limit=5'),
          api.get('/batches?limit=5').catch(() => ({ data: { batches: [], total: 0 } })),
        ])

        const allDetections: Detection[] = detectRes.data.detections ?? []
        const total: number = detectRes.data.total ?? 0
        const batchTotal: number = batchRes.data.total ?? 0

        const processing = allDetections.filter((d) => d.processing_status === 'processing' || d.processing_status === 'pending').length
        const completed = allDetections.filter((d) => d.ai_probability != null)
        const avg = completed.length > 0
          ? completed.reduce((s, d) => s + (d.ai_probability ?? 0), 0) / completed.length
          : null

        setDetections(allDetections.slice(0, 5))
        setStats({ scansThisMonth: total, processing, batches: batchTotal, avgProbability: avg })

        // Quota — read fresh from API response, not stale closure
        const meRes = await api.get('/auth/me').catch(() => null)
        const freshTier = (meRes?.data?.tier ?? meRes?.data?.subscription_tier ?? 'free') as string
        const rawLimit = TIER_QUOTAS[freshTier as keyof typeof TIER_QUOTAS] ?? TIER_QUOTAS.free
        setQuotaTotal(rawLimit < 0 ? 999999 : rawLimit)
        setQuotaUsed(total)
      } catch {
        // ignore
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const statCards = [
    { icon: <Activity className="w-5 h-5" />, label: 'Scans this month', value: stats.scansThisMonth, color: 'blue' },
    { icon: <Upload className="w-5 h-5" />, label: 'Processing now', value: stats.processing, color: 'yellow' },
    { icon: <Layers className="w-5 h-5" />, label: 'Batches', value: stats.batches, color: 'purple' },
    { icon: <TrendingUp className="w-5 h-5" />, label: 'Avg AI probability', value: stats.avgProbability != null ? `${Math.round(stats.avgProbability * 100)}%` : '—', color: 'green' },
  ]

  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-500/20 text-blue-400',
    yellow: 'bg-yellow-500/20 text-yellow-400',
    purple: 'bg-purple-500/20 text-purple-400',
    green: 'bg-green-500/20 text-green-400',
  }

  return (
    <Layout quotaUsed={quotaUsed} quotaTotal={quotaTotal}>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">
          Welcome back, {user?.full_name?.split(' ')[0] ?? 'there'}! 👋
        </h1>
        <p className="text-slate-400 text-sm mt-1">Here's what's happening with your detections</p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((card, i) => (
          <motion.div
            key={card.label}
            custom={i}
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            className="bg-slate-800 rounded-xl border border-slate-700 p-5"
          >
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${colorClasses[card.color]}`}>
              {card.icon}
            </div>
            <div className="text-2xl font-bold text-white mb-1">
              {loading ? <Skeleton className="h-7 w-12" /> : card.value}
            </div>
            <div className="text-xs text-slate-400">{card.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Recent detections */}
      <div className="bg-slate-800 rounded-xl border border-slate-700">
        <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
          <h2 className="font-semibold text-white">Recent Detections</h2>
          <Link to="/history" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1">
            View all <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {loading ? (
          <div className="p-6 space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex gap-3 items-center">
                <Skeleton className="w-8 h-8 rounded" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-3 w-24" />
                </div>
              </div>
            ))}
          </div>
        ) : detections.length === 0 ? (
          <div className="py-16 text-center">
            <div className="w-16 h-16 bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <Upload className="w-8 h-8 text-slate-500" />
            </div>
            <h3 className="text-slate-300 font-medium mb-2">No detections yet</h3>
            <p className="text-slate-500 text-sm mb-4">Upload a file to get started</p>
            <Link
              to="/upload"
              className="inline-flex px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              Upload Now
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-700/50">
            {detections.map((d) => (
              <div key={d.detection_id} className="px-6 py-4 flex items-center gap-4 hover:bg-slate-700/30 transition-colors group">
                <div className="w-9 h-9 bg-slate-700 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-bold text-slate-300 uppercase">{d.file_type.slice(0, 3)}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{d.original_filename ?? `Detection #${d.detection_id}`}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{formatDate(d.uploaded_at)}</p>
                </div>
                <div className="flex items-center gap-3">
                  {d.ai_probability != null ? (
                    <span className={`text-sm font-bold ${getProbabilityColor(d.ai_probability)}`}>
                      {formatProbability(d.ai_probability)}
                    </span>
                  ) : (
                    <Badge variant={d.processing_status === 'error' ? 'error' : 'info'}>
                      {d.processing_status}
                    </Badge>
                  )}
                  <Link
                    to={`/results/${d.detection_id}`}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 text-slate-400 hover:text-white rounded"
                  >
                    <Eye className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick upload */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="mt-6 bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/20 rounded-xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4"
      >
        <div>
          <h3 className="font-semibold text-white mb-1">Ready to detect deepfakes?</h3>
          <p className="text-slate-400 text-sm">Upload any image or video for instant AI analysis</p>
        </div>
        <Link
          to="/upload"
          className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-all hover:scale-105 whitespace-nowrap"
        >
          <Upload className="w-4 h-4" />
          Upload File
        </Link>
      </motion.div>
    </Layout>
  )
}
