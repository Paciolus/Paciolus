'use client'

import { motion } from 'framer-motion'
import {
  getHealthClasses,
  getHealthLabel,
  getVarianceClasses,
  createCardStaggerVariants,
  type HealthStatus,
  type VarianceDirection,
} from '@/utils'

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
}

/**
 * MetricCard - Sprint 19 Analytics Component
 *
 * Displays a single financial metric with Tier 2 semantic colors.
 * Sage (#4A7C59) for positive/healthy, Clay (#BC4749) for negative/concern.
 *
 * Features:
 * - Tier 1 staggered entrance animation (40ms delay)
 * - Health status indicator with semantic colors
 * - Variance display with trend direction
 *
 * Phase 2 Refactor: Uses shared themeUtils
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
}: MetricCardProps) {
  // Card entrance animation with stagger
  const cardVariants = createCardStaggerVariants(index, 40)

  // Get health classes from shared utilities
  const healthClasses = getHealthClasses(healthStatus)

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
        rounded-xl border ${healthClasses.border} ${healthClasses.bg}
        p-4 transition-all hover:border-opacity-50
      `}
    >
      {/* Header: Name and Health Badge */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <h4 className="font-sans font-medium text-oatmeal-200 text-sm">
          {name}
        </h4>
        {isCalculable && (
          <span className={`text-xs font-sans px-2 py-0.5 rounded-full ${healthClasses.badge}`}>
            {getHealthLabel(healthStatus)}
          </span>
        )}
      </div>

      {/* Value */}
      <div className="mb-2">
        <span className={`font-mono text-2xl font-bold ${isCalculable ? 'text-oatmeal-100' : 'text-oatmeal-500'}`}>
          {value}
        </span>
      </div>

      {/* Variance (if available) */}
      {variance && (
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
      <p className="text-xs font-sans text-oatmeal-400 leading-relaxed">
        {interpretation}
      </p>
    </motion.div>
  )
}
