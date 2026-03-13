import React, { useState } from 'react'
import { Eye, EyeOff, Check } from 'lucide-react'
import { validatePasswordStrength, type PasswordStrength } from '../utils/validation'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
  required?: boolean
  className?: string
  containerClassName?: string
}

const strengthColors: Record<PasswordStrength, string> = {
  weak: 'bg-red-500',
  medium: 'bg-yellow-500',
  strong: 'bg-green-500',
}

const strengthLabels: Record<PasswordStrength, string> = {
  weak: 'Weak',
  medium: 'Medium',
  strong: 'Strong',
}

const strengthTextColors: Record<PasswordStrength, string> = {
  weak: 'text-red-400',
  medium: 'text-yellow-400',
  strong: 'text-green-400',
}

function PasswordStrengthBar({ password }: { password: string }) {
  const strength = validatePasswordStrength(password)
  const widths = { weak: 'w-1/3', medium: 'w-2/3', strong: 'w-full' }

  return (
    <div className="mt-1.5">
      <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${strengthColors[strength]} ${widths[strength]}`}
        />
      </div>
      <p className={`text-xs mt-1 ${strengthTextColors[strength]}`}>
        Password strength: {strengthLabels[strength]}
      </p>
    </div>
  )
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      hint,
      type = 'text',
      required,
      className = '',
      containerClassName = '',
      value,
      onChange,
      ...props
    },
    ref
  ) => {
    const [showPassword, setShowPassword] = useState(false)

    const isPassword = type === 'password'
    const inputType = isPassword ? (showPassword ? 'text' : 'password') : type
    const hasValue = typeof value === 'string' ? value.length > 0 : false
    const isValid = hasValue && !error

    return (
      <div className={`flex flex-col gap-1 ${containerClassName}`}>
        {label && (
          <label className="text-sm font-medium text-slate-300">
            {label}
            {required && <span className="text-red-400 ml-1">*</span>}
          </label>
        )}

        <div className="relative">
          <input
            ref={ref}
            type={inputType}
            value={value}
            onChange={onChange}
            className={[
              'w-full bg-slate-700/50 border rounded-lg px-3 py-2.5 text-slate-100 text-sm placeholder:text-slate-500 transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500',
              error
                ? 'border-red-500/60 bg-red-500/5'
                : isValid
                  ? 'border-green-500/40 bg-green-500/5'
                  : 'border-slate-600',
              (isPassword || isValid) ? 'pr-10' : '',
              className,
            ]
              .filter(Boolean)
              .join(' ')}
            {...props}
          />

          {/* Right icons */}
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
            {isPassword && (
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="text-slate-400 hover:text-slate-200 transition-colors"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            )}
            {!isPassword && isValid && <Check className="w-4 h-4 text-green-400" />}
          </div>
        </div>

        {/* Password strength indicator */}
        {isPassword && hasValue && !error && (
          <PasswordStrengthBar password={value as string} />
        )}

        {/* Error message */}
        {error && <p className="text-xs text-red-400 mt-0.5">{error}</p>}

        {/* Hint message */}
        {hint && !error && <p className="text-xs text-slate-500">{hint}</p>}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input
