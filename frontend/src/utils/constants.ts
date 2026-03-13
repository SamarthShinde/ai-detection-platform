export const API_BASE_URL = 'http://localhost:8000'

export const ROUTES = {
  LANDING: '/',
  AUTH: '/auth',
  VERIFY: '/verify',
  DASHBOARD: '/dashboard',
  UPLOAD: '/upload',
  RESULTS: '/results',
  HISTORY: '/history',
  BATCH: '/batch',
  API_KEYS: '/api-keys',
  SETTINGS: '/settings',
}

export const FILE_TYPES = {
  IMAGE: 'image',
  VIDEO: 'video',
}

export const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100MB

export const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
export const ACCEPTED_VIDEO_TYPES = ['video/mp4', 'video/avi', 'video/quicktime']

export const ACCEPTED_ALL_TYPES = [...ACCEPTED_IMAGE_TYPES, ...ACCEPTED_VIDEO_TYPES]

export const QUOTA_COLORS = {
  safe: 'text-green-400',
  warning: 'text-yellow-400',
  danger: 'text-red-400',
}

export const TIER_QUOTAS = {
  free: 10,
  pro: 500,
  enterprise: -1, // unlimited
}

export const DETECTION_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
}

export const PROBABILITY_THRESHOLDS = {
  LOW: 30,
  MEDIUM: 70,
}

export const POLL_INTERVAL_MS = 2000
export const BATCH_POLL_INTERVAL_MS = 5000
