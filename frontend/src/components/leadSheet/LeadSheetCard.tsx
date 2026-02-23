'use client'

/**
 * LeadSheetCard - Sprint 50 Lead Sheet Grouping Card
 *
 * Displays a single lead sheet grouping with account list,
 * totals, and drill-down capability.
 *
 * Features:
 * - Collapsible account list
 * - Category-based color coding
 * - Debit/Credit totals
 * - Net balance display
 * - Oat & Obsidian theme compliance
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Display component only, no data persistence
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { LeadSheetSummary } from '@/types/leadSheet'
import { getLeadSheetColors } from '@/types/leadSheet'

interface LeadSheetCardProps {
  /** Lead sheet summary data */
  summary: LeadSheetSummary
  /** Animation index for staggered entrance */
  index?: number
}

/**
 * Format currency for display
 */
function formatCurrency(value: number): string {
  const absValue = Math.abs(value)
  if (absValue >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`
  } else if (absValue >= 1_000) {
    return `$${(value / 1_000).toFixed(1)}K`
  }
  return `$${value.toFixed(0)}`
}

/**
 * Format full currency for detail view
 */
function formatFullCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

/**
 * LeadSheetCard Component
 */
export function LeadSheetCard({ summary, index = 0 }: LeadSheetCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const colors = getLeadSheetColors(summary.category)

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className={`
        rounded-xl border overflow-hidden
        ${colors.border} ${colors.bg}
        hover:shadow-lg transition-shadow duration-200
      `}
    >
      {/* Header */}
      <div
        className="p-4 cursor-pointer select-none"
        onClick={() => setIsExpanded(!isExpanded)}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setIsExpanded(!isExpanded) } }}
        role="button"
        tabIndex={0}
      >
        <div className="flex items-start justify-between mb-3">
          {/* Lead Sheet Letter Badge */}
          <div className="flex items-center gap-3">
            <div className={`
              w-10 h-10 rounded-lg flex items-center justify-center
              ${colors.accent} text-white font-mono font-bold text-lg
            `}>
              {summary.lead_sheet}
            </div>
            <div>
              <h4 className="font-serif text-sm font-medium text-content-primary">
                {summary.lead_sheet_name}
              </h4>
              <p className="text-xs text-content-tertiary capitalize">
                {summary.category}
              </p>
            </div>
          </div>

          {/* Account Count */}
          <div className="text-right">
            <div className="text-xs text-content-tertiary">Accounts</div>
            <div className={`font-mono text-lg font-bold ${colors.text}`}>
              {summary.account_count}
            </div>
          </div>
        </div>

        {/* Totals Row */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="p-2 rounded-lg bg-surface-card-secondary">
            <div className="text-[10px] uppercase tracking-wider text-content-tertiary mb-0.5">
              Debits
            </div>
            <div className="font-mono text-sm text-sage-400">
              {formatCurrency(summary.total_debit)}
            </div>
          </div>
          <div className="p-2 rounded-lg bg-surface-card-secondary">
            <div className="text-[10px] uppercase tracking-wider text-content-tertiary mb-0.5">
              Credits
            </div>
            <div className="font-mono text-sm text-clay-400">
              {formatCurrency(summary.total_credit)}
            </div>
          </div>
          <div className="p-2 rounded-lg bg-surface-card-secondary">
            <div className="text-[10px] uppercase tracking-wider text-content-tertiary mb-0.5">
              Net
            </div>
            <div className={`font-mono text-sm font-medium ${
              summary.net_balance >= 0 ? 'text-sage-400' : 'text-clay-400'
            }`}>
              {formatCurrency(summary.net_balance)}
            </div>
          </div>
        </div>

        {/* Expand indicator */}
        <div className="flex justify-center mt-3">
          <motion.span
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="text-xs text-content-tertiary"
          >
            ▼
          </motion.span>
        </div>
      </div>

      {/* Expanded Account List */}
      <AnimatePresence>
        {isExpanded && summary.accounts.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-theme overflow-hidden"
          >
            <div className="max-h-64 overflow-y-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-surface-elevated">
                  <tr className="text-content-tertiary uppercase tracking-wider">
                    <th className="text-left p-2 font-medium">Account</th>
                    <th className="text-right p-2 font-medium">Debit</th>
                    <th className="text-right p-2 font-medium">Credit</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.accounts.map((account, idx) => (
                    <tr
                      key={`${account.account}-${idx}`}
                      className="border-t border-theme-divider hover:bg-surface-card-secondary transition-colors"
                    >
                      <td className="p-2 text-content-primary truncate max-w-[200px]" title={account.account}>
                        {account.account}
                      </td>
                      <td className="p-2 text-right font-mono text-sage-400">
                        {account.debit > 0 ? formatFullCurrency(account.debit) : '-'}
                      </td>
                      <td className="p-2 text-right font-mono text-clay-400">
                        {account.credit > 0 ? formatFullCurrency(account.credit) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default LeadSheetCard
