'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { TrendSummaryCard, TrendSummaryCardSkeleton } from './TrendSummaryCard'
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

  // Container animation for staggered children
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
        delayChildren: 0.1,
      },
    },
  }

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
                  d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
                />
              </svg>
            </div>
            <div>
              <h3 className="font-serif font-semibold text-oatmeal-200 text-lg">
                Historical Trends
              </h3>
              <p className="text-oatmeal-500 text-xs font-sans">Loading trend data...</p>
            </div>
          </div>
        </div>

        {/* Skeleton Grid */}
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
        {/* Section Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-clay-500/10 flex items-center justify-center">
              <svg
                className="w-4 h-4 text-clay-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <div>
              <h3 className="font-serif font-semibold text-oatmeal-200 text-lg">
                Historical Trends
              </h3>
              <p className="text-clay-400 text-xs font-sans">{error}</p>
            </div>
          </div>
        </div>

        {/* Info message */}
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
            Insufficient Historical Data
          </h4>
          <p className="text-oatmeal-500 text-sm font-sans max-w-sm mx-auto">
            Trend analysis requires at least 2 diagnostic summaries.
            Run diagnostics on multiple periods to see trends.
          </p>
        </motion.div>
      </div>
    )
  }

  // No data state
  if (!hasData) {
    return (
      <div className={disabled ? 'opacity-50 pointer-events-none' : ''}>
        {/* Section Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-obsidian-700/50 flex items-center justify-center">
              <svg
                className="w-4 h-4 text-oatmeal-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
                />
              </svg>
            </div>
            <div>
              <h3 className="font-serif font-semibold text-oatmeal-200 text-lg">
                Historical Trends
              </h3>
              <p className="text-oatmeal-500 text-xs font-sans">No trend data available</p>
            </div>
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-obsidian-800/50 rounded-xl border border-obsidian-600/50 p-6 text-center"
        >
          <p className="text-oatmeal-500 text-sm font-sans">
            Select a client and run multiple diagnostics to see trend analysis.
          </p>
        </motion.div>
      </div>
    )
  }

  // Main content with data
  return (
    <div className={disabled ? 'opacity-50 pointer-events-none' : ''}>
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
                d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
              />
            </svg>
          </div>
          <div>
            <h3 className="font-serif font-semibold text-oatmeal-200 text-lg">
              Historical Trends
            </h3>
            <p className="text-oatmeal-500 text-xs font-sans">
              {periodsAnalyzed} periods analyzed
              {formatDateRange() && <span className="mx-1">•</span>}
              {formatDateRange()}
            </p>
          </div>
        </div>

        {/* Period badge */}
        <div className="flex items-center gap-2 bg-sage-500/10 border border-sage-500/20 rounded-full px-3 py-1">
          <div className="w-2 h-2 bg-sage-400 rounded-full" />
          <span className="text-sage-300 text-xs font-sans font-medium">
            Trend Active
          </span>
        </div>
      </div>

      {/* Ratio Trends Grid */}
      {ratioTrends.length > 0 && (
        <motion.div
          variants={containerVariants}
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
        <div className="mt-4">
          {/* Toggle Button */}
          <button
            onClick={() => setShowCategoryTrends(!showCategoryTrends)}
            className="w-full flex items-center justify-center gap-2 py-2 px-4
                       bg-obsidian-800/30 hover:bg-obsidian-800/50
                       border border-obsidian-700/50 hover:border-obsidian-600/50
                       rounded-lg transition-all group"
          >
            <span className="text-xs font-sans text-oatmeal-400 group-hover:text-oatmeal-300">
              {showCategoryTrends ? 'Hide' : 'Show'} Category Trends
            </span>
            <span className="text-oatmeal-500 text-xs">
              ({categoryTrends.length} available)
            </span>
            <motion.svg
              animate={{ rotate: showCategoryTrends ? 180 : 0 }}
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

          {/* Category Trends Grid */}
          <AnimatePresence>
            {showCategoryTrends && (
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
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}

export default TrendSection
