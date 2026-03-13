import { useState, useCallback, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, X, FileVideo, FileImage, Loader2, Layers, ChevronRight } from 'lucide-react'
import Layout from '../components/Layout'
import { useToast } from '../components/Toast'
import api from '../utils/api'
import { ACCEPTED_IMAGE_TYPES, ACCEPTED_VIDEO_TYPES, MAX_FILE_SIZE } from '../utils/constants'
import { formatFileSize } from '../utils/formatting'

interface FileItem {
  id: string
  file: File
  type: 'image' | 'video'
  preview?: string
  progress: number
  status: 'pending' | 'uploading' | 'done' | 'error'
  detectionId?: number
  error?: string
}

function getFileType(file: File): 'image' | 'video' | null {
  if (ACCEPTED_IMAGE_TYPES.includes(file.type)) return 'image'
  if (ACCEPTED_VIDEO_TYPES.includes(file.type)) return 'video'
  return null
}

export default function UploadPage() {
  const [files, setFiles] = useState<FileItem[]>([])
  const [batchMode, setBatchMode] = useState(false)
  const [batchName, setBatchName] = useState('')
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const previewUrlsRef = useRef<string[]>([])
  const navigate = useNavigate()
  const { success, error, info } = useToast()

  // Clean up all blob URLs when the component unmounts
  useEffect(() => {
    return () => {
      previewUrlsRef.current.forEach((url) => URL.revokeObjectURL(url))
    }
  }, [])

  const addFiles = useCallback((rawFiles: FileList | File[]) => {
    const newItems: FileItem[] = []
    Array.from(rawFiles).forEach((file) => {
      if (file.size > MAX_FILE_SIZE) {
        error('File too large', `${file.name} exceeds 100MB limit`)
        return
      }
      const type = getFileType(file)
      if (!type) {
        error('Unsupported file', `${file.name} is not a supported format`)
        return
      }
      const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`
      const preview = type === 'image' ? URL.createObjectURL(file) : undefined
      if (preview) previewUrlsRef.current.push(preview)
      newItems.push({ id, file, type, preview, progress: 0, status: 'pending' })
    })
    setFiles((prev) => [...prev, ...newItems])
  }, [error])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    addFiles(e.dataTransfer.files)
  }, [addFiles])

  const removeFile = (id: string) => {
    setFiles((prev) => {
      const item = prev.find((f) => f.id === id)
      if (item?.preview) URL.revokeObjectURL(item.preview)
      return prev.filter((f) => f.id !== id)
    })
  }

  const uploadFiles = async () => {
    const pending = files.filter((f) => f.status === 'pending')
    if (!pending.length) return
    setUploading(true)

    let batchId: number | undefined
    if (batchMode && batchName.trim() && pending.length > 1) {
      try {
        const r = await api.post('/batches', { batch_name: batchName.trim(), detection_ids: [] })
        batchId = r.data.batch_id ?? r.data.id
      } catch {
        // Batch creation optional
      }
    }

    const uploaded: number[] = []
    for (const item of pending) {
      setFiles((prev) => prev.map((f) => f.id === item.id ? { ...f, status: 'uploading' } : f))

      const formData = new FormData()
      formData.append('file', item.file)

      const endpoint = `/detections/${item.type}${batchId ? `?batch_id=${batchId}` : ''}`
      try {
        const r = await api.post(endpoint, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (e) => {
            const pct = Math.round(((e.loaded ?? 0) / (e.total ?? 1)) * 100)
            setFiles((prev) => prev.map((f) => f.id === item.id ? { ...f, progress: pct } : f))
          },
        })
        const detectionId: number = r.data.detection_id
        uploaded.push(detectionId)
        setFiles((prev) => prev.map((f) => f.id === item.id ? { ...f, status: 'done', progress: 100, detectionId } : f))
      } catch (err: unknown) {
        const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Upload failed'
        setFiles((prev) => prev.map((f) => f.id === item.id ? { ...f, status: 'error', error: msg } : f))
      }
    }

    setUploading(false)
    if (uploaded.length === 1) {
      success('Upload complete', 'Redirecting to results...')
      setTimeout(() => navigate(`/results/${uploaded[0]}`), 800)
    } else if (uploaded.length > 1) {
      info('Upload complete', `${uploaded.length} files uploaded. Redirecting to history...`)
      setTimeout(() => navigate('/history'), 1200)
    }
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Upload Files</h1>
          <p className="text-slate-400 text-sm mt-1">Drag and drop images or videos for deepfake detection</p>
        </div>

        {/* Batch mode toggle */}
        <div className="flex items-center gap-3 mb-6 bg-slate-800 rounded-xl border border-slate-700 p-4">
          <Layers className="w-4 h-4 text-slate-400" />
          <div className="flex-1">
            <p className="text-sm font-medium text-white">Batch upload mode</p>
            <p className="text-xs text-slate-400">Group multiple files into a single batch for tracking</p>
          </div>
          <button
            onClick={() => setBatchMode(!batchMode)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${batchMode ? 'bg-blue-600' : 'bg-slate-600'}`}
          >
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${batchMode ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>

        {batchMode && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="mb-4">
            <input
              type="text"
              value={batchName}
              onChange={(e) => setBatchName(e.target.value)}
              placeholder="Batch name (e.g. 'September dataset')"
              className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
            />
          </motion.div>
        )}

        {/* Drop zone */}
        <motion.div
          onDragEnter={() => setDragging(true)}
          onDragLeave={() => setDragging(false)}
          onDragOver={(e) => e.preventDefault()}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          animate={{ borderColor: dragging ? '#3B82F6' : '#334155' }}
          className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all mb-4 ${
            dragging ? 'bg-blue-500/10 border-blue-500' : 'border-slate-600 hover:border-slate-500 bg-slate-800/50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={[...ACCEPTED_IMAGE_TYPES, ...ACCEPTED_VIDEO_TYPES].join(',')}
            onChange={(e) => e.target.files && addFiles(e.target.files)}
            className="hidden"
          />
          <motion.div animate={{ scale: dragging ? 1.1 : 1 }} transition={{ type: 'spring', stiffness: 300 }}>
            <Upload className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          </motion.div>
          <p className="text-lg font-medium text-white mb-2">
            {dragging ? 'Drop files here' : 'Drop files here or click to select'}
          </p>
          <p className="text-sm text-slate-400">
            Images: JPEG, PNG, WebP &bull; Videos: MP4, AVI, MOV &bull; Max 100MB
          </p>
        </motion.div>

        {/* File list */}
        <AnimatePresence>
          {files.map((item) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="bg-slate-800 rounded-xl border border-slate-700 p-4 mb-3 flex items-center gap-4"
            >
              {/* Preview / icon */}
              <div className="w-12 h-12 flex-shrink-0 rounded-lg overflow-hidden bg-slate-700 flex items-center justify-center">
                {item.preview ? (
                  <img src={item.preview} alt="" className="w-full h-full object-cover" />
                ) : item.type === 'video' ? (
                  <FileVideo className="w-6 h-6 text-slate-400" />
                ) : (
                  <FileImage className="w-6 h-6 text-slate-400" />
                )}
              </div>

              {/* File info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{item.file.name}</p>
                <p className="text-xs text-slate-400">{formatFileSize(item.file.size)} · {item.type}</p>
                {item.status === 'uploading' && (
                  <div className="mt-2">
                    <div className="h-1.5 bg-slate-600 rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-blue-500 rounded-full"
                        animate={{ width: `${item.progress}%` }}
                        transition={{ duration: 0.3 }}
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">{item.progress}%</p>
                  </div>
                )}
                {item.status === 'error' && (
                  <p className="text-xs text-red-400 mt-1">{item.error}</p>
                )}
                {item.status === 'done' && (
                  <p className="text-xs text-green-400 mt-1">Uploaded successfully</p>
                )}
              </div>

              {/* Status / remove */}
              <div className="flex items-center gap-2">
                {item.status === 'done' && item.detectionId && (
                  <button
                    onClick={() => navigate(`/results/${item.detectionId}`)}
                    className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                  >
                    View <ChevronRight className="w-3 h-3" />
                  </button>
                )}
                {item.status !== 'uploading' && item.status !== 'done' && (
                  <button onClick={() => removeFile(item.id)} className="p-1 text-slate-500 hover:text-red-400 transition-colors">
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Upload button */}
        {files.some((f) => f.status === 'pending') && (
          <motion.button
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            onClick={uploadFiles}
            disabled={uploading}
            className="w-full py-3.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 mt-2"
          >
            {uploading ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Uploading...</>
            ) : (
              <><Upload className="w-4 h-4" /> Upload {files.filter((f) => f.status === 'pending').length} file(s)</>
            )}
          </motion.button>
        )}
      </div>
    </Layout>
  )
}
