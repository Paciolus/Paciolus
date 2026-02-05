'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { TrendSummaryCard, TrendSummaryCardSkeleton } from './TrendSummaryCard'
import { SectionHeader, CollapsibleSection, EmptyStateCard, TrendIcon } from '@/components/shared'
import { CONTAINER_VARIANTS } from '@/utils'
import type { TrendMetric } from '@/hooks/useTrends'

interface TrendSectionProps {
  /** Ratio trends to display */
  ratioTrends: TrendMetric[]
  /** Category trends to display (optional, shown in collapsible) */
  categoryTrends?: TrendMetric[]
  /** Number of periods analyzed */
  periodsAnalyzed: number
  /** Date range of analysis */
  dateRange: { start: string | null; end: string | null }
  /** Loading state */
  isLoading: boolean
  /** Error message */
  error: string | null
  /** Whether data exists */
  hasData: boolean
  /** Disabled state */
  disabled?: boolean
}

/**
 * TrendSection - Sprint 34 Trend Visualization Dashboard Section
 *
 * Displays historical trend data with sparkline visualizations.
 * Integrates with KeyMetricsSection or can be used standalone.
 *
 * Features:
 * - Ratio trends in 2-column grid
 * - Collapsible category trends section
 * - Loading skeletons
 * - Error states
 * - Date range display
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */
export function TrendSection({
  ratioTrends,
  categoryTrends = [],
  periodsAnalyzed,
  dateRange,
  isLoading,
  error,
  hasData,
  disabled = false,
}: TrendSectionProps) {
  const [showCategoryTrends, setShowCategoryTrends] = useState(false)

  // Format date range for display
  const formatDateRange = () => {
    if (!dateRange.start || !dateRange.end) return null

    const startDate = new Date(dateRange.start)
    const endDate = new Date(dateRange.end)

    const formatDate = (date: Date) =>
      date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })

    return `${formatDate(startDate)} - ${formatDate(endDate)}`
  }

  // Loading state
  if (isLoading) {
    return (
      <div className={disabled ? 'opacity-50 pointer-events-none' : ''}>
        <SectionHeader
          title="Historical Trends"
          subtitle="Loading trend data..."
          icon={<TrendIcon />}
          accentColor="sage"
          animate={false}
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map(i => (
            <TrendSummaryCardSkeleton key={i} />
          ))}
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className={disabled ? 'opacity-50 pointer-events-none' : ''}>
        <SectionHeader
          title="Historical Trends"
          subtitle={error}
          icon={<TrendIcon />}
          accentColor="clay"
          animate={false}
        />
        <EmptyStateCard
          icon={<TrendIcon />}
          title="Insufficient Historical Data"
          message="Trend analysis requires at least 2 diagnostic summaries. Run diagnostics on multiple periods to see trends."
        />
      </div>
    )
  }

  // No data state
  if (!hasData) {
    return (
      <div className={disabled ? 'opacity-50 pointer-events-none' : ''}>
        <SectionHeader
          title="Historical Trends"
          subtitle="No trend data available"
          icon={<TrendIcon />}
          accentColor="obsidian"
          animate={false}
        />
        <EmptyStateCard
          icon={<TrendIcon />}
          title="No Trend Data"
          message="Select a client and run multiple diagnostics to see trend analysis."
        />
      </div>
    )
  }

  // Main content with data
  return (
    <div className={disabled ? 'opacity-50 pointer-events-none' : ''}>
      <SectionHeader
        title="Historical Trends"
        subtitle={`${periodsAnalyzed} periods analyzed${formatDateRange() ? ` • ${formatDateRange()}` : ''}`}
        icon={<TrendIcon />}
        accentColor="sage"
        badge={
          <div className="flex items-center gap-2 bg-sage-500/10 border border-sage-500/20 rounded-full px-3 py-1">
            <div className="w-2 h-2 bg-sage-400 rounded-full" />
            <span className="text-sage-300 text-xs font-sans font-medium">
              Trend Active
            </span>
          </div>
        }
      />

      {/* Ratio Trends Grid */}
      {ratioTrends.length > 0 && (
        <motion.div
          variants={CONTAINER_VARIANTS.standard}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 sm:grid-cols-2 gap-4"
        >
          {ratioTrends.map((trend, index) => (
            <TrendSummaryCard
              key={trend.metricName}
              name={trend.displayName}
              currentValue={trend.currentValue}
              trendData={trend.dataPoints}
              direction={trend.direction}
              totalChange={trend.totalChange}
              totalChangePercent={trend.totalChangePercent}
              periodsAnalyzed={trend.periodsAnalyzed}
              minValue={trend.minValue}
              maxValue={trend.maxValue}
              averageValue={trend.averageValue}
              valuePrefix={trend.valuePrefix}
              valueSuffix={trend.valueSuffix}
              index={index}
            />
          ))}
        </motion.div>
      )}

      {/* Category Trends Collapsible Section */}
      {categoryTrends.length > 0 && (
        <CollapsibleSection
          label="Category Trends"
          itemCount={categoryTrends.length}
          isExpanded={showCategoryTrends}
          onToggle={() => setShowCategoryTrends(!showCategoryTrends)}
        >
          <motion.div
            variants={CONTAINER_VARIANTS.standard}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 sm:grid-cols-2 gap-3"
          >
            {categoryTrends.map((trend, index) => (
              <TrendSummaryCard
                key={trend.metricName}
                name={trend.displayName}
                currentValue={trend.currentValue}
                trendData={trend.dataPoints}
                direction={trend.direction}
                totalChange={trend.totalChange}
                totalChangePercent={trend.totalChangePercent}
                periodsAnalyzed={trend.periodsAnalyzed}
                minValue={trend.minValue}
                maxValue={trend.maxValue}
                averageValue={trend.averageValue}
                valuePrefix={trend.valuePrefix}
                valueSuffix={trend.valueSuffix}
                index={index}
                compact
              />
            ))}
          </motion.div>
        </CollapsibleSection>
      )}
    </div>
  )
}

export default TrendSection
