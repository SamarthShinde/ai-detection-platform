import { motion } from 'framer-motion'

interface ProgressBarProps {
  value: number // 0-100
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'auto'
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
  animated?: boolean
}

function getAutoColor(value: number): string {
  if (value < 50) return 'bg-green-500'
  if (value < 80) return 'bg-yellow-500'
  return 'bg-red-500'
}

const colorClasses: Record<string, string> = {
  blue: 'bg-blue-500',
  green: 'bg-green-500',
  yellow: 'bg-yellow-500',
  red: 'bg-red-500',
}

const sizeClasses: Record<string, string> = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
}

export default function ProgressBar({
  value,
  color = 'blue',
  showLabel = false,
  size = 'md',
  className = '',
  animated = true,
}: ProgressBarProps) {
  const clampedValue = Math.min(100, Math.max(0, value))
  const barColor = color === 'auto' ? getAutoColor(clampedValue) : colorClasses[color]

  return (
    <div className={`w-full ${className}`}>
      {showLabel && (
        <div className="flex justify-between mb-1">
          <span className="text-xs text-slate-400">Progress</span>
          <span className="text-xs font-medium text-slate-200">{clampedValue}%</span>
        </div>
      )}
      <div className={`w-full bg-slate-700 rounded-full overflow-hidden ${sizeClasses[size]}`}>
        <motion.div
          className={`h-full rounded-full ${barColor}`}
          initial={animated ? { width: 0 } : { width: `${clampedValue}%` }}
          animate={{ width: `${clampedValue}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </div>
    </div>
  )
}
