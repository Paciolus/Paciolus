'use client'

import { motion } from 'framer-motion'

/**
 * UnverifiedCTA — Shared email-verification prompt for authenticated
 * but unverified users.
 *
 * Displayed on tool pages when the user is logged in but has not yet
 * verified their email address. Parallel to `GuestCTA` (which handles
 * the unauthenticated case).
 *
 * Sprint 595: Created after the 2026-04-09 incident exposed that all
 * 11 tool pages silently hid their entire UI behind `isVerified` with
 * no explanation — users saw a blank page below the title and assumed
 * the app was broken.
 */
export function UnverifiedCTA() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-lg mx-auto theme-card rounded-2xl p-10 text-center mb-10"
    >
      <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-clay-50 dark:bg-clay-500/10 border border-clay-500/20 flex items-center justify-center">
        <svg className="w-8 h-8 text-clay-600 dark:text-clay-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      </div>
      <h2 className="text-2xl font-serif font-bold text-content-primary mb-3">
        Verify Your Email
      </h2>
      <p className="text-content-secondary font-sans mb-2">
        This tool requires a verified email address before it can be used.
      </p>
      <p className="text-content-tertiary font-sans text-sm">
        Check your inbox for a verification link, or use the banner above to resend.
      </p>
    </motion.div>
  )
}
