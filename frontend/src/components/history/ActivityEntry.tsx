'use client'

import { motion } from 'framer-motion'
import type { AuditActivity } from '@/types/history'
import { createTimelineEntryVariants, createTimelineNodeVariants } from '@/utils/themeUtils'
import { formatDateTime, formatNumber, formatCurrency } from '@/utils'

interface ActivityEntryProps {
  activity: AuditActivity
  index: number
  onReRun: (activity: AuditActivity) => void
}

/**
 * ActivityEntry - Heritage Timeline Entry Card
 *
 * Design: Traditional accounting ledger aesthetic with ruled lines.
 * Uses "Premium Restraint" philosophy - subtle left-border accents
 * rather than overwhelming color blocks.
 *
 * - Balanced entries: Sage (#4A7C59) left border
 * - Unbalanced entries: Clay (#BC4749) left border
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */
export function ActivityEntry({ activity, index, onReRun }: ActivityEntryProps) {
  const isBalanced = activity.balanced

  // Use shared animation variants from theme utilities
  const cardVariants = createTimelineEntryVariants(index)
  const nodeVariants = createTimelineNodeVariants(index)

  return (
    <div className="relative pl-8">
      {/* Timeline node */}
      <motion.div
        variants={nodeVariants}
        className={`
          absolute left-0 top-6 w-4 h-4 rounded-full
          border-2 bg-surface-card
          ${isBalanced
            ? 'border-sage-500'
            : 'border-clay-500'
          }
        `}
      />

      {/* Entry Card */}
      <motion.div
        variants={cardVariants}
        className={`
          relative rounded-lg overflow-hidden
          bg-surface-card
          border-l-4
          ${isBalanced
            ? 'border-l-sage-500'
            : 'border-l-clay-500'
          }
          border border-theme
          group
        `}
      >
        {/* Ledger-style ruled line effect (top) */}
        <div className="absolute top-0 left-0 right-0 h-px bg-obsidian-500/30" />

        <div className="p-4">
          {/* Header Row: Timestamp and Status Badge */}
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-content-tertiary text-xs font-sans">
                {formatDateTime(activity.timestamp)}
              </p>
              <p className="text-content-primary font-mono text-sm mt-1 tracking-tight">
                {activity.filenameHash}...
              </p>
            </div>

            {/* Balance Status Badge */}
            <div className={`
              inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-sans font-medium
              ${isBalanced
                ? 'bg-sage-500/20 text-sage-400 border border-sage-500/30'
                : 'bg-clay-500/20 text-clay-400 border border-clay-500/30'
              }
            `}>
              {isBalanced ? (
                <>
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>Balanced</span>
                </>
              ) : (
                <>
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span>Unbalanced</span>
                </>
              )}
            </div>
          </div>

          {/* Ledger-style Data Grid */}
          <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            {/* Row Count */}
            <div className="flex justify-between items-baseline">
              <span className="text-content-tertiary font-sans text-xs">Records</span>
              <span className="text-content-primary font-mono">
                {formatNumber(activity.rowCount)} rows
              </span>
            </div>

            {/* Threshold */}
            <div className="flex justify-between items-baseline">
              <span className="text-content-tertiary font-sans text-xs">Threshold</span>
              <span className="text-content-primary font-mono">
                {formatCurrency(activity.materialityThreshold)}
              </span>
            </div>

            {/* Debits */}
            <div className="flex justify-between items-baseline">
              <span className="text-content-tertiary font-sans text-xs">Debits</span>
              <span className="text-content-primary font-mono font-medium">
                {formatCurrency(activity.totalDebits)}
              </span>
            </div>

            {/* Credits */}
            <div className="flex justify-between items-baseline">
              <span className="text-content-tertiary font-sans text-xs">Credits</span>
              <span className="text-content-primary font-mono font-medium">
                {formatCurrency(activity.totalCredits)}
              </span>
            </div>
          </div>

          {/* Ledger-style ruled line (separator) */}
          <div className="my-3 h-px bg-obsidian-500/30" />

          {/* Footer Row: Anomalies + Re-Run Button */}
          <div className="flex items-center justify-between">
            {/* Anomaly Count */}
            <div className="flex items-center gap-4 text-xs">
              {activity.anomalyCount > 0 ? (
                <div className="flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-clay-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span className="text-content-secondary font-sans">
                    {activity.anomalyCount} anomal{activity.anomalyCount === 1 ? 'y' : 'ies'}
                    {activity.materialCount > 0 && (
                      <span className="text-clay-400 ml-1">
                        ({activity.materialCount} material)
                      </span>
                    )}
                  </span>
                </div>
              ) : (
                <span className="text-sage-400/70 font-sans flex items-center gap-1.5">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  No anomalies
                </span>
              )}

              {/* Multi-sheet indicator */}
              {activity.isConsolidated && activity.sheetCount && activity.sheetCount > 1 && (
                <span className="text-content-tertiary font-sans flex items-center gap-1">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {activity.sheetCount} sheets
                </span>
              )}
            </div>

            {/* Quick Re-Run Button */}
            <motion.button
              onClick={() => onReRun(activity)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="
                flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                text-xs font-sans font-medium
                bg-surface-card-secondary text-content-secondary
                hover:bg-surface-card hover:text-content-primary
                opacity-60 group-hover:opacity-100
                transition-all duration-200
                border border-theme
              "
              title="Re-upload Required"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Re-Run</span>
            </motion.button>
          </div>
        </div>

        {/* Ledger-style ruled line effect (bottom) */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-obsidian-500/30" />
      </motion.div>
    </div>
  )
}

export default ActivityEntry
