'use client'

import { useState, memo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MetricCard } from './MetricCard'
import { SectionHeader } from '@/components/shared'

interface RatioData {
  name: string
  value: number | null
  display_value: string
  is_calculable: boolean
  interpretation: string
  health_status: 'healthy' | 'warning' | 'concern' | 'neutral'
}

interface VarianceData {
  metric_name: string
  current_value: number
  previous_value: number
  change_amount: number
  change_percent: number
  direction: 'positive' | 'negative' | 'neutral'
  display_text: string
}

interface Analytics {
  ratios: {
    current_ratio: RatioData
    quick_ratio: RatioData
    debt_to_equity: RatioData
    gross_margin: RatioData
    net_profit_margin?: RatioData
    operating_margin?: RatioData
    return_on_assets?: RatioData
    return_on_equity?: RatioData
  }
  variances: Record<string, VarianceData>
  has_previous_data: boolean
  category_totals: {
    total_assets: number
    current_assets: number
    total_liabilities: number
    total_equity: number
    total_revenue: number
  }
}

interface KeyMetricsSectionProps {
  analytics: Analytics
  disabled?: boolean
}

// Core ratios (always visible) vs Advanced ratios (collapsible)
const CORE_RATIO_KEYS = ['current_ratio', 'quick_ratio', 'debt_to_equity', 'gross_margin'] as const
const ADVANCED_RATIO_KEYS = ['net_profit_margin', 'operating_margin', 'return_on_assets', 'return_on_equity'] as const

// Map ratio key to variance key - moved outside component to prevent recreation on every render
const RATIO_TO_VARIANCE_MAP: Record<string, string> = {
  current_ratio: 'current_assets',
  quick_ratio: 'current_assets',
  debt_to_equity: 'total_liabilities',
  gross_margin: 'total_revenue',
  net_profit_margin: 'total_revenue',
  operating_margin: 'total_revenue',
  return_on_assets: 'total_assets',
  return_on_equity: 'total_equity',
}

/**
 * KeyMetricsSection - Sprint 28 Enhanced Analytics Dashboard
 *
 * Displays key financial metrics calculated from the diagnostic run.
 * Uses Tier 2 semantic colors and Tier 1 staggered entrance animations.
 *
 * Features (Sprint 28 Enhanced):
 * - Eight ratios: Core 4 + Advanced 4 (collapsible)
 * - 2-column responsive grid layout
 * - Formula tooltips on hover
 * - Variance Intelligence with trend indicators (↑↓→)
 * - Staggered card entrance (40ms delay per card)
 * - Premium Oat & Obsidian styling
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */
/**
 * KeyMetricsSection wrapped with React.memo() to prevent unnecessary re-renders.
 * Only re-renders when analytics data or disabled state changes.
 */
