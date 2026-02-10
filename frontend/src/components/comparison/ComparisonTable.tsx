'use client'

/**
 * ComparisonTable - Sprint 51 Prior Period Comparison Table
 *
 * Displays side-by-side comparison of current vs prior period
 * with variance highlighting for significant changes.
 *
 * Features:
 * - Balance sheet and income statement sections
 * - Dollar and percent variance columns
 * - Significant variance highlighting (Clay Red)
 * - Trend direction arrows
 * - Collapsible sections
 * - Oat & Obsidian theme compliance
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Display component only, no data persistence
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { CategoryVariance, RatioVariance, PeriodComparison } from '@/types/priorPeriod'
import { getVarianceColors } from '@/types/priorPeriod'

interface ComparisonTableProps {
  /** Comparison data */
  comparison: PeriodComparison
  /** Loading state */
  isLoading?: boolean
  /** Disabled state */
  disabled?: boolean
}

/**
 * Format currency for display
 */
function formatCurrency(value: number): string {
  const absValue = Math.abs(value)
  const sign = value < 0 ? '-' : ''

  if (absValue >= 1_000_000) {
    return `${sign}$${(absValue / 1_000_000).toFixed(1)}M`
  } else if (absValue >= 1_000) {
    return `${sign}$${(absValue / 1_000).toFixed(1)}K`
  }
  return `${sign}$${absValue.toFixed(0)}`
}

/**
 * Format percent for display
 */
function formatPercent(value: number | null): string {
  if (value === null) return 'N/A'
  if (!isFinite(value)) return value > 0 ? '+∞' : '-∞'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}

/**
 * Format ratio for display
 */
function formatRatio(value: number | null, isPercentage: boolean): string {
  if (value === null) return 'N/A'
  if (isPercentage) {
    return `${(value * 100).toFixed(1)}%`
  }
  return value.toFixed(2)
}

/**
 * Format point change for ratios
 */
function formatPointChange(value: number | null, isPercentage: boolean): string {
  if (value === null) return 'N/A'
  const sign = value > 0 ? '+' : ''
  if (isPercentage) {
    return `${sign}${(value * 100).toFixed(1)}pp`
  }
  return `${sign}${value.toFixed(2)}`
}

/**
 * Category variance row component
 */
function CategoryRow({ variance }: { variance: CategoryVariance }) {
  const colors = getVarianceColors(variance.direction, variance.is_significant)

  return (
    <tr className={`border-t border-theme-divider hover:bg-surface-card-secondary transition-colors ${variance.is_significant ? colors.bg : ''}`}>
      <td className="p-3 text-content-primary">{variance.category_name}</td>
      <td className="p-3 text-right font-mono text-content-primary">
        {formatCurrency(variance.current_value)}
      </td>
      <td className="p-3 text-right font-mono text-content-secondary">
        {formatCurrency(variance.prior_value)}
      </td>
      <td className={`p-3 text-right font-mono ${colors.text}`}>
        <span className="mr-1">{colors.icon}</span>
        {formatCurrency(variance.dollar_variance)}
      </td>
      <td className={`p-3 text-right font-mono ${colors.text}`}>
        {formatPercent(variance.percent_variance)}
      </td>
    </tr>
  )
}

/**
 * Ratio variance row component
 */
function RatioRow({ variance }: { variance: RatioVariance }) {
  const colors = getVarianceColors(variance.direction, variance.is_significant)

  return (
    <tr className={`border-t border-theme-divider hover:bg-surface-card-secondary transition-colors ${variance.is_significant ? colors.bg : ''}`}>
      <td className="p-3 text-content-primary">{variance.ratio_name}</td>
      <td className="p-3 text-right font-mono text-content-primary">
        {formatRatio(variance.current_value, variance.is_percentage)}
      </td>
      <td className="p-3 text-right font-mono text-content-secondary">
        {formatRatio(variance.prior_value, variance.is_percentage)}
      </td>
      <td className={`p-3 text-right font-mono ${colors.text}`} colSpan={2}>
        <span className="mr-1">{colors.icon}</span>
        {formatPointChange(variance.point_change, variance.is_percentage)}
      </td>
    </tr>
  )
}

