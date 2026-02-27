'use client'

/**
 * BenchmarkCard - Sprint 46 Benchmark Comparison Display
 *
 * Displays a single ratio's benchmark comparison with percentile
 * position, interpretation, and visual indicator.
 *
 * Features:
 * - Ratio name and client value display
 * - PercentileBar visualization
 * - Interpretation text
 * - Source attribution
 * - Animated entrance with stagger support
 * - Oat & Obsidian theme compliance
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Display component only, no data persistence
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { BenchmarkComparisonResult } from '@/hooks/useBenchmarks'
import { createCardStaggerVariants } from '@/utils'
import { PercentileBar } from './PercentileBar'

interface BenchmarkCardProps {
  /** Comparison result from API */
  comparison: BenchmarkComparisonResult
  /** Index for stagger animation */
  index?: number
  /** Show benchmark reference values */
  showBenchmarkValues?: boolean
}

/** Ratios where lower is better */
const LOWER_IS_BETTER_RATIOS = [
  'debt_to_equity',
  'days_sales_outstanding',
  'days_inventory_outstanding',
]

/** Format ratio name for display */
function formatRatioName(name: string): string {
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/** Format ratio value for display */
function formatRatioValue(value: number, ratioName: string): string {
  // Percentage ratios
  if (ratioName.includes('margin') || ratioName === 'roa' || ratioName === 'roe') {
    return `${(value * 100).toFixed(1)}%`
  }
  // Turnover ratios
  if (ratioName.includes('turnover')) {
    return `${value.toFixed(1)}x`
  }
  // Standard ratios
  return value.toFixed(2)
}

/** Get position badge color classes */
function getPositionClasses(position: string): { bg: string; text: string } {
  switch (position) {
    case 'excellent':
      return { bg: 'bg-sage-500/20', text: 'text-sage-400' }
    case 'above_average':
      return { bg: 'bg-sage-500/10', text: 'text-sage-400' }
    case 'average':
      return { bg: 'bg-oatmeal-500/20', text: 'text-content-secondary' }
    case 'below_average':
      return { bg: 'bg-oatmeal-600/20', text: 'text-content-tertiary' }
    case 'concerning':
      return { bg: 'bg-clay-500/20', text: 'text-clay-400' }
    case 'critical':
      return { bg: 'bg-clay-500/30', text: 'text-clay-400' }
    default:
      return { bg: 'bg-obsidian-600', text: 'text-content-secondary' }
  }
}

/** Format position label */
function formatPositionLabel(position: string): string {
  return position
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * BenchmarkCard Component
 */
export function BenchmarkCard({
  comparison,
  index = 0,
  showBenchmarkValues = false,
}: BenchmarkCardProps) {
  const [showDetails, setShowDetails] = useState(false)

  const cardVariants = createCardStaggerVariants(index, 50)
  const positionClasses = getPositionClasses(comparison.position)
  const lowerIsBetter = LOWER_IS_BETTER_RATIOS.includes(comparison.ratio_name)

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      custom={index}
      className="
        relative rounded-xl border border-theme
        bg-surface-card backdrop-blur-xs
        p-4 transition-all duration-base
        hover:border-theme-hover hover:shadow-theme-card-hover
      "
      onMouseEnter={() => setShowDetails(true)}
      onMouseLeave={() => setShowDetails(false)}
    >
      {/* Header: Ratio Name + Position Badge */}
      <div className="flex items-start justify-between mb-3">
        <h4 className="font-serif text-sm font-medium text-content-primary">
          {formatRatioName(comparison.ratio_name)}
        </h4>
        <span className={`
          inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-medium
          ${positionClasses.bg} ${positionClasses.text}
        `}>
          {formatPositionLabel(comparison.position)}
        </span>
      </div>

      {/* Client Value */}
      <div className="flex items-baseline gap-2 mb-4">
        <span className="font-mono text-2xl font-bold text-content-primary">
          {formatRatioValue(comparison.client_value, comparison.ratio_name)}
        </span>
        <span className="font-mono text-xs text-content-tertiary">
          {comparison.percentile_label}
        </span>
      </div>

      {/* Percentile Bar */}
      <div className="mb-4">
        <PercentileBar
          percentile={comparison.percentile}
          healthIndicator={comparison.health_indicator}
          lowerIsBetter={lowerIsBetter}
          size="md"
        />
      </div>

      {/* Interpretation */}
      <p className="text-xs text-content-secondary leading-relaxed mb-3">
        {comparison.interpretation}
      </p>

      {/* Benchmark Reference Values (expandable) */}
      <AnimatePresence>
        {(showDetails || showBenchmarkValues) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="pt-3 border-t border-theme">
              <div className="flex justify-between text-xs">
                <div className="text-content-tertiary">
                  <span className="block text-[10px] uppercase tracking-wider mb-0.5">
                    Industry Median
                  </span>
                  <span className="font-mono text-content-secondary">
                    {formatRatioValue(comparison.benchmark_median, comparison.ratio_name)}
                  </span>
                </div>
                <div className="text-content-tertiary text-right">
                  <span className="block text-[10px] uppercase tracking-wider mb-0.5">
                    Industry Mean
                  </span>
                  <span className="font-mono text-content-secondary">
                    {formatRatioValue(comparison.benchmark_mean, comparison.ratio_name)}
                  </span>
                </div>
              </div>

              {/* vs Median/Mean indicators */}
              <div className="flex gap-4 mt-2 text-xs">
                <span className={`font-mono ${
                  comparison.vs_median >= 0 ? 'text-sage-400' : 'text-clay-400'
                }`}>
                  {comparison.vs_median >= 0 ? '+' : ''}
                  {(comparison.vs_median * 100).toFixed(1)}% vs median
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hover hint */}
      {!showBenchmarkValues && (
        <div className="absolute bottom-2 right-2">
          <span className="text-[10px] text-oatmeal-600 opacity-50">
            Hover for details
          </span>
        </div>
      )}
    </motion.div>
  )
}

export default BenchmarkCard
