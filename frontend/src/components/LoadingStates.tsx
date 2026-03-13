interface SkeletonProps {
  className?: string
  variant?: 'text' | 'card' | 'circle' | 'block'
  lines?: number
}

export function Skeleton({ className = '', variant = 'block', lines = 1 }: SkeletonProps) {
  if (variant === 'text') {
    return (
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`h-4 bg-slate-700 rounded animate-pulse ${i === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full'} ${className}`}
          />
        ))}
      </div>
    )
  }

  if (variant === 'card') {
    return (
      <div className={`bg-slate-800 rounded-xl border border-slate-700 p-6 space-y-4 ${className}`}>
        <div className="h-4 w-1/3 bg-slate-700 rounded animate-pulse" />
        <div className="h-8 w-1/2 bg-slate-700 rounded animate-pulse" />
        <div className="h-3 w-full bg-slate-700 rounded animate-pulse" />
      </div>
    )
  }

  if (variant === 'circle') {
    return <div className={`rounded-full bg-slate-700 animate-pulse ${className}`} />
  }

  return <div className={`bg-slate-700 rounded animate-pulse ${className}`} />
}

export function Spinner({ size = 'md', className = '' }: { size?: 'sm' | 'md' | 'lg'; className?: string }) {
  const sizeMap = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8' }
  return (
    <svg
      className={`animate-spin text-blue-500 ${sizeMap[size]} ${className}`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}

export function PageLoader() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="text-center space-y-4">
        <Spinner size="lg" />
        <p className="text-slate-400 text-sm">Loading...</p>
      </div>
    </div>
  )
}

export function TableRowSkeleton({ cols = 5 }: { cols?: number }) {
  return (
    <tr className="border-b border-slate-700/50">
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-slate-700 rounded animate-pulse" style={{ width: `${60 + Math.random() * 40}%` }} />
        </td>
      ))}
    </tr>
  )
}
