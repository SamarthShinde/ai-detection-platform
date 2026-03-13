/**
 * Validate email format.
 */
export function validateEmail(email: string): boolean {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email.trim())
}

interface PasswordValidationResult {
  valid: boolean
  errors: string[]
}

/**
 * Validate password and return errors array.
 */
export function validatePassword(password: string): PasswordValidationResult {
  const errors: string[] = []

  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long')
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter')
  }
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter')
  }
  if (!/[0-9]/.test(password)) {
    errors.push('Password must contain at least one number')
  }

  return {
    valid: errors.length === 0,
    errors,
  }
}

export type PasswordStrength = 'weak' | 'medium' | 'strong'

/**
 * Evaluate password strength.
 */
export function validatePasswordStrength(password: string): PasswordStrength {
  if (!password || password.length < 6) return 'weak'

  let score = 0

  // Length scoring
  if (password.length >= 8) score++
  if (password.length >= 12) score++

  // Character variety
  if (/[A-Z]/.test(password)) score++
  if (/[a-z]/.test(password)) score++
  if (/[0-9]/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++

  // Pattern checks
  if (/(.)\1{2,}/.test(password)) score-- // repeated characters
  if (/^[a-z]+$/.test(password) || /^[0-9]+$/.test(password)) score-- // all same type

  if (score <= 2) return 'weak'
  if (score <= 4) return 'medium'
  return 'strong'
}

/**
 * Validate that two passwords match.
 */
export function validatePasswordsMatch(password: string, confirmPassword: string): boolean {
  return password === confirmPassword
}

/**
 * Validate full name (non-empty, reasonable length).
 */
export function validateFullName(name: string): { valid: boolean; error?: string } {
  const trimmed = name.trim()
  if (!trimmed) return { valid: false, error: 'Full name is required' }
  if (trimmed.length < 2) return { valid: false, error: 'Name must be at least 2 characters' }
  if (trimmed.length > 100) return { valid: false, error: 'Name is too long' }
  return { valid: true }
}

/**
 * Validate a file for upload constraints.
 */
export function validateFile(
  file: File,
  acceptedTypes: string[],
  maxSize: number
): { valid: boolean; error?: string } {
  if (!acceptedTypes.includes(file.type)) {
    return { valid: false, error: `File type "${file.type}" is not supported` }
  }
  if (file.size > maxSize) {
    const maxMB = Math.round(maxSize / (1024 * 1024))
    return { valid: false, error: `File size exceeds the ${maxMB}MB limit` }
  }
  return { valid: true }
}
