import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Download, RefreshCw, ArrowLeft, Clock, Shield, AlertTriangle, CheckCircle } from 'lucide-react'
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts'
import Layout from '../components/Layout'
import { Skeleton, Spinner } from '../components/LoadingStates'
import Badge from '../components/Badge'
import ProgressBar from '../components/ProgressBar'
import { useToast } from '../components/Toast'
import api from '../utils/api'
import { formatDate, formatProcessingTime, getProbabilityLabel } from '../utils/formatting'

interface DetectionResult {
  detection_id: number
  processing_status: string
  progress_percent?: number
  file_hash?: string
  file_type?: string
  ai_probability?: number
  confidence_score?: number
  detection_methods?: string
  processing_time_ms?: number
  uploaded_at?: string
  completed_at?: string
  error_message?: string
  result_json?: {
    model_scores?: Record<string, number>
    artifacts_found?: string[]
    frames?: Array<{ frame: number; timestamp: number; ai_probability: number }>
  }
}

function ProbabilityMeter({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color = pct < 30 ? '#10B981' : pct < 70 ? '#F59E0B' : '#EF4444'
  const label = getProbabilityLabel(value)

  const data = [{ name: 'AI Probability', value: pct, fill: color }]

  return (
    <div className="relative flex flex-col items-center">
      <div className="w-48 h-48">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="65%"
            outerRadius="90%"
            startAngle={90}
            endAngle={-270}
            data={data}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar dataKey="value" background={{ fill: '#1E293B' }} />
          </RadialBarChart>
        </ResponsiveContainer>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold" style={{ color }}>{pct}%</span>
          <span className="text-xs text-slate-400 mt-1">AI Probability</span>
        </div>
      </div>
      <div className="text-center mt-2">
        <span className="text-sm font-semibold" style={{ color }}>{label}</span>
      </div>
    </div>
  )
}

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>()
  const [result, setResult] = useState<DetectionResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [retrying, setRetrying] = useState(false)
  const { error, success } = useToast()

  const fetchResult = useCallback(async () => {
    if (!id) return
    try {
      const r = await api.get(`/detections/${id}`)
      setResult(r.data)
      return r.data.processing_status
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Failed to load result'
      error('Error', msg)
      return 'error'
    }
  }, [id, error])

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>
    const load = async () => {
      const status = await fetchResult()
      setLoading(false)
      if (status === 'pending' || status === 'processing') {
        interval = setInterval(async () => {
          const s = await fetchResult()
          if (s !== 'pending' && s !== 'processing') clearInterval(interval)
        }, 2000)
      }
    }
    load()
    return () => clearInterval(interval)
  }, [fetchResult])

  const handleRetry = async () => {
    if (!id) return
    setRetrying(true)
    try {
      await api.post(`/detections/${id}/retry`)
      success('Retry queued', 'Detection has been re-queued for processing')
      await fetchResult()
    } catch {
      error('Retry failed', 'Please try again later')
    } finally {
      setRetrying(false)
    }
  }

  const handleDownloadJSON = () => {
    if (!result) return
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `detection-${id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const isProcessing = result?.processing_status === 'pending' || result?.processing_status === 'processing'

  return (
    <Layout>
      <div className="max-w-3xl mx-auto">
        {/* Back */}
        <Link to="/history" className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-white mb-6 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Back to history
        </Link>

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Detection #{id}</h1>
        </div>

        {loading ? (
          <div className="space-y-4">
            <Skeleton variant="card" className="h-48" />
            <Skeleton variant="card" className="h-32" />
          </div>
        ) : isProcessing ? (
          /* Processing state */
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-slate-800 rounded-2xl border border-slate-700 p-10 text-center">
            <Spinner size="lg" className="mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">Analyzing your file...</h2>
            <p className="text-slate-400 text-sm mb-6">Our AI ensemble is examining every pixel</p>
            {result?.progress_percent != null && (
              <div className="max-w-xs mx-auto">
                <ProgressBar value={result.progress_percent} color="blue" showLabel animated />
              </div>
            )}
            <p className="text-xs text-slate-500 mt-4">Results will appear automatically</p>
          </motion.div>
        ) : result?.processing_status === 'error' ? (
          /* Error state */
          <div className="bg-slate-800 rounded-2xl border border-red-500/30 p-8 text-center">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">Detection Failed</h2>
            <p className="text-slate-400 text-sm mb-6">{result.error_message ?? 'An unknown error occurred'}</p>
            <button
              onClick={handleRetry}
              disabled={retrying}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors"
            >
              {retrying ? <Spinner size="sm" /> : <RefreshCw className="w-4 h-4" />}
              Retry Detection
            </button>
          </div>
        ) : result?.processing_status === 'completed' ? (
          /* Completed state */
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
            {/* Main result card */}
            <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6">
              <div className="flex flex-col md:flex-row gap-8 items-center">
                {/* Probability meter */}
                {result.ai_probability != null && (
                  <ProbabilityMeter value={result.ai_probability} />
                )}

                {/* Stats */}
                <div className="flex-1 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    {result.confidence_score != null && (
                      <div className="bg-slate-700/50 rounded-xl p-4">
                        <p className="text-xs text-slate-400 mb-1">Confidence Score</p>
                        <p className="text-2xl font-bold text-white">{Math.round(result.confidence_score * 100)}%</p>
                        <ProgressBar value={result.confidence_score * 100} color="blue" size="sm" className="mt-2" />
                      </div>
                    )}
                    {result.processing_time_ms != null && (
                      <div className="bg-slate-700/50 rounded-xl p-4">
                        <p className="text-xs text-slate-400 mb-1">Processing Time</p>
                        <p className="text-2xl font-bold text-white">{formatProcessingTime(result.processing_time_ms)}</p>
                        <div className="flex items-center gap-1 mt-2">
                          <Clock className="w-3 h-3 text-slate-500" />
                          <span className="text-xs text-slate-500">analysis time</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* File info */}
                  <div className="text-sm text-slate-400 space-y-1">
                    {result.file_type && (
                      <div className="flex items-center gap-2">
                        <span className="text-slate-500">Type:</span>
                        <Badge variant="info">{result.file_type}</Badge>
                      </div>
                    )}
                    {result.uploaded_at && (
                      <div className="flex items-center gap-2">
                        <span className="text-slate-500">Uploaded:</span>
                        <span className="text-slate-300">{formatDate(result.uploaded_at)}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Model scores */}
            {result.result_json?.model_scores && Object.keys(result.result_json.model_scores).length > 0 && (
              <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6">
                <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-400" />
                  Model Breakdown
                </h3>
                <div className="space-y-3">
                  {Object.entries(result.result_json.model_scores).map(([model, score]) => (
                    <div key={model}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-slate-300 capitalize">{model.replace(/_/g, ' ')}</span>
                        <span className="font-medium text-white">{Math.round((score as number) * 100)}%</span>
                      </div>
                      <ProgressBar value={(score as number) * 100} color="auto" size="sm" />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Artifacts */}
            {result.result_json?.artifacts_found && result.result_json.artifacts_found.length > 0 && (
              <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6">
                <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-yellow-400" />
                  Artifacts Detected
                </h3>
                <div className="flex flex-wrap gap-2">
                  {result.result_json.artifacts_found.map((a) => (
                    <Badge key={a} variant="warning">{a}</Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Detection methods */}
            {result.detection_methods && (
              <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6">
                <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  Detection Methods
                </h3>
                <p className="text-sm text-slate-400">{result.detection_methods}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleDownloadJSON}
                className="flex items-center gap-2 px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-xl transition-colors"
              >
                <Download className="w-4 h-4" />
                Export JSON
              </button>
              <Link
                to="/upload"
                className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-colors"
              >
                <Shield className="w-4 h-4" />
                Analyze Another
              </Link>
            </div>
          </motion.div>
        ) : null}
      </div>
    </Layout>
  )
}
