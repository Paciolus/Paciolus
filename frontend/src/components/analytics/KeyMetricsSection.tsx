'use client'

import { motion } from 'framer-motion'
import { MetricCard } from './MetricCard'

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

/**
 * KeyMetricsSection - Sprint 19 Analytics Dashboard
 *
 * Displays key financial metrics calculated from the diagnostic run.
 * Uses Tier 2 semantic colors and Tier 1 staggered entrance animations.
 *
 * Features:
 * - Four core ratios: Current, Quick, Debt-to-Equity, Gross Margin
 * - Variance Intelligence (vs previous diagnostic)
 * - Staggered card entrance (40ms delay per card)
 * - Premium Oat & Obsidian styling
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */
export function KeyMetricsSection({
  analytics,
  disabled = false,
}: KeyMetricsSectionProps) {
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
  const hasCalculableRatios = Object.values(analytics.ratios).some(r => r.is_calculable)

  // Map ratio key to variance key
  const ratioToVarianceMap: Record<string, string> = {
    current_ratio: 'current_assets',
    quick_ratio: 'current_assets',
    debt_to_equity: 'total_liabilities',
    gross_margin: 'total_revenue',
  }

  // Build metric cards data
  const ratioEntries = Object.entries(analytics.ratios) as [string, RatioData][]

  return (
    <div className={`${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      {/* Section Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-sage-500/10 flex items-center justify-center">
            <svg
              className="w-4 h-4 text-sage-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <div>
            <h3 className="font-serif font-semibold text-oatmeal-200 text-lg">
              Key Metrics
            </h3>
            <p className="text-oatmeal-500 text-xs font-sans">
              Financial ratio intelligence
            </p>
          </div>
        </div>

        {/* Variance badge */}
        {analytics.has_previous_data && (
          <div className="flex items-center gap-2 bg-sage-500/10 border border-sage-500/20 rounded-full px-3 py-1">
            <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
            <span className="text-sage-300 text-xs font-sans font-medium">
              Variance Active
            </span>
          </div>
        )}
      </div>

      {/* Metrics Grid */}
      {hasCalculableRatios ? (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-2 md:grid-cols-4 gap-4"
        >
          {ratioEntries.map(([key, ratio], index) => {
            // Get variance data if available
            const varianceKey = ratioToVarianceMap[key]
            const variance = varianceKey && analytics.variances[varianceKey]
              ? {
                  direction: analytics.variances[varianceKey].direction,
                  displayText: analytics.variances[varianceKey].display_text,
                  changePercent: analytics.variances[varianceKey].change_percent,
                }
              : undefined

            return (
              <MetricCard
                key={key}
                name={ratio.name}
                value={ratio.display_value}
                interpretation={ratio.interpretation}
                healthStatus={ratio.health_status}
                variance={analytics.has_previous_data ? variance : undefined}
                index={index}
                isCalculable={ratio.is_calculable}
              />
            )
          })}
        </motion.div>
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
}

export default KeyMetricsSection
