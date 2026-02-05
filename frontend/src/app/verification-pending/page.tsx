'use client'

import { Suspense, useEffect, useRef } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { useAuth } from '@/context/AuthContext'
import { useVerification } from '@/hooks/useVerification'

/**
 * Verification Pending Page — Sprint 58
 *
 * URL: /verification-pending?email=user@example.com
 * Shown after registration. "Check your email" with resend button.
 * Obsidian Vault aesthetic.
 */

function VerificationPendingContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { isAuthenticated, user, checkVerificationStatus } = useAuth()
  const { cooldownSeconds, canResend, isResending, resendError, resendSuccess, resend } = useVerification()
  const checkedRef = useRef(false)

  const email = searchParams.get('email') || user?.email || ''

  // If already verified, redirect to home
  useEffect(() => {
    if (checkedRef.current) return
    checkedRef.current = true

    if (!isAuthenticated) return

    const check = async () => {
      const status = await checkVerificationStatus()
      if (status?.is_verified) {
        router.push('/')
      }
    }
    check()
  }, [isAuthenticated, checkVerificationStatus, router])

  // Format cooldown as M:SS
  const formatCooldown = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.1 },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { type: 'spring' as const, stiffness: 300, damping: 24 },
    },
  }

  return (
    <main className="min-h-screen bg-gradient-obsidian flex items-center justify-center p-6">
      <motion.div
        className="w-full max-w-md"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.div
          className="bg-obsidian-800 border border-obsidian-600 rounded-2xl shadow-2xl overflow-hidden"
          variants={itemVariants}
        >
          {/* Header */}
          <div className="px-8 pt-8 pb-6 text-center border-b border-obsidian-700">
            {/* Envelope Icon */}
            <motion.div
              className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-obsidian-700 border border-obsidian-500 flex items-center justify-center"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 20, delay: 0.2 }}
            >
              <svg
                className="w-10 h-10 text-sage-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </motion.div>

            <motion.h1
              className="text-2xl font-serif font-bold text-oatmeal-200 mb-2"
              variants={itemVariants}
            >
              Check Your Email
            </motion.h1>

            <motion.p
              className="text-oatmeal-400 font-sans text-sm"
              variants={itemVariants}
            >
              We sent a verification link to
            </motion.p>
            {email && (
              <motion.p
                className="text-oatmeal-200 font-mono text-sm mt-1"
                variants={itemVariants}
              >
                {email}
              </motion.p>
            )}
          </div>

          {/* Instructions */}
          <div className="px-8 py-6 space-y-4">
            <div className="p-4 rounded-lg bg-obsidian-700/50 border border-obsidian-600">
              <p className="text-oatmeal-300 text-sm font-sans leading-relaxed">
                Click the link in your email to verify your account. The link will expire in 24 hours.
                If you don&apos;t see the email, check your spam folder.
              </p>
            </div>

            {/* Resend Section */}
            {isAuthenticated && (
              <div className="text-center space-y-3">
                {resendSuccess && (
                  <motion.div
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-3 rounded-lg bg-sage-500/10 border border-sage-500/30"
                  >
                    <p className="text-sage-300 text-sm font-sans">Verification email sent!</p>
                  </motion.div>
                )}

                {resendError && (
                  <motion.div
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-3 rounded-lg bg-clay-500/10 border border-clay-500/30"
                  >
                    <p className="text-clay-300 text-sm font-sans">{resendError}</p>
                  </motion.div>
                )}

                <button
                  onClick={resend}
                  disabled={!canResend || isResending}
                  className={`px-6 py-2.5 rounded-xl font-sans text-sm font-medium transition-all ${
                    canResend && !isResending
                      ? 'bg-sage-500/10 border border-sage-500/30 text-sage-400 hover:bg-sage-500/20 hover:border-sage-500/50'
                      : 'bg-obsidian-700 border border-obsidian-600 text-oatmeal-500 cursor-not-allowed'
                  }`}
                >
                  {isResending ? (
                    <span className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-oatmeal-400/30 border-t-oatmeal-400 rounded-full animate-spin" />
                      Sending...
                    </span>
                  ) : canResend ? (
                    'Resend Verification Email'
                  ) : (
                    <span className="flex items-center gap-2">
                      Resend available in
                      <span className="font-mono text-oatmeal-400">{formatCooldown(cooldownSeconds)}</span>
                    </span>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Footer */}
          <motion.div
            className="px-8 py-5 bg-obsidian-700/30 border-t border-obsidian-700 text-center"
            variants={itemVariants}
          >
            <p className="text-oatmeal-400 text-sm font-sans">
              Already verified?{' '}
              <Link
                href="/login"
                className="text-sage-400 hover:text-sage-300 font-medium transition-colors"
              >
                Sign in
              </Link>
            </p>
          </motion.div>
        </motion.div>

        {/* Bottom Link */}
        <motion.div className="mt-6 text-center" variants={itemVariants}>
          <Link
            href="/"
            className="text-oatmeal-500 hover:text-oatmeal-400 text-sm font-sans transition-colors inline-flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Paciolus
          </Link>
        </motion.div>
      </motion.div>
    </main>
  )
}

export default function VerificationPendingPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen bg-gradient-obsidian flex items-center justify-center p-6">
        <div className="w-10 h-10 border-2 border-oatmeal-400/30 border-t-sage-400 rounded-full animate-spin" />
      </main>
    }>
      <VerificationPendingContent />
    </Suspense>
  )
}
