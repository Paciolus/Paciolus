'use client'

import { useState, memo } from 'react'
import { motion } from 'framer-motion'
import { SectionHeader, CollapsibleSection, EmptyStateCard, ChartIcon } from '@/components/shared'
import { staggerContainerTight } from '@/lib/motion'
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

/**
 * Three-component DuPont decomposition (Sprint 798).
 *
 * The engine has existed since the original ratio work and the user guide has
 * told customers it "is available when all components are calculable" — but
 * nothing rendered it. Its only caller was a unit test. `null` from the
 * backend whenever revenue, assets or equity is zero, which is exactly the
 * documented condition.
 */
interface DupontData {
  net_profit_margin: number
  asset_turnover: number
  equity_multiplier: number
  decomposed_roe: number
  verification_matches: boolean
  prior_period_deltas?: {
    net_profit_margin_delta: number
    asset_turnover_delta: number
    equity_multiplier_delta: number
    decomposed_roe_delta: number
  }
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
  dupont?: DupontData | null
  /** Sprint 829: accounts with no category, left out of every ratio. */
  excluded_accounts?: { count: number; total_abs_balance: number } | null
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
/** Format a DuPont component. Margins read as percentages, the turnover and
 *  multiplier as multiples — the conventional presentation of each. */
const formatDupont = (key: string, value: number): string => {
  if (key === 'net_profit_margin' || key === 'decomposed_roe') {
    return `${(value * 100).toFixed(2)}%`
  }
  return `${value.toFixed(4)}x`
}

const DUPONT_COMPONENTS = [
  { key: 'net_profit_margin', label: 'Net Profit Margin', formula: 'Net Income / Revenue' },
  { key: 'asset_turnover', label: 'Asset Turnover', formula: 'Revenue / Total Assets' },
  { key: 'equity_multiplier', label: 'Equity Multiplier', formula: 'Total Assets / Total Equity' },
] as const

export const KeyMetricsSection = memo(function KeyMetricsSection({
  analytics,
  disabled = false,
}: KeyMetricsSectionProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [showDupont, setShowDupont] = useState(false)

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
            variants={staggerContainerTight}
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
                variants={staggerContainerTight}
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

          {/* DuPont Decomposition (Sprint 798) */}
          {analytics.dupont && (
            <CollapsibleSection
              label="DuPont Decomposition"
              itemCount={DUPONT_COMPONENTS.length}
              isExpanded={showDupont}
              onToggle={() => setShowDupont(!showDupont)}
            >
              <div className="space-y-3">
                <p className="font-sans text-xs text-obsidian-600 dark:text-oatmeal-400">
                  Return on Equity separated into its operating, efficiency and leverage
                  components: Net Profit Margin &times; Asset Turnover &times; Equity Multiplier.
                  Computed on ending balances.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {DUPONT_COMPONENTS.map(({ key, label, formula }) => (
                    <div
                      key={key}
                      className="rounded border border-obsidian-200 dark:border-obsidian-700 p-3"
                    >
                      <div className="font-sans text-xs uppercase tracking-wide text-obsidian-600 dark:text-oatmeal-400">
                        {label}
                      </div>
                      <div className="font-mono text-lg text-obsidian-900 dark:text-oatmeal-100 mt-1">
                        {formatDupont(key, analytics.dupont![key])}
                      </div>
                      <div className="font-sans text-xs text-obsidian-500 dark:text-oatmeal-500 mt-1">
                        {formula}
                      </div>
                      {analytics.dupont!.prior_period_deltas && (
                        <div className="font-mono text-xs text-obsidian-600 dark:text-oatmeal-400 mt-2">
                          vs prior:{' '}
                          {analytics.dupont!.prior_period_deltas[
                            `${key}_delta` as keyof NonNullable<DupontData['prior_period_deltas']>
                          ] >= 0
                            ? '+'
                            : ''}
                          {analytics.dupont!.prior_period_deltas[
                            `${key}_delta` as keyof NonNullable<DupontData['prior_period_deltas']>
                          ].toFixed(4)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex items-baseline justify-between rounded border border-sage-500/30 bg-sage-500/5 p-3">
                  <span className="font-sans text-xs uppercase tracking-wide text-obsidian-700 dark:text-oatmeal-300">
                    Decomposed Return on Equity
                  </span>
                  <span className="font-mono text-lg text-obsidian-900 dark:text-oatmeal-100">
                    {formatDupont('decomposed_roe', analytics.dupont.decomposed_roe)}
                  </span>
                </div>

                {/* The decomposition is only evidence if it reconciles. Say so
                    either way rather than showing three numbers that may not
                    multiply out — before Sprint 798 this flag was false on
                    99.85% of real trial balances and nothing displayed it. */}
                {!analytics.dupont.verification_matches && (
                  <p className="font-sans text-xs text-clay-600 dark:text-clay-400">
                    These components do not reconcile to Return on Equity computed directly.
                    Treat the decomposition as indicative and re-check the underlying totals.
                  </p>
                )}
              </div>
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
          <div className="flex flex-wrap gap-4 justify-center text-content-tertiary">
            <span className="inline-flex items-baseline gap-1">
              <span className="font-sans text-xs">Assets:</span>
              <span className="text-content-secondary type-num-xs">${analytics.category_totals.total_assets.toLocaleString()}</span>
            </span>
            <span className="inline-flex items-baseline gap-1">
              <span className="font-sans text-xs">Liabilities:</span>
              <span className="text-content-secondary type-num-xs">${analytics.category_totals.total_liabilities.toLocaleString()}</span>
            </span>
            <span className="inline-flex items-baseline gap-1">
              <span className="font-sans text-xs">Equity:</span>
              <span className="text-content-secondary type-num-xs">${analytics.category_totals.total_equity.toLocaleString()}</span>
            </span>
            {analytics.category_totals.total_revenue > 0 && (
              <span className="inline-flex items-baseline gap-1">
                <span className="font-sans text-xs">Revenue:</span>
                <span className="text-content-secondary type-num-xs">${analytics.category_totals.total_revenue.toLocaleString()}</span>
              </span>
            )}
          </div>
          {analytics.excluded_accounts && analytics.excluded_accounts.count > 0 && (
            <p className="mt-3 text-center font-sans text-xs text-clay-600 dark:text-clay-400">
              {analytics.excluded_accounts.count} unclassified account
              {analytics.excluded_accounts.count === 1 ? '' : 's'} (
              <span className="font-mono">${analytics.excluded_accounts.total_abs_balance.toLocaleString()}</span>
              {' '}absolute balance) {analytics.excluded_accounts.count === 1 ? 'is' : 'are'} excluded from these ratios.
            </p>
          )}
        </motion.div>
      )}
    </div>
  )
})

// Display name for React DevTools
KeyMetricsSection.displayName = 'KeyMetricsSection'

export default KeyMetricsSection
