'use client'

import { Suspense, useState, useEffect, useRef } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { useAuth } from '@/context/AuthContext'

/**
 * Email Verification Page — Sprint 58
 *
 * URL: /verify-email?token=abc123...
 * Auto-verifies on mount, shows success/error states.
 * Obsidian Vault aesthetic matching login/register pages.
 */

type VerifyState = 'loading' | 'success' | 'error'

function VerifyEmailContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { verifyEmail, isAuthenticated, refreshUser } = useAuth()
  const [verifyState, setVerifyState] = useState<VerifyState>('loading')
  const [errorMessage, setErrorMessage] = useState('')
  const hasVerified = useRef(false)

  const token = searchParams.get('token')

  // Auto-verify on mount
  useEffect(() => {
    if (hasVerified.current) return
    hasVerified.current = true

    if (!token) {
      setVerifyState('error')
      setErrorMessage('No verification token found. Please check your email for the verification link.')
      return
    }

    const verify = async () => {
      const result = await verifyEmail(token)

      if (result.success) {
        setVerifyState('success')
        // If authenticated, refresh user data
        if (isAuthenticated) {
          await refreshUser()
        }
        // Auto-redirect after 3 seconds
        setTimeout(() => {
          router.push(isAuthenticated ? '/' : '/login')
        }, 3000)
      } else {
        setVerifyState('error')
        setErrorMessage(result.error || 'Verification failed. Please try again.')
      }
    }

    verify()
  }, [token, verifyEmail, isAuthenticated, refreshUser, router])

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
            <motion.div
              className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-obsidian-700 border border-obsidian-500 flex items-center justify-center"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 20, delay: 0.2 }}
            >
              <AnimatePresence mode="wait">
                {verifyState === 'loading' && (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="w-10 h-10 border-2 border-oatmeal-400/30 border-t-sage-400 rounded-full animate-spin"
                  />
                )}
                {verifyState === 'success' && (
                  <motion.svg
                    key="success"
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                    className="w-10 h-10 text-sage-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </motion.svg>
                )}
                {verifyState === 'error' && (
                  <motion.svg
                    key="error"
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                    className="w-10 h-10 text-clay-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </motion.svg>
                )}
              </AnimatePresence>
            </motion.div>

            <motion.h1
              className="text-2xl font-serif font-bold text-oatmeal-200 mb-2"
              variants={itemVariants}
            >
              {verifyState === 'loading' && 'Verifying Email...'}
              {verifyState === 'success' && 'Email Verified'}
              {verifyState === 'error' && 'Verification Failed'}
            </motion.h1>

            <motion.p
              className="text-oatmeal-400 font-sans text-sm"
              variants={itemVariants}
            >
              {verifyState === 'loading' && 'Please wait while we verify your email address.'}
              {verifyState === 'success' && 'Your email has been successfully verified.'}
              {verifyState === 'error' && 'We could not verify your email address.'}
            </motion.p>
          </div>

          {/* Content */}
          <div className="px-8 py-6">
            <AnimatePresence mode="wait">
              {verifyState === 'success' && (
                <motion.div
                  key="success-content"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-center space-y-4"
                >
                  <div className="p-4 rounded-lg bg-sage-500/10 border border-sage-500/30">
                    <p className="text-sage-300 text-sm font-sans">
                      {isAuthenticated
                        ? 'Redirecting to your workspace...'
                        : 'Redirecting to login...'}
                    </p>
                  </div>
                  <Link
                    href={isAuthenticated ? '/' : '/login'}
                    className="inline-block text-sage-400 hover:text-sage-300 text-sm font-sans font-medium transition-colors"
                  >
                    {isAuthenticated ? 'Go to workspace now' : 'Log in now'}
                  </Link>
                </motion.div>
              )}

              {verifyState === 'error' && (
                <motion.div
                  key="error-content"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-4"
                >
                  <div className="p-4 rounded-lg bg-clay-500/10 border border-clay-500/30">
                    <p className="text-clay-300 text-sm font-sans">{errorMessage}</p>
                  </div>
                  <div className="flex flex-col gap-3 items-center">
                    {isAuthenticated ? (
                      <Link
                        href="/"
                        className="text-sage-400 hover:text-sage-300 text-sm font-sans font-medium transition-colors"
                      >
                        Back to workspace
                      </Link>
                    ) : (
                      <Link
                        href="/login"
                        className="text-sage-400 hover:text-sage-300 text-sm font-sans font-medium transition-colors"
                      >
                        Go to login
                      </Link>
                    )}
                  </div>
                </motion.div>
              )}

              {verifyState === 'loading' && (
                <motion.div
                  key="loading-content"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-center py-4"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
                    <span className="text-oatmeal-400 text-sm font-sans">Processing verification...</span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
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

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen bg-gradient-obsidian flex items-center justify-center p-6">
        <div className="w-10 h-10 border-2 border-oatmeal-400/30 border-t-sage-400 rounded-full animate-spin" />
      </main>
    }>
      <VerifyEmailContent />
    </Suspense>
  )
}
