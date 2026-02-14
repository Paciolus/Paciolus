'use client'

import { useCallback } from 'react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { HeritageTimeline } from '@/components/history'
import { useActivityHistory } from '@/hooks'
import type { AuditActivity } from '@/types/history'

/**
 * History Page - Heritage Timeline View
 *
 * Sprint 18: Diagnostic Fidelity & Batch Intelligence
 *
 * Displays diagnostic history with Zero-Storage reassurance.
 * - Authenticated users: Fetches from backend API
 * - Anonymous users: Falls back to localStorage
 *
 * Features:
 * - Heritage Timeline component with ledger aesthetic
 * - Zero-Storage Reassurance Banner
 * - Quick Re-Run navigation (requires re-upload)
 * - Empty state for new users
 *
 * Sprint 18 Terminology: "Audit History" → "Diagnostic History"
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */
export default function HistoryPage() {
  const router = useRouter()
  const { activities, isLoading } = useActivityHistory({ pageSize: 50 })

  // Handle Re-Run action
  const handleReRun = useCallback((activity: AuditActivity) => {
    // Store the threshold from this audit for convenience
    sessionStorage.setItem('paciolus_last_threshold', String(activity.materialityThreshold))

    // Navigate to home page with a message
    router.push('/?rerun=true')
  }, [router])

  // Page fade-in animation
  const pageVariants = {
    initial: { opacity: 0 },
    animate: {
      opacity: 1,
      transition: {
        duration: 0.4,
        ease: 'easeOut' as const,
      },
    },
  }

  return (
    <motion.main
      variants={pageVariants}
      initial="initial"
      animate="animate"
      className="min-h-screen bg-surface-page"
    >
      {/* Header */}
      <header className="border-b border-theme">
        <div className="max-w-3xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            {/* Logo/Brand */}
            <a
              href="/"
              className="flex items-center gap-3 group"
            >
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="w-10 h-10 rounded-xl bg-sage-50 flex items-center justify-center"
              >
                <svg
                  className="w-6 h-6 text-sage-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"
                  />
                </svg>
              </motion.div>
              <div>
                <h1 className="text-content-primary font-serif font-bold text-lg group-hover:text-sage-600 transition-colors">
                  Paciolus
                </h1>
                <p className="text-content-tertiary font-sans text-xs">
                  Diagnostic History
                </p>
              </div>
            </a>

            {/* Navigation */}
            <nav className="flex items-center gap-4">
              <a
                href="/"
                className="
                  flex items-center gap-2 px-4 py-2 rounded-lg
                  text-content-secondary font-sans text-sm
                  hover:bg-surface-card-secondary hover:text-content-primary
                  transition-colors
                "
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
                <span>Home</span>
              </a>

              <a
                href="/"
                className="
                  flex items-center gap-2 px-4 py-2 rounded-lg
                  bg-sage-600 text-white
                  font-sans font-medium text-sm
                  hover:bg-sage-700 transition-colors
                "
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>New Diagnostic</span>
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-3xl mx-auto px-6 py-8">
        {isLoading ? (
          // Loading state
          <div className="flex flex-col items-center justify-center py-16">
            <div className="w-8 h-8 border-2 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
            <p className="text-content-tertiary font-sans text-sm mt-4">
              Loading history...
            </p>
          </div>
        ) : (
          <HeritageTimeline
            activities={activities}
            onReRun={handleReRun}
          />
        )}
      </div>

      {/* Footer */}
      <footer className="border-t border-theme mt-auto">
        <div className="max-w-3xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between text-xs font-sans text-content-tertiary">
            <span>Paciolus - Surgical Precision for Trial Balance Diagnostics</span>
            <span>Zero-Storage Architecture</span>
          </div>
        </div>
      </footer>
    </motion.main>
  )
}
