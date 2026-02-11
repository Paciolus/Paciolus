'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { useVerification } from '@/hooks/useVerification'

/**
 * VerificationBanner — Sprint 58
 *
 * Dismissible banner shown to authenticated but unverified users.
 * Includes resend button with countdown timer.
 * Dismiss is React state only — reappears on full page refresh.
 */

export function VerificationBanner() {
  const { user, isAuthenticated } = useAuth()
  const { cooldownSeconds, canResend, isResending, resendSuccess, resend } = useVerification()
  const [isDismissed, setIsDismissed] = useState(false)

  // Only show for authenticated, unverified users
  if (!isAuthenticated || !user || user.is_verified !== false || isDismissed) {
    return null
  }

  const formatCooldown = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className="bg-theme-error-bg border border-theme-error-border mx-6 mt-4 rounded-xl"
      >
        <div className="px-4 py-3 flex items-center justify-between gap-4">
          {/* Warning icon + message */}
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <svg
              className="w-5 h-5 text-theme-error-text flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
            <p className="text-content-primary text-sm font-sans truncate">
              Your email is not yet verified. Please check your inbox for a verification link.
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3 flex-shrink-0">
            {resendSuccess ? (
              <span className="text-theme-success-text text-xs font-sans font-medium">Sent!</span>
            ) : (
              <button
                onClick={resend}
                disabled={!canResend || isResending}
                className={`text-sm font-sans font-medium whitespace-nowrap transition-colors ${
                  canResend && !isResending
                    ? 'text-theme-success-text hover:opacity-80'
                    : 'text-content-tertiary cursor-not-allowed'
                }`}
              >
                {isResending
                  ? 'Sending...'
                  : canResend
                  ? 'Resend Email'
                  : `Resend in ${formatCooldown(cooldownSeconds)}`}
              </button>
            )}

            {/* Dismiss button */}
            <button
              onClick={() => setIsDismissed(true)}
              className="text-content-tertiary hover:text-content-primary transition-colors"
              aria-label="Dismiss verification banner"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
