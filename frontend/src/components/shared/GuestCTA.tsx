'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'

interface GuestCTAProps {
  description: string
}

/**
 * GuestCTA — Shared sign-in prompt for unauthenticated visitors.
 *
 * Displayed on tool pages when the user is not logged in.
 * Standardizes the "Sign in to get started" block across all 11 tools.
 *
 * Sprint 239: Extracted from 11 duplicated inline blocks.
 */
export function GuestCTA({ description }: GuestCTAProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="theme-card rounded-2xl p-8 text-center mb-10"
    >
      <h2 className="font-serif text-xl text-content-primary mb-2">Sign in to get started</h2>
      <p className="font-sans text-content-secondary text-sm mb-6 max-w-md mx-auto">
        {description}
      </p>
      <div className="flex items-center justify-center gap-4">
        <Link
          href="/login"
          className="btn-primary"
        >
          Sign In
        </Link>
        <Link
          href="/register"
          className="btn-secondary"
        >
          Create Account
        </Link>
      </div>
    </motion.div>
  )
}
