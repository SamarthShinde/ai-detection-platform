import React from 'react'

interface CardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
  onClick?: () => void
}

function Card({ children, className = '', hover = false, onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={[
        'bg-slate-800 rounded-xl border border-slate-700 p-6',
        hover
          ? 'transition-all duration-200 hover:border-slate-600 hover:shadow-lg hover:shadow-black/20 hover:-translate-y-0.5'
          : '',
        onClick ? 'cursor-pointer' : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {children}
    </div>
  )
}

export default Card
