'use client'

import { useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
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
  } as const

  return (
    <motion.main
      variants={pageVariants}
      initial="initial"
      animate="animate"
      className="min-h-screen bg-surface-page"
    >
      {/* Page Header */}
      <div className="border-b border-theme">
        <div className="max-w-3xl mx-auto px-6 py-6">
          <h1 className="text-content-primary font-serif font-bold text-xl">
            Diagnostic History
          </h1>
          <p className="text-content-tertiary font-sans text-sm mt-1">
            View and manage your past analyses
          </p>
        </div>
      </div>

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
