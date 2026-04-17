'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { apiPost } from '@/utils/apiClient'
import { fadeUp } from '@/lib/motion'

/**
 * Forgot Password Page — Sprint 572
 *
 * Collects email, calls POST /auth/forgot-password.
 * Always shows success message (prevents account enumeration).
 * Oat & Obsidian vault aesthetic matching login/register pages.
 */

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!email.trim()) {
      setError('Please enter your email address.')
      return
    }

    setIsSubmitting(true)
    try {
      const result = await apiPost('/auth/forgot-password', null, { email: email.trim().toLowerCase() })
      if (result.ok) {
        setSubmitted(true)
      } else {
        // Even on error, show success to prevent enumeration
        setSubmitted(true)
      }
    } catch {
      setSubmitted(true)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate="visible"
        custom={0}
        className="bg-obsidian-800 border border-obsidian-700 rounded-2xl p-8 shadow-vault"
      >
        {/* Success Icon */}
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 rounded-full bg-sage-900/30 flex items-center justify-center">
            <svg className="w-8 h-8 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
        </div>

        <h1 className="text-2xl font-serif text-oatmeal-200 text-center mb-4">Check Your Email</h1>
        <p className="text-oatmeal-400 font-sans text-center mb-6 leading-relaxed">
          If an account with that email exists, we&apos;ve sent a password reset link.
          The link will expire in 1 hour.
        </p>
        <p className="text-oatmeal-500 font-sans text-center text-sm mb-8">
          Didn&apos;t receive an email? Check your spam folder or try again.
        </p>

        <div className="flex flex-col gap-3">
          <button
            onClick={() => { setSubmitted(false); setEmail('') }}
            className="w-full py-3 rounded-xl font-sans font-bold bg-obsidian-700 text-oatmeal-300 hover:bg-obsidian-600 transition-colors"
          >
            Try Another Email
          </button>
          <Link
            href="/login"
            className="w-full py-3 rounded-xl font-sans font-bold text-center bg-sage-700 text-oatmeal-50 hover:bg-sage-600 transition-colors"
          >
            Back to Login
          </Link>
        </div>
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
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
      </div>

      <h1 className="text-2xl font-serif text-oatmeal-200 text-center mb-2">Reset Your Password</h1>
      <p className="text-oatmeal-500 font-sans text-center mb-8 text-sm">
        Enter your email address and we&apos;ll send you a link to reset your password.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="p-3 rounded-lg bg-clay-900/30 border border-clay-800 text-clay-400 text-sm font-sans">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="email" className="block text-sm font-sans text-oatmeal-400 mb-2">
            Email Address
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
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
          {isSubmitting ? 'Sending...' : 'Send Reset Link'}
        </button>
      </form>

      <div className="mt-6 text-center">
        <Link href="/login" className="text-sm text-oatmeal-500 hover:text-oatmeal-400 font-sans transition-colors">
          Remember your password? Sign in
        </Link>
      </div>
    </motion.div>
  )
}
