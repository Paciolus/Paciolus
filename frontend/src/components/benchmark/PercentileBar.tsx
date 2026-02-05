'use client'

/**
 * PercentileBar - Sprint 46 Benchmark Visual Component
 *
 * Visual percentile indicator with quartile markers showing
 * where a client's ratio falls within industry distribution.
 *
 * Features:
 * - Color-coded position indicator (sage/oatmeal/clay)
 * - Quartile markers (0, 25, 50, 75, 100)
 * - Animated indicator positioning
 * - Oat & Obsidian theme compliance
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Display component only, no data persistence
 */

import { motion } from 'framer-motion'

interface PercentileBarProps {
  /** Percentile value (0-100) */
  percentile: number
  /** Show quartile labels below the bar */
  showLabels?: boolean
  /** Health indicator for color coding */
  healthIndicator?: 'positive' | 'neutral' | 'negative'
  /** Whether lower percentile is better (inverted interpretation) */
  lowerIsBetter?: boolean
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
}

/**
 * Get indicator color based on health indicator
 */
function getIndicatorColor(
  healthIndicator: 'positive' | 'neutral' | 'negative',
): string {
  switch (healthIndicator) {
    case 'positive':
      return 'bg-sage-500'
    case 'negative':
      return 'bg-clay-500'
    case 'neutral':
    default:
      return 'bg-oatmeal-500'
  }
}

/**
 * Get size classes for the bar
 */
function getSizeClasses(size: 'sm' | 'md' | 'lg') {
  switch (size) {
    case 'sm':
      return {
        track: 'h-1.5',
        indicator: 'w-2.5 h-2.5 -mt-0.5',
        marker: 'h-1.5',
        labels: 'text-[10px]',
      }
    case 'lg':
      return {
        track: 'h-3',
        indicator: 'w-4 h-4 -mt-0.5',
        marker: 'h-3',
        labels: 'text-xs',
      }
    case 'md':
    default:
      return {
        track: 'h-2',
        indicator: 'w-3 h-3 -mt-0.5',
        marker: 'h-2',
        labels: 'text-[11px]',
      }
  }
}

/**
 * PercentileBar Component
 */
export function PercentileBar({
  percentile,
  showLabels = true,
  healthIndicator = 'neutral',
  lowerIsBetter = false,
  size = 'md',
}: PercentileBarProps) {
  // Clamp percentile to valid range
  const clampedPercentile = Math.max(0, Math.min(100, percentile))

  // Calculate effective health based on percentile and direction
  const effectiveHealth = lowerIsBetter
    ? clampedPercentile <= 25
      ? 'positive'
      : clampedPercentile >= 75
      ? 'negative'
      : 'neutral'
    : healthIndicator

  const indicatorColor = getIndicatorColor(effectiveHealth)
  const sizeClasses = getSizeClasses(size)

  return (
    <div className="relative w-full">
      {/* Track */}
      <div className={`relative ${sizeClasses.track} bg-obsidian-700 rounded-full overflow-visible`}>
        {/* Gradient zones for visual context */}
        <div className="absolute inset-0 flex rounded-full overflow-hidden">
          <div className="w-1/4 bg-clay-500/20" />
          <div className="w-1/4 bg-oatmeal-500/10" />
          <div className="w-1/4 bg-oatmeal-500/10" />
          <div className="w-1/4 bg-sage-500/20" />
        </div>

        {/* Quartile markers */}
        <div
          className={`absolute left-1/4 ${sizeClasses.marker} w-px bg-obsidian-500`}
          style={{ transform: 'translateX(-50%)' }}
        />
        <div
          className={`absolute left-1/2 ${sizeClasses.marker} w-px bg-obsidian-400`}
          style={{ transform: 'translateX(-50%)' }}
        />
        <div
          className={`absolute left-3/4 ${sizeClasses.marker} w-px bg-obsidian-500`}
          style={{ transform: 'translateX(-50%)' }}
        />

        {/* Position indicator */}
        <motion.div
          initial={{ left: '50%', scale: 0 }}
          animate={{
            left: `${clampedPercentile}%`,
            scale: 1,
          }}
          transition={{
            type: 'spring',
            stiffness: 300,
            damping: 25,
            delay: 0.1,
          }}
          className={`
            absolute top-1/2 transform -translate-x-1/2 -translate-y-1/2
            ${sizeClasses.indicator} rounded-full ${indicatorColor}
            shadow-lg ring-2 ring-obsidian-900/50
          `}
        />
      </div>

      {/* Labels */}
      {showLabels && (
        <div className={`flex justify-between mt-1.5 ${sizeClasses.labels} text-oatmeal-600 font-mono`}>
          <span>0</span>
          <span>25</span>
          <span>50</span>
          <span>75</span>
          <span>100</span>
        </div>
      )}
    </div>
  )
}

export default PercentileBar
