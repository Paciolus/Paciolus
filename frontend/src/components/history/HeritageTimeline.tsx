'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'
import { CHART_SHADOWS } from '@/utils/chartTheme'
import type { AuditActivity } from '@/types/history'
import { STORED_METADATA, NOT_STORED } from '@/types/history'
import { ActivityEntry } from './ActivityEntry'

interface HeritageTimelineProps {
  activities: AuditActivity[]
  onReRun: (activity: AuditActivity) => void
}

/**
 * HeritageTimeline - Professional History View
 *
 * Vertical timeline inspired by traditional accounting ledgers.
 * Uses Oat & Obsidian theme with "Premium Restraint" design.
 *
 * Features:
 * - Zero-Storage Reassurance Banner (top)
 * - Staggered entry animations via framer-motion
 * - Ledger-style ruled lines and columns
 * - Empty state with encouraging CTA
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */
export function HeritageTimeline({ activities, onReRun }: HeritageTimelineProps) {
  const [showStorageInfo, setShowStorageInfo] = useState(false)

  // Container animation for staggered children
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.2,
      },
    },
  }

  // Banner pulse animation
  const pulseVariants = {
    initial: { boxShadow: `0 0 0 0 ${CHART_SHADOWS.sagePulse(0)}` },
    animate: {
      boxShadow: [
        `0 0 0 0 ${CHART_SHADOWS.sagePulse(0)}`,
        `0 0 0 4px ${CHART_SHADOWS.sagePulse(0.1)}`,
        `0 0 0 0 ${CHART_SHADOWS.sagePulse(0)}`,
      ],
      transition: {
        duration: 3,
        repeat: Infinity,
        ease: 'easeInOut' as const,
      },
    },
  }

  // Empty State Component
  if (activities.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-6">
        {/* Empty state illustration */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="w-24 h-24 rounded-full bg-obsidian-700/50 flex items-center justify-center mb-6"
        >
          <svg
            className="w-12 h-12 text-oatmeal-500/50"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </motion.div>

        <motion.h3
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-oatmeal-200 font-serif text-xl mb-2"
        >
          No Diagnostic History Yet
        </motion.h3>

        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-oatmeal-500 font-sans text-sm text-center max-w-sm mb-6"
        >
          Your completed diagnostics will appear here. Upload a trial balance
          to begin your first analysis.
        </motion.p>

        <motion.a
          href="/"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          className="
            flex items-center gap-2 px-6 py-3 rounded-xl
            bg-sage-500 text-obsidian-900
            font-sans font-medium text-sm
            shadow-lg shadow-sage-500/20
            hover:bg-sage-400 transition-colors
          "
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          <span>Start Your First Diagnostic</span>
        </motion.a>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Zero-Storage Reassurance Banner */}
      <motion.div
        variants={pulseVariants}
        initial="initial"
        animate="animate"
        className="
          relative rounded-xl overflow-hidden
          bg-sage-500/10 border border-sage-500/20
          p-4
        "
      >
        <div className="flex items-start gap-3">
          {/* Shield icon */}
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-sage-500/20 flex items-center justify-center">
            <svg className="w-5 h-5 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>

          <div className="flex-1">
            <h3 className="text-sage-300 font-serif font-semibold text-sm">
              Zero-Storage Architecture
            </h3>
            <p className="text-oatmeal-400 font-sans text-sm mt-1">
              Your financial data was never saved. Only diagnostic metadata is stored.
            </p>
          </div>

          {/* Info toggle button */}
          <motion.button
            onClick={() => setShowStorageInfo(!showStorageInfo)}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            className="
              flex-shrink-0 w-8 h-8 rounded-full
              bg-obsidian-700/50 hover:bg-obsidian-700
              flex items-center justify-center
              text-oatmeal-400 hover:text-oatmeal-200
              transition-colors
            "
            aria-label="Toggle storage details"
            aria-expanded={showStorageInfo}
          >
            <motion.svg
              animate={{ rotate: showStorageInfo ? 180 : 0 }}
              transition={{ duration: 0.2 }}
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </motion.svg>
          </motion.button>
        </div>

        {/* Expandable storage details */}
        <AnimatePresence>
          {showStorageInfo && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
              className="overflow-hidden"
            >
              <div className="pt-4 mt-4 border-t border-sage-500/20 grid md:grid-cols-2 gap-4">
                {/* What IS stored */}
                <div>
                  <h4 className="text-sage-400 font-sans font-medium text-xs uppercase tracking-wide mb-2 flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Stored (Metadata Only)
                  </h4>
                  <ul className="space-y-1">
                    {STORED_METADATA.map((item) => (
                      <li key={item} className="text-oatmeal-500 text-xs font-sans flex items-start gap-1.5">
                        <span className="text-sage-500/50 mt-0.5">-</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* What is NOT stored */}
                <div>
                  <h4 className="text-clay-400 font-sans font-medium text-xs uppercase tracking-wide mb-2 flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                    Never Stored
                  </h4>
                  <ul className="space-y-1">
                    {NOT_STORED.map((item) => (
                      <li key={item} className="text-oatmeal-500 text-xs font-sans flex items-start gap-1.5">
                        <span className="text-clay-500/50 mt-0.5">-</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Timeline Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-oatmeal-200 font-serif text-lg">
          Diagnostic History
        </h2>
        <span className="text-oatmeal-500 font-sans text-sm">
          {activities.length} diagnostic{activities.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Timeline Container */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative"
      >
        {/* Vertical timeline connector line */}
        <div className="absolute left-[7px] top-6 bottom-6 w-0.5 bg-obsidian-600" />

        {/* Activity Entries */}
        <div className="space-y-4">
          {activities.map((activity, index) => (
            <ActivityEntry
              key={activity.id}
              activity={activity}
              index={index}
              onReRun={onReRun}
            />
          ))}
        </div>
      </motion.div>

      {/* Footer note */}
      <div className="pt-4 border-t border-obsidian-700/50">
        <p className="text-oatmeal-500 text-xs font-sans text-center">
          History is stored locally on your device. Clearing browser data will remove this history.
        </p>
      </div>
    </div>
  )
}

export default HeritageTimeline
