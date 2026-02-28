'use client'

import { useState, memo } from 'react'
import { motion } from 'framer-motion'
import { SectionHeader, CollapsibleSection, EmptyStateCard, ChartIcon } from '@/components/shared'
import { CONTAINER_VARIANTS } from '@/utils'
import { MetricCard } from './MetricCard'

interface RatioData {
  name: string
  value: number | null
  display_value: string
  is_calculable: boolean
  interpretation: string
  threshold_status: 'above_threshold' | 'at_threshold' | 'below_threshold' | 'neutral'
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
    dso?: RatioData  // Sprint 53: Days Sales Outstanding
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
const ADVANCED_RATIO_KEYS = ['net_profit_margin', 'operating_margin', 'return_on_assets', 'return_on_equity', 'dso'] as const

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
  dso: 'total_revenue',  // Sprint 53: DSO varies with revenue changes
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
        subtitle={hasAdvancedRatios ? '9 financial ratios' : 'Financial ratio intelligence'}
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
            variants={CONTAINER_VARIANTS.fast}
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
                healthStatus={ratio.threshold_status}
                variance={analytics.has_previous_data ? getVarianceForRatio(key) : undefined}
                index={index}
                isCalculable={ratio.is_calculable}
              />
            ))}
          </motion.div>

          {/* Advanced Ratios Collapsible Section */}
          {hasAdvancedRatios && (
            <CollapsibleSection
              label="Advanced Ratios"
              itemCount={advancedRatios.filter(r => r.ratio?.is_calculable).length}
              isExpanded={showAdvanced}
              onToggle={() => setShowAdvanced(!showAdvanced)}
            >
              <motion.div
                variants={CONTAINER_VARIANTS.fast}
                initial="hidden"
                animate="visible"
                className="grid grid-cols-1 sm:grid-cols-2 gap-3"
              >
                {advancedRatios.map(({ key, ratio }, index) => (
                  <MetricCard
                    key={key}
                    name={ratio.name}
                    value={ratio.display_value}
                    interpretation={ratio.interpretation}
                    healthStatus={ratio.threshold_status}
                    variance={analytics.has_previous_data ? getVarianceForRatio(key) : undefined}
                    index={index}
                    isCalculable={ratio.is_calculable}
                    compact
                  />
                ))}
              </motion.div>
            </CollapsibleSection>
          )}
        </>
      ) : (
        // Empty state when no ratios calculable
        <EmptyStateCard
          icon={<ChartIcon />}
          title="Limited Account Classification"
          message="Ratio calculations require classified accounts. Upload a trial balance with standard account names for ratio analysis."
        />
      )}

      {/* Category Totals Summary (compact) */}
      {hasCalculableRatios && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-4 pt-4 border-t border-theme-divider"
        >
          <div className="flex flex-wrap gap-4 justify-center text-xs font-sans text-content-tertiary">
            <span>
              Assets: <span className="text-content-secondary type-num-xs">${analytics.category_totals.total_assets.toLocaleString()}</span>
            </span>
            <span>
              Liabilities: <span className="text-content-secondary type-num-xs">${analytics.category_totals.total_liabilities.toLocaleString()}</span>
            </span>
            <span>
              Equity: <span className="text-content-secondary type-num-xs">${analytics.category_totals.total_equity.toLocaleString()}</span>
            </span>
            {analytics.category_totals.total_revenue > 0 && (
              <span>
                Revenue: <span className="text-content-secondary type-num-xs">${analytics.category_totals.total_revenue.toLocaleString()}</span>
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
