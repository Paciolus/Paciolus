'use client'

import { motion } from 'framer-motion'
import { TrendSparkline, TrendSparklineMini, type TrendDataPoint, type TrendDirection } from './TrendSparkline'
import { createCardStaggerVariants } from '@/utils'

interface TrendSummaryCardProps {
  /** Metric name (e.g., "Current Ratio", "Gross Margin") */
  name: string
  /** Current/latest value display string */
  currentValue: string
  /** Historical trend data points */
  trendData: TrendDataPoint[]
  /** Overall trend direction */
  direction: TrendDirection
  /** Total change from first to last period */
  totalChange: number
  /** Total change as percentage */
  totalChangePercent: number
  /** Number of periods analyzed */
  periodsAnalyzed: number
  /** Min value across all periods */
  minValue: number
  /** Max value across all periods */
  maxValue: number
  /** Average value across all periods */
  averageValue: number
  /** Stagger index for animation */
  index?: number
  /** Compact mode for smaller cards */
  compact?: boolean
  /** Value prefix for formatting (e.g., "$") */
  valuePrefix?: string
  /** Value suffix for formatting (e.g., "%") */
  valueSuffix?: string
}

/**
 * TrendSummaryCard - Sprint 34 Trend Visualization Component
 *
 * Displays a metric with its historical trend sparkline and summary statistics.
 * Designed for the KeyMetricsSection dashboard integration.
 *
 * Features:
 * - Sparkline visualization of historical data
 * - Direction-aware styling (sage for positive, clay for negative)
 * - Summary statistics (min, max, average, periods)
 * - Staggered entrance animation
 * - Responsive compact mode
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */
export function TrendSummaryCard({
  name,
  currentValue,
  trendData,
  direction,
  totalChange,
  totalChangePercent,
  periodsAnalyzed,
  minValue,
  maxValue,
  averageValue,
  index = 0,
  compact = false,
  valuePrefix = '',
  valueSuffix = '',
}: TrendSummaryCardProps) {
  // Card entrance animation
  const cardVariants = createCardStaggerVariants(index, 50)

  // Direction-based styling
  const directionClasses = {
    positive: {
      border: 'border-sage-500/30',
      bg: 'bg-sage-500/10',
      text: 'text-sage-400',
      badge: 'bg-sage-500/20 text-sage-300',
      icon: '↑',
    },
    negative: {
      border: 'border-clay-500/30',
      bg: 'bg-clay-500/10',
      text: 'text-clay-400',
      badge: 'bg-clay-500/20 text-clay-300',
      icon: '↓',
    },
    neutral: {
      border: 'border-oatmeal-300/50',
      bg: 'bg-oatmeal-100/50',
      text: 'text-content-tertiary',
      badge: 'bg-oatmeal-200/50 text-content-secondary',
      icon: '→',
    },
  }

  const styles = directionClasses[direction]

  // Format numeric values
  const formatValue = (value: number) => {
    const formatted = Math.abs(value) >= 1000
      ? `${(value / 1000).toFixed(1)}K`
      : value.toFixed(value % 1 === 0 ? 0 : 1)
    return `${valuePrefix}${formatted}${valueSuffix}`
  }

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(1)}%`
  }

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      className={`
        relative rounded-xl border ${styles.border} ${styles.bg}
        ${compact ? 'p-3' : 'p-4'} transition-all hover:border-opacity-70
      `}
    >
      {/* Header: Name and Direction Badge */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <h4 className={`font-sans font-medium text-content-primary ${compact ? 'text-xs' : 'text-sm'}`}>
          {name}
        </h4>
        <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full ${styles.badge}`}>
          <span className="text-xs font-mono">{styles.icon}</span>
          <span className="text-[10px] font-sans font-medium">
            {formatPercent(totalChangePercent)}
          </span>
        </div>
      </div>

      {/* Current Value */}
      <div className="mb-3">
        <span className={`font-mono font-bold text-content-primary ${compact ? 'text-xl' : 'text-2xl'}`}>
          {currentValue}
        </span>
        <span className="text-xs text-content-tertiary font-sans ml-2">
          current
        </span>
      </div>

      {/* Sparkline */}
      <div className={`${compact ? 'mb-2' : 'mb-3'}`}>
        {compact ? (
          <TrendSparklineMini
            data={trendData}
            direction={direction}
            width={100}
            height={24}
          />
        ) : (
          <TrendSparkline
            data={trendData}
            direction={direction}
            height={48}
            valuePrefix={valuePrefix}
            valueSuffix={valueSuffix}
            showReferenceLine
            animate
          />
        )}
      </div>

      {/* Summary Statistics */}
      {!compact && (
        <div className="grid grid-cols-3 gap-2 pt-2 border-t border-theme-divider">
          <div className="text-center">
            <p className="text-[10px] text-content-disabled font-sans uppercase tracking-wide mb-0.5">
              Min
            </p>
            <p className="text-xs text-content-secondary font-mono">
              {formatValue(minValue)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-content-disabled font-sans uppercase tracking-wide mb-0.5">
              Avg
            </p>
            <p className="text-xs text-content-secondary font-mono">
              {formatValue(averageValue)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-content-disabled font-sans uppercase tracking-wide mb-0.5">
              Max
            </p>
            <p className="text-xs text-content-secondary font-mono">
              {formatValue(maxValue)}
            </p>
          </div>
        </div>
      )}

      {/* Periods indicator */}
      <div className={`flex items-center justify-end ${compact ? 'mt-1' : 'mt-2'}`}>
        <span className="text-[10px] text-content-disabled font-sans">
          {periodsAnalyzed} periods
        </span>
      </div>
    </motion.div>
  )
}

/**
 * TrendSummaryCardSkeleton - Loading placeholder
 */
export function TrendSummaryCardSkeleton({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`
      rounded-xl border border-oatmeal-300/30 bg-oatmeal-100/30
      ${compact ? 'p-3' : 'p-4'} animate-pulse
    `}>
      {/* Header skeleton */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="h-4 w-24 bg-oatmeal-200/50 rounded" />
        <div className="h-5 w-16 bg-oatmeal-200/50 rounded-full" />
      </div>

      {/* Value skeleton */}
      <div className="mb-3">
        <div className="h-8 w-20 bg-oatmeal-200/50 rounded" />
      </div>

      {/* Sparkline skeleton */}
      <div className={`${compact ? 'h-6' : 'h-12'} bg-obsidian-700/30 rounded mb-3`} />

      {/* Stats skeleton */}
      {!compact && (
        <div className="grid grid-cols-3 gap-2 pt-2 border-t border-theme-divider">
          {[1, 2, 3].map(i => (
            <div key={i} className="text-center">
              <div className="h-2 w-8 bg-oatmeal-200/50 rounded mx-auto mb-1" />
              <div className="h-3 w-10 bg-oatmeal-200/50 rounded mx-auto" />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default TrendSummaryCard
