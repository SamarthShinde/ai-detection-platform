interface BadgeProps {
  children: React.ReactNode
  variant?: 'success' | 'warning' | 'error' | 'info' | 'default' | 'purple'
  size?: 'sm' | 'md'
  className?: string
}

const variantClasses: Record<NonNullable<BadgeProps['variant']>, string> = {
  success: 'bg-green-500/20 text-green-400 border-green-500/30',
  warning: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  error: 'bg-red-500/20 text-red-400 border-red-500/30',
  info: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  default: 'bg-slate-700 text-slate-300 border-slate-600',
  purple: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
}

export default function Badge({ children, variant = 'default', size = 'sm', className = '' }: BadgeProps) {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm'
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border font-medium ${variantClasses[variant]} ${sizeClasses} ${className}`}
    >
      {children}
    </span>
  )
}