export const KeyMetricsSection = memo(function KeyMetricsSection({
  analytics,
  disabled = false,
}: KeyMetricsSectionProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Container animation for staggered children
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.04,
        delayChildren: 0.1,
      },
    },
  }

  // Check if we have any calculable ratios
  const hasCalculableRatios = Object.values(analytics.ratios).some(r => r?.is_calculable)

  // Check if we have advanced ratios available
  const hasAdvancedRatios = ADVANCED_RATIO_KEYS.some(
    key => analytics.ratios[key]?.is_calculable
  )

  // Get variance for a ratio (uses module-level constant for performance)
  const getVarianceForRatio = (key: string) => {
    const varianceKey = RATIO_TO_VARIANCE_MAP[key]
    if (!varianceKey || !analytics.variances[varianceKey]) return undefined
    return {
      direction: analytics.variances[varianceKey].direction,
      displayText: analytics.variances[varianceKey].display_text,
      changePercent: analytics.variances[varianceKey].change_percent,
    }
  }

  // Build core ratio entries (always visible) - with type guard
  const coreRatios = CORE_RATIO_KEYS
    .map(key => ({ key, ratio: analytics.ratios[key] }))
    .filter((entry): entry is { key: typeof CORE_RATIO_KEYS[number]; ratio: RatioData } =>
      entry.ratio !== undefined
    )

  // Build advanced ratio entries (collapsible) - with type guard
  const advancedRatios = ADVANCED_RATIO_KEYS
    .map(key => ({ key, ratio: analytics.ratios[key] }))
    .filter((entry): entry is { key: typeof ADVANCED_RATIO_KEYS[number]; ratio: RatioData } =>
      entry.ratio !== undefined
    )

  return (
    <div className={`${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      {/* Section Header - Using shared SectionHeader component */}
      <SectionHeader
        title="Key Metrics"
        subtitle={hasAdvancedRatios ? '8 financial ratios' : 'Financial ratio intelligence'}
        accentColor="sage"
        icon={
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        }
        badge={
          analytics.has_previous_data && (
            <div className="flex items-center gap-2 bg-sage-500/10 border border-sage-500/20 rounded-full px-3 py-1">
              <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
              <span className="text-sage-300 text-xs font-sans font-medium">
                Variance Active
              </span>
            </div>
          )
        }
        animate={false}
      />

      {/* Core Metrics Grid - 2 columns */}
      {hasCalculableRatios ? (
        <>
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 sm:grid-cols-2 gap-4"
          >
            {coreRatios.map(({ key, ratio }, index) => (
              <MetricCard
                key={key}
                name={ratio.name}
                value={ratio.display_value}
                interpretation={ratio.interpretation}
                healthStatus={ratio.health_status}
                variance={analytics.has_previous_data ? getVarianceForRatio(key) : undefined}
                index={index}
                isCalculable={ratio.is_calculable}
              />
            ))}
          </motion.div>

          {/* Advanced Ratios Collapsible Section */}
          {hasAdvancedRatios && (
            <div className="mt-4">
              {/* Toggle Button */}
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="w-full flex items-center justify-center gap-2 py-2 px-4
                           bg-obsidian-800/30 hover:bg-obsidian-800/50
                           border border-obsidian-700/50 hover:border-obsidian-600/50
                           rounded-lg transition-all group"
              >
                <span className="text-xs font-sans text-oatmeal-400 group-hover:text-oatmeal-300">
                  {showAdvanced ? 'Hide' : 'Show'} Advanced Ratios
                </span>
                <span className="text-oatmeal-500 text-xs">
                  ({advancedRatios.filter(r => r.ratio?.is_calculable).length} available)
                </span>
                <motion.svg
                  animate={{ rotate: showAdvanced ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                  className="w-4 h-4 text-oatmeal-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </motion.svg>
              </button>

              {/* Advanced Ratios Grid */}
              <AnimatePresence>
                {showAdvanced && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25, ease: 'easeInOut' }}
                    className="overflow-hidden"
                  >
                    <motion.div
                      variants={containerVariants}
                      initial="hidden"
                      animate="visible"
                      className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4 pt-4 border-t border-obsidian-700/30"
                    >
                      {advancedRatios.map(({ key, ratio }, index) => (
                        <MetricCard
                          key={key}
                          name={ratio.name}
                          value={ratio.display_value}
                          interpretation={ratio.interpretation}
                          healthStatus={ratio.health_status}
                          variance={analytics.has_previous_data ? getVarianceForRatio(key) : undefined}
                          index={index}
                          isCalculable={ratio.is_calculable}
                          compact
                        />
                      ))}
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </>
      ) : (
        // Empty state when no ratios calculable
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-obsidian-800/50 rounded-xl border border-obsidian-600/50 p-6 text-center"
        >
          <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-obsidian-700/50 flex items-center justify-center">
            <svg
              className="w-6 h-6 text-oatmeal-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <h4 className="font-sans font-medium text-oatmeal-300 mb-1">
            Limited Account Classification
          </h4>
          <p className="text-oatmeal-500 text-sm font-sans max-w-sm mx-auto">
            Ratio calculations require classified accounts. Upload a trial balance
            with standard account names for ratio analysis.
          </p>
        </motion.div>
      )}

      {/* Category Totals Summary (compact) */}
      {hasCalculableRatios && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-4 pt-4 border-t border-obsidian-700/50"
        >
          <div className="flex flex-wrap gap-4 justify-center text-xs font-sans text-oatmeal-500">
            <span>
              Assets: <span className="text-oatmeal-300 font-mono">${analytics.category_totals.total_assets.toLocaleString()}</span>
            </span>
            <span>
              Liabilities: <span className="text-oatmeal-300 font-mono">${analytics.category_totals.total_liabilities.toLocaleString()}</span>
            </span>
            <span>
              Equity: <span className="text-oatmeal-300 font-mono">${analytics.category_totals.total_equity.toLocaleString()}</span>
            </span>
            {analytics.category_totals.total_revenue > 0 && (
              <span>
                Revenue: <span className="text-oatmeal-300 font-mono">${analytics.category_totals.total_revenue.toLocaleString()}</span>
              </span>
            )}
          </div>
        </motion.div>
      )}
    </div>
  )
})

// Display name for React DevTools
KeyMetricsSection.displayName = 'KeyMetricsSection'

export default KeyMetricsSection