/**
 * Collapsible section component
 */
function CollapsibleSection({
  title,
  icon,
  children,
  defaultOpen = true,
}: {
  title: string
  icon: string
  children: React.ReactNode
  defaultOpen?: boolean
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="mb-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-surface-card rounded-t-lg border border-theme hover:bg-surface-card-secondary transition-colors"
      >
        <div className="flex items-center gap-2">
          <span>{icon}</span>
          <span className="font-serif text-sm font-medium text-content-primary">{title}</span>
        </div>
        <motion.span
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-content-tertiary"
        >
          ▼
        </motion.span>
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="border border-t-0 border-theme rounded-b-lg overflow-hidden">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/**
 * ComparisonTable Component
 */
export function ComparisonTable({
  comparison,
  isLoading = false,
  disabled = false,
}: ComparisonTableProps) {
  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-32 bg-surface-card-secondary rounded-lg" />
        ))}
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={disabled ? 'opacity-50 pointer-events-none' : ''}
    >
      {/* Header with period labels */}
      <div className="flex items-center justify-between mb-4 p-3 bg-surface-card rounded-lg border border-theme shadow-theme-card">
        <div>
          <div className="text-xs text-content-tertiary uppercase tracking-wider">Comparing</div>
          <div className="text-sm font-medium text-content-primary">
            {comparison.current_period_label} vs {comparison.prior_period_label}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-content-tertiary uppercase tracking-wider">Significant Variances</div>
          <div className={`text-lg font-mono font-bold ${comparison.significant_variance_count > 0 ? 'text-clay-600' : 'text-sage-600'}`}>
            {comparison.significant_variance_count} / {comparison.total_categories_compared}
          </div>
        </div>
      </div>

      {/* Balance Sheet Comparison */}
      <CollapsibleSection title="Balance Sheet" icon="📊">
        <table className="w-full text-sm">
          <thead className="bg-surface-card-secondary">
            <tr className="text-content-secondary font-serif uppercase tracking-wider text-xs">
              <th className="text-left p-3 font-medium">Category</th>
              <th className="text-right p-3 font-medium">Current</th>
              <th className="text-right p-3 font-medium">Prior</th>
              <th className="text-right p-3 font-medium">$ Var</th>
              <th className="text-right p-3 font-medium">% Var</th>
            </tr>
          </thead>
          <tbody>
            {comparison.balance_sheet_variances.map((v) => (
              <CategoryRow key={v.category_key} variance={v} />
            ))}
          </tbody>
        </table>
      </CollapsibleSection>

      {/* Income Statement Comparison */}
      <CollapsibleSection title="Income Statement" icon="📈">
        <table className="w-full text-sm">
          <thead className="bg-surface-card-secondary">
            <tr className="text-content-secondary font-serif uppercase tracking-wider text-xs">
              <th className="text-left p-3 font-medium">Category</th>
              <th className="text-right p-3 font-medium">Current</th>
              <th className="text-right p-3 font-medium">Prior</th>
              <th className="text-right p-3 font-medium">$ Var</th>
              <th className="text-right p-3 font-medium">% Var</th>
            </tr>
          </thead>
          <tbody>
            {comparison.income_statement_variances.map((v) => (
              <CategoryRow key={v.category_key} variance={v} />
            ))}
          </tbody>
        </table>
      </CollapsibleSection>

      {/* Ratios Comparison */}
      <CollapsibleSection title="Financial Ratios" icon="📐" defaultOpen={false}>
        <table className="w-full text-sm">
          <thead className="bg-surface-card-secondary">
            <tr className="text-content-secondary font-serif uppercase tracking-wider text-xs">
              <th className="text-left p-3 font-medium">Ratio</th>
              <th className="text-right p-3 font-medium">Current</th>
              <th className="text-right p-3 font-medium">Prior</th>
              <th className="text-right p-3 font-medium" colSpan={2}>Change</th>
            </tr>
          </thead>
          <tbody>
            {comparison.ratio_variances.map((v) => (
              <RatioRow key={v.ratio_key} variance={v} />
            ))}
          </tbody>
        </table>
      </CollapsibleSection>
    </motion.div>
  )
}

export default ComparisonTable
