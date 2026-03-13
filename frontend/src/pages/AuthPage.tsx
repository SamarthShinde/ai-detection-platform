import { useState, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, Eye, EyeOff, Loader2 } from 'lucide-react'
import { useAuth, type TwoFactorChallenge } from '../hooks/useAuth'
import { useToast } from '../components/Toast'
import { validatePasswordStrength } from '../utils/validation'

type Tab = 'signin' | 'signup'

function PasswordStrength({ password }: { password: string }) {
  if (!password) return null
  const strength = validatePasswordStrength(password)
  const config = {
    weak: { color: 'bg-red-500', width: 'w-1/3', label: 'Weak' },
    medium: { color: 'bg-yellow-500', width: 'w-2/3', label: 'Medium' },
    strong: { color: 'bg-green-500', width: 'w-full', label: 'Strong' },
  }[strength]

  return (
    <div className="mt-1.5">
      <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-300 ${config.color} ${config.width}`} />
      </div>
      <p className={`text-xs mt-1 ${strength === 'strong' ? 'text-green-400' : strength === 'medium' ? 'text-yellow-400' : 'text-red-400'}`}>
        {config.label} password
      </p>
    </div>
  )
}

function TwoFactorStep({
  challenge,
  onSuccess,
  onBack,
}: {
  challenge: TwoFactorChallenge
  onSuccess: () => void
  onBack: () => void
}) {
  const [digits, setDigits] = useState<string[]>(Array(6).fill(''))
  const [loading, setLoading] = useState(false)
  const inputRefs = useRef<Array<HTMLInputElement | null>>(Array(6).fill(null))
  const { verify2FA } = useAuth()
  const { success, error } = useToast()

  const handleChange = (index: number, value: string) => {
    const cleaned = value.replace(/\D/g, '').slice(-1)
    const next = [...digits]
    next[index] = cleaned
    setDigits(next)
    if (cleaned && index < 5) inputRefs.current[index + 1]?.focus()
    if (cleaned && next.every(Boolean)) submit(next.join(''))
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) inputRefs.current[index - 1]?.focus()
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    const next = [...digits]
    for (let i = 0; i < pasted.length; i++) next[i] = pasted[i]
    setDigits(next)
    if (pasted.length === 6) submit(pasted)
    e.preventDefault()
  }

  const submit = async (otp: string) => {
    if (otp.length !== 6 || loading) return
    setLoading(true)
    try {
      await verify2FA(otp, challenge.tempToken)
      success('Signed in!', 'Welcome back')
      onSuccess()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Invalid code'
      error('2FA failed', msg)
      setDigits(Array(6).fill(''))
      inputRefs.current[0]?.focus()
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center">
      <div className="w-14 h-14 bg-blue-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
        <Shield className="w-7 h-7 text-blue-400" />
      </div>
      <h3 className="text-lg font-bold text-white mb-1">Two-Factor Authentication</h3>
      <p className="text-sm text-slate-400 mb-6">
        Enter the 6-digit code sent to <span className="text-white">{challenge.email}</span>
      </p>
      <div className="flex gap-2 justify-center mb-6">
        {digits.map((d, i) => (
          <input
            key={i}
            ref={(el) => { inputRefs.current[i] = el }}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={d}
            onChange={(e) => handleChange(i, e.target.value)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            onPaste={handlePaste}
            className="w-11 h-14 text-center text-xl font-bold bg-slate-700 border-2 border-slate-600 focus:border-blue-500 rounded-xl text-white outline-none transition-colors"
          />
        ))}
      </div>
      <button
        onClick={() => submit(digits.join(''))}
        disabled={digits.some((d) => !d) || loading}
        className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 mb-3"
      >
        {loading && <Loader2 className="w-4 h-4 animate-spin" />}
        Verify
      </button>
      <button onClick={onBack} className="text-sm text-slate-400 hover:text-white transition-colors">
        ← Back to sign in
      </button>
    </motion.div>
  )
}

export default function AuthPage() {
  const [tab, setTab] = useState<Tab>('signin')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [registerSuccess, setRegisterSuccess] = useState(false)
  const [twoFactorChallenge, setTwoFactorChallenge] = useState<TwoFactorChallenge | null>(null)

  const [signInForm, setSignInForm] = useState({ email: '', password: '' })
  const [signUpForm, setSignUpForm] = useState({ email: '', password: '', full_name: '' })

  const navigate = useNavigate()
  const { login, register } = useAuth()
  const { success, error } = useToast()

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!signInForm.email || !signInForm.password) return
    setLoading(true)
    try {
      const result = await login(signInForm.email, signInForm.password)
      if (result && 'requires2fa' in result) {
        setTwoFactorChallenge(result)
        return
      }
      success('Welcome back!', 'Redirecting to dashboard...')
      navigate('/dashboard')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Invalid email or password'
      error('Sign in failed', msg)
    } finally {
      setLoading(false)
    }
  }

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!signUpForm.email || !signUpForm.password || !signUpForm.full_name) return
    setLoading(true)
    try {
      await register(signUpForm)
      setRegisterSuccess(true)
      localStorage.setItem('pending_verify_email', signUpForm.email)
      localStorage.setItem('pending_credentials', JSON.stringify({ email: signUpForm.email, password: signUpForm.password }))
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Registration failed'
      error('Sign up failed', msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 via-transparent to-purple-600/5 pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white">DeepDetect</span>
          </Link>
        </div>

        <div className="bg-slate-800 rounded-2xl border border-slate-700 p-8 shadow-2xl">
          {/* 2FA step */}
          {twoFactorChallenge ? (
            <TwoFactorStep
              challenge={twoFactorChallenge}
              onSuccess={() => navigate('/dashboard')}
              onBack={() => setTwoFactorChallenge(null)}
            />
          ) : (
            <>
              {/* Tabs */}
              <div className="flex bg-slate-700/50 rounded-xl p-1 mb-8">
                {(['signin', 'signup'] as Tab[]).map((t) => (
                  <button
                    key={t}
                    onClick={() => { setTab(t); setRegisterSuccess(false) }}
                    className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${
                      tab === t ? 'bg-slate-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    {t === 'signin' ? 'Sign In' : 'Sign Up'}
                  </button>
                ))}
              </div>

              {/* Sign In */}
              {tab === 'signin' && (
                <motion.form initial={{ opacity: 0 }} animate={{ opacity: 1 }} onSubmit={handleSignIn} className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
                    <input
                      type="email"
                      value={signInForm.email}
                      onChange={(e) => setSignInForm({ ...signInForm, email: e.target.value })}
                      placeholder="you@example.com"
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={signInForm.password}
                        onChange={(e) => setSignInForm({ ...signInForm, password: e.target.value })}
                        placeholder="••••••••"
                        className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors pr-12"
                        required
                      />
                      <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={loading || !signInForm.email || !signInForm.password}
                    className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2"
                  >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                    Sign In
                  </button>
                  <p className="text-center text-sm text-slate-400">
                    Don't have an account?{' '}
                    <button type="button" onClick={() => setTab('signup')} className="text-blue-400 hover:text-blue-300">Sign up</button>
                  </p>
                </motion.form>
              )}

              {/* Sign Up */}
              {tab === 'signup' && !registerSuccess && (
                <motion.form initial={{ opacity: 0 }} animate={{ opacity: 1 }} onSubmit={handleSignUp} className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">Full Name</label>
                    <input
                      type="text"
                      value={signUpForm.full_name}
                      onChange={(e) => setSignUpForm({ ...signUpForm, full_name: e.target.value })}
                      placeholder="John Doe"
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
                    <input
                      type="email"
                      value={signUpForm.email}
                      onChange={(e) => setSignUpForm({ ...signUpForm, email: e.target.value })}
                      placeholder="you@example.com"
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={signUpForm.password}
                        onChange={(e) => setSignUpForm({ ...signUpForm, password: e.target.value })}
                        placeholder="Create a strong password"
                        className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors pr-12"
                        required
                        minLength={8}
                      />
                      <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    <PasswordStrength password={signUpForm.password} />
                  </div>
                  <button
                    type="submit"
                    disabled={loading || !signUpForm.email || !signUpForm.password || !signUpForm.full_name}
                    className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2"
                  >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                    Create Account
                  </button>
                  <p className="text-center text-sm text-slate-400">
                    Already have an account?{' '}
                    <button type="button" onClick={() => setTab('signin')} className="text-blue-400 hover:text-blue-300">Sign in</button>
                  </p>
                </motion.form>
              )}

              {/* Registration success */}
              {tab === 'signup' && registerSuccess && (
                <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-6">
                  <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Shield className="w-8 h-8 text-green-400" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">Check Your Email</h3>
                  <p className="text-slate-400 text-sm mb-6">
                    We sent a 6-digit verification code to <br />
                    <span className="text-white font-medium">{signUpForm.email}</span>
                  </p>
                  <Link to="/verify" className="inline-flex px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors">
                    Enter Verification Code
                  </Link>
                </motion.div>
              )}
            </>
          )}
        </div>
      </motion.div>
    </div>
  )
}
