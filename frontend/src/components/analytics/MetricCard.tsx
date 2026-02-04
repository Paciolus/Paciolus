'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  getHealthClasses,
  getHealthLabel,
  getVarianceClasses,
  createCardStaggerVariants,
  type HealthStatus,
  type VarianceDirection,
} from '@/utils'

// Formula definitions for tooltips - Sprint 28 + Sprint 30 IFRS/GAAP notes
export const RATIO_FORMULAS: Record<string, { formula: string; description: string; standardNote?: string }> = {
  'Current Ratio': {
    formula: 'Current Assets ÷ Current Liabilities',
    description: 'Measures short-term liquidity and ability to pay debts within one year',
    standardNote: 'IFRS/GAAP: Both require current/non-current classification',
  },
  'Quick Ratio': {
    formula: '(Current Assets − Inventory) ÷ Current Liabilities',
    description: 'Acid-test ratio excluding inventory for stricter liquidity assessment',
    standardNote: 'Note: LIFO inventory (US GAAP only) may affect comparability with IFRS',
  },
  'Debt-to-Equity': {
    formula: 'Total Liabilities ÷ Total Equity',
    description: 'Measures financial leverage and long-term solvency',
    standardNote: 'IFRS/GAAP: Equity composition may differ (redeemable preferred, revaluations)',
  },
  'Gross Margin': {
    formula: '(Revenue − COGS) ÷ Revenue × 100%',
    description: 'Profitability before operating expenses as percentage of revenue',
    standardNote: 'Revenue recognition converged (ASC 606/IFRS 15) since 2018',
  },
  'Net Profit Margin': {
    formula: '(Revenue − Total Expenses) ÷ Revenue × 100%',
    description: 'Bottom-line profitability after all expenses',
    standardNote: 'IFRS may capitalize R&D development costs, shifting expense timing',
  },
  'Operating Margin': {
    formula: '(Revenue − COGS − OpEx) ÷ Revenue × 100%',
    description: 'Profitability from core operations before interest and taxes',
    standardNote: 'Lease expense differs: single line (US GAAP) vs depreciation+interest (IFRS)',
  },
  'Return on Assets': {
    formula: 'Net Income ÷ Total Assets × 100%',
    description: 'Efficiency of asset utilization to generate earnings',
    standardNote: 'IFRS revaluations can inflate assets, reducing apparent ROA',
  },
  'Return on Equity': {
    formula: 'Net Income ÷ Total Equity × 100%',
    description: 'Return generated on shareholder investment',
    standardNote: 'Revaluation surplus (IFRS) may inflate equity denominator',
  },
}

interface MetricCardProps {
  name: string
  value: string
  interpretation: string
  healthStatus: HealthStatus
  variance?: {
    direction: VarianceDirection
    displayText: string
    changePercent: number
  }
  index: number
  isCalculable: boolean
  compact?: boolean
}

