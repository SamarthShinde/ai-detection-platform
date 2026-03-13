import { PROBABILITY_THRESHOLDS } from './constants'

/**
 * Format a date string or Date object to a human-readable string.
 */
export function formatDate(date: string | Date, options?: Intl.DateTimeFormatOptions): string {
  const d = typeof date === 'string' ? new Date(date) : date
  if (isNaN(d.getTime())) return 'Invalid date'

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    ...options,
  }
  return d.toLocaleDateString('en-US', defaultOptions)
}

/**
 * Format file size in bytes to human-readable string.
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const value = bytes / Math.pow(k, i)
  return `${value % 1 === 0 ? value : value.toFixed(1)} ${units[i]}`
}

/**
 * Format a probability value (0–1 or 0–100) as a percentage string.
 */
export function formatProbability(value: number): string {
  const percentage = value <= 1 ? value * 100 : value
  return `${Math.round(percentage)}%`
}

/**
 * Get Tailwind text color class based on probability value.
 */
export function getProbabilityColor(value: number): string {
  const percentage = value <= 1 ? value * 100 : value
  if (percentage < PROBABILITY_THRESHOLDS.LOW) return 'text-green-400'
  if (percentage < PROBABILITY_THRESHOLDS.MEDIUM) return 'text-yellow-400'
  return 'text-red-400'
}

/**
 * Get Tailwind background color class based on probability value.
 */
export function getProbabilityBgColor(value: number): string {
  const percentage = value <= 1 ? value * 100 : value
  if (percentage < PROBABILITY_THRESHOLDS.LOW) return 'bg-green-400'
  if (percentage < PROBABILITY_THRESHOLDS.MEDIUM) return 'bg-yellow-400'
  return 'bg-red-400'
}

/**
 * Get human-readable label for a probability value.
 */
export function getProbabilityLabel(value: number): string {
  const percentage = value <= 1 ? value * 100 : value
  if (percentage < PROBABILITY_THRESHOLDS.LOW) return 'Likely Real'
  if (percentage < PROBABILITY_THRESHOLDS.MEDIUM) return 'Uncertain'
  return 'Likely AI-Generated'
}

/**
 * Format duration in seconds to human-readable string.
 */
export function formatDuration(seconds: number): string {
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}

/**
 * Format processing time in milliseconds to readable string.
 */
export function formatProcessingTime(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  return formatDuration(ms / 1000)
}

/**
 * Truncate a filename to a max length keeping extension.
 */
export function truncateFilename(filename: string, maxLength: number = 30): string {
  if (filename.length <= maxLength) return filename
  const lastDot = filename.lastIndexOf('.')
  const ext = lastDot >= 0 ? filename.slice(lastDot) : ''
  const baseName = lastDot >= 0 ? filename.slice(0, lastDot) : filename
  const truncatedBase = baseName.slice(0, maxLength - ext.length - 3) + '...'
  return truncatedBase + ext
}

/**
 * Get relative time string (e.g., "2 hours ago").
 */
export function getRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffSecs / 60)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffSecs < 60) return 'just now'
  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`
  return formatDate(d, { year: 'numeric', month: 'short', day: 'numeric' })
}
