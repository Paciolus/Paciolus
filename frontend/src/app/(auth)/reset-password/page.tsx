'use client'

import { Suspense, useState, useRef } from 'react'
import Link from 'next/link'
import { useSearchParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { apiPost } from '@/utils/apiClient'
import { fadeUp } from '@/lib/motion'

/**
 * Reset Password Page — Sprint 572
 *
 * URL: /reset-password?token=abc123...
 * Collects new password, calls POST /auth/reset-password.
 * Token is stripped from URL on load (same pattern as verify-email).
 */

function ResetPasswordContent() {
  const searchParams = useSearchParams()
  const router = useRouter()

  // Capture token on first render, then strip from URL
  const tokenRef = useRef<string | null>(null)
  if (tokenRef.current === null) {
    tokenRef.current = searchParams.get('token')
  }

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [status, setStatus] = useState<'form' | 'success' | 'error'>('form')
  const [errorMessage, setErrorMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Strip token from URL on mount
  const hasStripped = useRef(false)
  if (!hasStripped.current && typeof window !== 'undefined') {
    hasStripped.current = true
    window.history.replaceState(null, '', '/reset-password')
  }

  if (!tokenRef.current && status === 'form') {
    return (
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate="visible"
        custom={0}
        className="bg-obsidian-800 border border-obsidian-700 rounded-2xl p-8 shadow-vault text-center"
      >
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 rounded-full bg-clay-900/30 flex items-center justify-center">
            <svg className="w-8 h-8 text-clay-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
        </div>
        <h1 className="text-2xl font-serif text-oatmeal-200 mb-4">Invalid Reset Link</h1>
        <p className="text-oatmeal-400 font-sans mb-6">
          This password reset link is invalid or has already been used.
        </p>
        <Link
          href="/forgot-password"
          className="inline-block py-3 px-8 rounded-xl font-sans font-bold bg-sage-700 text-oatmeal-50 hover:bg-sage-600 transition-colors"
        >
          Request a New Link
        </Link>
      </motion.div>
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage('')

    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters.')
      return
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.')
      return
    }

    // Basic complexity check
    const hasUpper = /[A-Z]/.test(password)
    const hasLower = /[a-z]/.test(password)
    const hasDigit = /[0-9]/.test(password)
    if (!hasUpper || !hasLower || !hasDigit) {
      setErrorMessage('Password must contain at least one uppercase letter, one lowercase letter, and one number.')
      return
    }

    setIsSubmitting(true)
    try {
      const result = await apiPost<{ message: string }>('/auth/reset-password', null, {
        token: tokenRef.current,
        new_password: password,
      })

      if (result.ok) {
        setStatus('success')
      } else {
        setStatus('error')
        setErrorMessage(result.error || 'Failed to reset password. The link may have expired.')
      }
    } catch {
      setStatus('error')
      setErrorMessage('An unexpected error occurred. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (status === 'success') {
    return (
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate="visible"
        custom={0}
        className="bg-obsidian-800 border border-obsidian-700 rounded-2xl p-8 shadow-vault text-center"
      >
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 rounded-full bg-sage-900/30 flex items-center justify-center">
            <svg className="w-8 h-8 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>
        <h1 className="text-2xl font-serif text-oatmeal-200 mb-4">Password Reset</h1>
        <p className="text-oatmeal-400 font-sans mb-8">
          Your password has been reset successfully. You can now log in with your new password.
        </p>
        <button
          onClick={() => router.push('/login')}
          className="w-full py-3 rounded-xl font-sans font-bold bg-sage-700 text-oatmeal-50 hover:bg-sage-600 transition-colors"
        >
          Go to Login
        </button>
      </motion.div>
    )
  }

  if (status === 'error') {
    return (
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate="visible"
        custom={0}
        className="bg-obsidian-800 border border-obsidian-700 rounded-2xl p-8 shadow-vault text-center"
      >
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 rounded-full bg-clay-900/30 flex items-center justify-center">
            <svg className="w-8 h-8 text-clay-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        </div>
        <h1 className="text-2xl font-serif text-oatmeal-200 mb-4">Reset Failed</h1>
        <p className="text-oatmeal-400 font-sans mb-8">{errorMessage}</p>
        <Link
          href="/forgot-password"
          className="inline-block w-full py-3 rounded-xl font-sans font-bold bg-sage-700 text-oatmeal-50 hover:bg-sage-600 transition-colors"
        >
          Request a New Link
        </Link>
      </motion.div>
    )
  }

  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      custom={0}
      className="bg-obsidian-800 border border-obsidian-700 rounded-2xl p-8 shadow-vault"
    >
      {/* Lock Icon */}
      <div className="flex justify-center mb-6">
        <div className="w-16 h-16 rounded-full bg-obsidian-700 flex items-center justify-center">
          <svg className="w-8 h-8 text-oatmeal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
        </div>
      </div>

      <h1 className="text-2xl font-serif text-oatmeal-200 text-center mb-2">Choose a New Password</h1>
      <p className="text-oatmeal-500 font-sans text-center mb-8 text-sm">
        Enter your new password below. Must be at least 8 characters with uppercase, lowercase, and a number.
      </p>

      <form onSubmit={handleSubmit} className="space-y-5">
        {errorMessage && (
          <div className="p-3 rounded-lg bg-clay-900/30 border border-clay-800 text-clay-400 text-sm font-sans">
            {errorMessage}
          </div>
        )}

        <div>
          <label htmlFor="password" className="block text-sm font-sans text-oatmeal-400 mb-2">
            New Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter new password"
            autoComplete="new-password"
            className="w-full px-4 py-3 rounded-xl bg-obsidian-900 border border-obsidian-600 text-oatmeal-200 placeholder-oatmeal-600 font-sans focus:outline-hidden focus:ring-2 focus:ring-sage-600 focus:border-transparent transition-all"
          />
        </div>

        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-sans text-oatmeal-400 mb-2">
            Confirm Password
          </label>
          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm new password"
            autoComplete="new-password"
            className="w-full px-4 py-3 rounded-xl bg-obsidian-900 border border-obsidian-600 text-oatmeal-200 placeholder-oatmeal-600 font-sans focus:outline-hidden focus:ring-2 focus:ring-sage-600 focus:border-transparent transition-all"
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className={`w-full py-3 rounded-xl font-sans font-bold transition-all ${
            isSubmitting
              ? 'bg-obsidian-600 text-oatmeal-500 cursor-not-allowed'
              : 'bg-sage-700 text-oatmeal-50 hover:bg-sage-600'
          }`}
        >
          {isSubmitting ? 'Resetting...' : 'Reset Password'}
        </button>
      </form>
    </motion.div>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="bg-obsidian-800 border border-obsidian-700 rounded-2xl p-8 shadow-vault text-center">
          <div className="animate-pulse text-oatmeal-400 font-sans">Loading...</div>
        </div>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  )
}