/**
 * MetricCard - Sprint 28 Enhanced Analytics Component
 *
 * Displays a single financial metric with Tier 2 semantic colors.
 * Sage (#4A7C59) for positive/healthy, Clay (#BC4749) for negative/concern.
 *
 * Features:
 * - Tier 1 staggered entrance animation (40ms delay)
 * - Health status indicator with semantic colors
 * - Variance display with trend direction
 * - Formula tooltip on hover (Sprint 28)
 * - Compact mode for advanced ratios section (Sprint 28)
 * - Animated value changes (Sprint 28)
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */
export function MetricCard({
  name,
  value,
  interpretation,
  healthStatus,
  variance,
  index,
  isCalculable,
  compact = false,
}: MetricCardProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  // Card entrance animation with stagger
  const cardVariants = createCardStaggerVariants(index, 40)

  // Get health classes from shared utilities
  const healthClasses = getHealthClasses(healthStatus)

  // Get formula info for tooltip
  const formulaInfo = RATIO_FORMULAS[name]

  // Trend indicator icons - Sprint 28
  const getTrendIcon = (direction: VarianceDirection) => {
    switch (direction) {
      case 'positive':
        return (
          <motion.span
            initial={{ y: 3, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="text-sage-400"
          >
            ↑
          </motion.span>
        )
      case 'negative':
        return (
          <motion.span
            initial={{ y: -3, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="text-clay-400"
          >
            ↓
          </motion.span>
        )
      default:
        return (
          <motion.span
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-oatmeal-500"
          >
            →
          </motion.span>
        )
    }
  }

  // Variance arrow icon
  const getVarianceIcon = (direction: VarianceDirection) => {
    switch (direction) {
      case 'positive':
        return (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
        )
      case 'negative':
        return (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        )
      default:
        return (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
          </svg>
        )
    }
  }

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      className={`
        relative rounded-xl border ${healthClasses.border} ${healthClasses.bg}
        ${compact ? 'p-3' : 'p-4'} transition-all hover:border-opacity-50
        group cursor-default
      `}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {/* Formula Tooltip - Sprint 28 + Sprint 30 IFRS/GAAP notes */}
      <AnimatePresence>
        {showTooltip && formulaInfo && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.95 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-3
                       bg-obsidian-900 border border-obsidian-600 rounded-lg shadow-xl"
          >
            <div className="text-xs font-sans">
              <div className="text-oatmeal-300 font-medium mb-1">Formula</div>
              <code className="text-sage-300 font-mono text-[11px] block mb-2 bg-obsidian-800 rounded px-2 py-1">
                {formulaInfo.formula}
              </code>
              <p className="text-oatmeal-500 leading-relaxed mb-2">
                {formulaInfo.description}
              </p>
              {/* Sprint 30: IFRS/GAAP Standards Note */}
              {formulaInfo.standardNote && (
                <div className="pt-2 border-t border-obsidian-700">
                  <p className="text-oatmeal-600 text-[10px] leading-relaxed italic">
                    {formulaInfo.standardNote}
                  </p>
                </div>
              )}
            </div>
            {/* Tooltip arrow */}
            <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-[1px]">
              <div className="border-8 border-transparent border-t-obsidian-600" />
              <div className="border-8 border-transparent border-t-obsidian-900 -mt-[17px]" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header: Name, Trend, and Health Badge */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <h4 className={`font-sans font-medium text-oatmeal-200 ${compact ? 'text-xs' : 'text-sm'}`}>
            {name}
          </h4>
          {/* Info icon hint for tooltip */}
          <svg
            className="w-3 h-3 text-oatmeal-600 opacity-0 group-hover:opacity-100 transition-opacity"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <div className="flex items-center gap-2">
          {/* Trend indicator - Sprint 28 */}
          {variance && (
            <span className="text-sm font-mono">
              {getTrendIcon(variance.direction)}
            </span>
          )}
          {isCalculable && (
            <span className={`text-xs font-sans px-2 py-0.5 rounded-full ${healthClasses.badge}`}>
              {getHealthLabel(healthStatus)}
            </span>
          )}
        </div>
      </div>

      {/* Value with animated updates */}
      <div className={compact ? 'mb-1' : 'mb-2'}>
        <motion.span
          key={value}
          initial={{ opacity: 0.5, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.2 }}
          className={`font-mono font-bold ${isCalculable ? 'text-oatmeal-100' : 'text-oatmeal-500'} ${compact ? 'text-xl' : 'text-2xl'}`}
        >
          {value}
        </motion.span>
      </div>

      {/* Variance (if available) */}
      {variance && !compact && (
        <div className={`flex items-center gap-1 mb-2 ${getVarianceClasses(variance.direction)}`}>
          {getVarianceIcon(variance.direction)}
          <span className="text-xs font-sans font-medium">
            {variance.displayText}
          </span>
          <span className="text-xs text-oatmeal-500 font-sans">
            vs last
          </span>
        </div>
      )}

      {/* Interpretation */}
      {!compact && (
        <p className="text-xs font-sans text-oatmeal-400 leading-relaxed">
          {interpretation}
        </p>
      )}
      {compact && (
        <p className="text-[10px] font-sans text-oatmeal-500 leading-tight truncate">
          {interpretation}
        </p>
      )}
    </motion.div>
  )
}
