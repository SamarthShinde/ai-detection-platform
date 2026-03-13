import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, Loader2 } from 'lucide-react'
import api from '../utils/api'
import { useAuthStore } from '../store/authStore'
import { useToast } from '../components/Toast'

export default function VerificationPage() {
  const [digits, setDigits] = useState<string[]>(Array(6).fill(''))
  const [loading, setLoading] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)
  const inputRefs = useRef<Array<HTMLInputElement | null>>(Array(6).fill(null))
  const navigate = useNavigate()
  const { setToken, setUser } = useAuthStore()
  const { success, error } = useToast()

  const email = localStorage.getItem('pending_verify_email') ?? ''

  // Guard: redirect to /auth if accessed without a pending verification email
  useEffect(() => {
    if (!email) navigate('/auth')
  }, [email, navigate])

  // Resend cooldown timer
  useEffect(() => {
    if (resendCooldown <= 0) return
    const timer = setTimeout(() => setResendCooldown((c) => c - 1), 1000)
    return () => clearTimeout(timer)
  }, [resendCooldown])

  const handleDigitChange = (index: number, value: string) => {
    const cleaned = value.replace(/\D/g, '').slice(-1)
    const newDigits = [...digits]
    newDigits[index] = cleaned
    setDigits(newDigits)

    if (cleaned && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }

    // Auto-submit when all filled
    if (cleaned && newDigits.every(Boolean)) {
      handleVerify(newDigits.join(''))
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    const newDigits = [...digits]
    for (let i = 0; i < pasted.length; i++) newDigits[i] = pasted[i]
    setDigits(newDigits)
    if (pasted.length === 6) handleVerify(pasted)
    e.preventDefault()
  }

  const handleVerify = async (otp: string) => {
    if (otp.length !== 6 || loading) return
    setLoading(true)
    try {
      await api.post('/auth/verify-email', { email, otp })
      success('Email verified!', 'Redirecting to dashboard...')
      localStorage.removeItem('pending_verify_email')

      // Try to login with stored credentials (if available)
      const stored = localStorage.getItem('pending_credentials')
      if (stored) {
        const { email: e, password: p } = JSON.parse(stored)
        const r = await api.post('/auth/login', { email: e, password: p })
        setToken(r.data.access_token)
        const profile = await api.get('/auth/me', { headers: { Authorization: `Bearer ${r.data.access_token}` } })
        setUser(profile.data)
        localStorage.removeItem('pending_credentials')
        navigate('/dashboard')
      } else {
        navigate('/auth')
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Invalid code'
      error('Verification failed', msg)
      setDigits(Array(6).fill(''))
      inputRefs.current[0]?.focus()
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (resendCooldown > 0) return
    try {
      await api.post('/auth/resend-otp', { email })
      success('Code sent', 'Check your email for a new verification code')
      setResendCooldown(60)
    } catch {
      error('Failed to resend', 'Please try again later')
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="bg-slate-800 rounded-2xl border border-slate-700 p-8 shadow-2xl text-center">
          <div className="w-16 h-16 bg-blue-600/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <Shield className="w-8 h-8 text-blue-400" />
          </div>

          <h1 className="text-2xl font-bold text-white mb-2">Verify Your Email</h1>
          <p className="text-slate-400 text-sm mb-1">
            Enter the 6-digit code sent to
          </p>
          <p className="text-white font-medium text-sm mb-8">{email || 'your email'}</p>

          {/* OTP inputs */}
          <div className="flex gap-2 justify-center mb-6">
            {digits.map((digit, i) => (
              <input
                key={i}
                ref={(el) => { inputRefs.current[i] = el }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleDigitChange(i, e.target.value)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                onPaste={handlePaste}
                className="w-12 h-14 text-center text-xl font-bold bg-slate-700 border-2 border-slate-600 focus:border-blue-500 rounded-xl text-white outline-none transition-colors"
              />
            ))}
          </div>

          {/* Submit button */}
          <button
            onClick={() => handleVerify(digits.join(''))}
            disabled={digits.some((d) => !d) || loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold rounded-xl transition-all mb-4 flex items-center justify-center gap-2"
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            Verify Email
          </button>

          {/* Resend */}
          <p className="text-sm text-slate-400">
            Didn't get a code?{' '}
            <button
              onClick={handleResend}
              disabled={resendCooldown > 0}
              className="text-blue-400 hover:text-blue-300 disabled:text-slate-500 disabled:cursor-not-allowed transition-colors"
            >
              {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend'}
            </button>
          </p>
        </div>
      </motion.div>
    </div>
  )
}
