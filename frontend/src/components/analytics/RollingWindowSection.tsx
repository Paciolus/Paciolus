'use client'

/**
 * RollingWindowSection - Sprint 37 Rolling Window Analysis
 *
 * Displays rolling window averages with period selector and momentum indicators.
 * Supports 3, 6, and 12 month rolling windows.
 *
 * Features:
 * - Period selector (3/6/12 months)
 * - Rolling averages with sparklines
 * - Momentum indicators (accelerating/decelerating/steady/reversing)
 * - Trend direction indicators
 * - Oat & Obsidian theme compliance
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Displays only aggregate rolling data
 * - No financial data persisted to localStorage
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import { CollapsibleSection, EmptyStateCard, RollingIcon } from '@/components/shared'
import type {
  RollingWindowResponse,
  RollingWindowMetric,
  MomentumType,
  TrendDirection,
} from '@/hooks/useRollingWindow'

interface RollingWindowSectionProps {
  data: RollingWindowResponse | null
  isLoading?: boolean
  disabled?: boolean
  onWindowChange?: (window: 3 | 6 | 12) => void
}

// Window options
const WINDOW_OPTIONS: Array<{ value: 3 | 6 | 12; label: string }> = [
  { value: 3, label: '3 Month' },
  { value: 6, label: '6 Month' },
  { value: 12, label: '12 Month' },
]

// Momentum icons and colors
const MOMENTUM_CONFIG: Record<MomentumType, { icon: string; label: string; colorClass: string }> = {
  accelerating: { icon: '🚀', label: 'Accelerating', colorClass: 'text-sage-600' },
  decelerating: { icon: '🔻', label: 'Decelerating', colorClass: 'text-oatmeal-600' },
  steady: { icon: '➡️', label: 'Steady', colorClass: 'text-oatmeal-600' },
  reversing: { icon: '🔄', label: 'Reversing', colorClass: 'text-clay-600' },
}

// Trend direction icons
const TREND_CONFIG: Record<TrendDirection, { icon: string; colorClass: string }> = {
  positive: { icon: '↑', colorClass: 'text-sage-500' },
  negative: { icon: '↓', colorClass: 'text-clay-500' },
  neutral: { icon: '→', colorClass: 'text-oatmeal-500' },
}

// Display names for metrics
const METRIC_DISPLAY_NAMES: Record<string, string> = {
  total_assets: 'Total Assets',
  total_liabilities: 'Total Liabilities',
  total_equity: 'Total Equity',
  total_revenue: 'Total Revenue',
  total_expenses: 'Total Expenses',
  current_ratio: 'Current Ratio',
  quick_ratio: 'Quick Ratio',
  debt_to_equity: 'Debt to Equity',
  gross_margin: 'Gross Margin',
  net_profit_margin: 'Net Profit Margin',
  operating_margin: 'Operating Margin',
  return_on_assets: 'Return on Assets',
  return_on_equity: 'Return on Equity',
}

// Check if metric is a percentage
const PERCENTAGE_METRICS = new Set([
  'gross_margin', 'net_profit_margin', 'operating_margin',
  'return_on_assets', 'return_on_equity',
])

// Check if metric is currency
const CURRENCY_METRICS = new Set([
  'total_assets', 'total_liabilities', 'total_equity',
  'total_revenue', 'total_expenses',
])

/**
 * Format value based on metric type
 */
function formatValue(value: number, metricKey: string): string {
  if (PERCENTAGE_METRICS.has(metricKey)) {
    return `${value.toFixed(1)}%`
  }
  if (CURRENCY_METRICS.has(metricKey)) {
    return `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
  }
  return value.toFixed(2)
}

/**
 * Single metric card with rolling average
 */
function RollingMetricCard({
  metricKey,
  metric,
  selectedWindow,
  index,
}: {
  metricKey: string
  metric: RollingWindowMetric
  selectedWindow: 3 | 6 | 12
  index: number
}) {
  const displayName = METRIC_DISPLAY_NAMES[metricKey] || metricKey.replace(/_/g, ' ')
  const momentumConfig = MOMENTUM_CONFIG[metric.momentum.momentum_type]
  const trendConfig = TREND_CONFIG[metric.trend_direction]

  // Get the rolling average for selected window
  const rollingAvg = metric.rolling_averages[String(selectedWindow)]

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="border border-oatmeal-200 rounded-lg p-4 bg-oatmeal-50 hover:shadow-md transition-shadow duration-base"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-serif text-sm font-medium text-content-primary">
          {displayName}
        </h4>
        <span className={`text-lg ${trendConfig.colorClass}`}>
          {trendConfig.icon}
        </span>
      </div>

      {/* Current Value */}
      <div className="mb-3">
        <div className="text-xs text-oatmeal-500 mb-1">Current</div>
        <div className="font-mono text-xl font-bold text-content-primary">
          {formatValue(metric.current_value, metricKey)}
        </div>
      </div>

      {/* Rolling Average */}
      {rollingAvg && (
        <div className="mb-3 p-2 bg-oatmeal-50 rounded">
          <div className="text-xs text-oatmeal-500 mb-1">
            {selectedWindow}M Rolling Avg
          </div>
          <div className="font-mono text-lg font-semibold text-content-primary">
            {formatValue(rollingAvg.value, metricKey)}
          </div>
          <div className="text-xs text-oatmeal-400">
            {rollingAvg.data_points} data points
          </div>
        </div>
      )}

      {/* Momentum Indicator */}
      <div className="flex items-center gap-2 pt-2 border-t border-oatmeal-100">
        <span className="text-sm">{momentumConfig.icon}</span>
        <span className={`text-xs font-medium ${momentumConfig.colorClass}`}>
          {momentumConfig.label}
        </span>
        {metric.momentum.confidence >= 0.7 && (
          <span className="text-xs text-oatmeal-400 ml-auto">
            High confidence
          </span>
        )}
      </div>
    </motion.div>
  )
}

/**
 * Loading skeleton
 */
function RollingWindowSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="flex items-center justify-between mb-4">
        <div className="h-6 w-48 bg-oatmeal-200 rounded" />
        <div className="flex gap-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-8 w-20 bg-oatmeal-200 rounded" />
          ))}
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="border border-oatmeal-200 rounded-lg p-4">
            <div className="h-4 w-24 bg-oatmeal-200 rounded mb-3" />
            <div className="h-8 w-32 bg-oatmeal-200 rounded mb-2" />
            <div className="h-12 w-full bg-oatmeal-100 rounded" />
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * RollingWindowSection - Main component
 */
export function RollingWindowSection({
  data,
  isLoading = false,
  disabled = false,
  onWindowChange,
}: RollingWindowSectionProps) {
  const [selectedWindow, setSelectedWindow] = useState<3 | 6 | 12>(6)
  const [showRatios, setShowRatios] = useState(true)

  // Handle window change
  const handleWindowChange = (window: 3 | 6 | 12) => {
    setSelectedWindow(window)
    onWindowChange?.(window)
  }

  // Loading state
  if (isLoading) {
    return (
      <section className="mt-8">
        <RollingWindowSkeleton />
      </section>
    )
  }

  // No data state
  if (!data) {
    return null
  }

  // Error state
  if (data.error || !data.analysis) {
    return (
      <section className="mt-8">
        <EmptyStateCard
          icon={<RollingIcon />}
          title="Rolling Window Analysis"
          message={data.message || 'Collect more diagnostic data over time to view rolling averages and momentum indicators.'}
        />
      </section>
    )
  }

  const { analysis } = data
  const categoryMetrics = Object.entries(analysis.category_rolling)
  const ratioMetrics = Object.entries(analysis.ratio_rolling)

  return (
    <section className={`mt-8 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      {/* Section Header with Window Selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl" role="img" aria-label="Rolling analysis">
            📈
          </span>
          <div>
            <h3 className="font-serif text-lg font-semibold text-content-primary">
              Rolling Window Analysis
            </h3>
            <p className="text-xs text-oatmeal-600">
              {analysis.periods_analyzed} periods analyzed
            </p>
          </div>
        </div>

        {/* Window Selector */}
        <div className="flex gap-2">
          {WINDOW_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => handleWindowChange(option.value)}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-all
                ${selectedWindow === option.value
                  ? 'bg-sage-600 text-white'
                  : 'bg-oatmeal-100 text-content-secondary hover:bg-oatmeal-200'
                }
              `}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Category Metrics */}
      {categoryMetrics.length > 0 && (
        <div className="mb-6">
          <h4 className="font-sans text-sm font-medium text-oatmeal-600 mb-3 uppercase tracking-wide">
            Category Totals
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {categoryMetrics.map(([key, metric], index) => (
              <RollingMetricCard
                key={key}
                metricKey={key}
                metric={metric}
                selectedWindow={selectedWindow}
                index={index}
              />
            ))}
          </div>
        </div>
      )}

      {/* Ratio Metrics (Collapsible) */}
      {ratioMetrics.length > 0 && (
        <CollapsibleSection
          label="Financial Ratios"
          itemCount={ratioMetrics.length}
          isExpanded={showRatios}
          onToggle={() => setShowRatios(!showRatios)}
          showBorder={false}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {ratioMetrics.map(([key, metric], index) => (
              <RollingMetricCard
                key={key}
                metricKey={key}
                metric={metric}
                selectedWindow={selectedWindow}
                index={index}
              />
            ))}
          </div>
        </CollapsibleSection>
      )}

      {/* Date Range Footer */}
      {analysis.date_range.start && analysis.date_range.end && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 text-xs text-oatmeal-500 text-right"
        >
          Data from {new Date(analysis.date_range.start).toLocaleDateString('en-US', {
            month: 'short',
            year: 'numeric',
          })} to {new Date(analysis.date_range.end).toLocaleDateString('en-US', {
            month: 'short',
            year: 'numeric',
          })}
        </motion.p>
      )}
    </section>
  )
}

export default RollingWindowSection
