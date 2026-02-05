'use client'

import { useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  LineChart,
  Line,
  ResponsiveContainer,
  YAxis,
  Tooltip,
  ReferenceLine,
} from 'recharts'

/**
 * Oat & Obsidian Chart Palette
 * See: tailwind.config.ts for full color definitions
 */
const CHART_COLORS = {
  positive: '#4A7C59',  // sage-500
  negative: '#BC4749',  // clay-500
  neutral: '#B5AD9F',   // oatmeal-500
  grid: '#424242',      // obsidian-600
  background: '#212121', // obsidian-800
  text: '#EBE9E4',      // oatmeal-200
  textMuted: '#9e9e9e', // obsidian-300
}

export type TrendDirection = 'positive' | 'negative' | 'neutral'

export interface TrendDataPoint {
  period: string       // Display label (e.g., "Q1", "Jan", "2025")
  value: number
  periodDate?: string  // ISO date for tooltip
}

interface TrendSparklineProps {
  data: TrendDataPoint[]
  direction: TrendDirection
  height?: number
  showTooltip?: boolean
  animate?: boolean
  valuePrefix?: string  // e.g., "$" for currency
  valueSuffix?: string  // e.g., "%" for percentages
  showReferenceLine?: boolean
  className?: string
}

/**
 * TrendSparkline - Sprint 34 Trend Visualization Component
 *
 * A minimal sparkline chart for displaying trend data with Oat & Obsidian styling.
 * Uses recharts for lightweight, performant rendering.
 *
 * Features:
 * - Animated line drawing on mount
 * - Direction-aware coloring (sage for positive, clay for negative)
 * - Optional tooltip on hover
 * - Reference line at average value
 * - Responsive sizing
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */
export function TrendSparkline({
  data,
  direction,
  height = 40,
  showTooltip = true,
  animate = true,
  valuePrefix = '',
  valueSuffix = '',
  showReferenceLine = false,
  className = '',
}: TrendSparklineProps) {
  // Determine line color based on direction
  const lineColor = useMemo(() => {
    switch (direction) {
      case 'positive':
        return CHART_COLORS.positive
      case 'negative':
        return CHART_COLORS.negative
      default:
        return CHART_COLORS.neutral
    }
  }, [direction])

  // Calculate average for reference line
  const averageValue = useMemo(() => {
    if (!data.length) return 0
    const sum = data.reduce((acc, point) => acc + point.value, 0)
    return sum / data.length
  }, [data])

  // Calculate domain with padding
  const yDomain = useMemo(() => {
    if (!data.length) return [0, 100]
    const values = data.map(d => d.value)
    const min = Math.min(...values)
    const max = Math.max(...values)
    const padding = (max - min) * 0.1 || 1
    return [min - padding, max + padding]
  }, [data])

  // Format value for display
  const formatValue = (value: number) => {
    const formatted = value >= 1000
      ? `${(value / 1000).toFixed(1)}K`
      : value.toFixed(value % 1 === 0 ? 0 : 1)
    return `${valuePrefix}${formatted}${valueSuffix}`
  }

  // Custom tooltip component
  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: TrendDataPoint }> }) => {
    if (!active || !payload?.length) return null

    const point = payload[0].payload
    return (
      <div className="bg-obsidian-900 border border-obsidian-600 rounded-lg px-2 py-1 shadow-lg">
        <p className="text-oatmeal-300 text-[10px] font-sans font-medium">
          {point.period}
        </p>
        <p className="text-oatmeal-100 text-xs font-mono font-bold">
          {formatValue(point.value)}
        </p>
      </div>
    )
  }

  if (!data.length) {
    return (
      <div
        className={`flex items-center justify-center text-oatmeal-600 text-xs font-sans ${className}`}
        style={{ height }}
      >
        No trend data
      </div>
    )
  }

  return (
    <motion.div
      initial={animate ? { opacity: 0 } : false}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className={className}
      style={{ height }}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 2, right: 2, bottom: 2, left: 2 }}
        >
          <YAxis domain={yDomain} hide />

          {/* Reference line at average */}
          {showReferenceLine && (
            <ReferenceLine
              y={averageValue}
              stroke={CHART_COLORS.grid}
              strokeDasharray="3 3"
              strokeWidth={1}
            />
          )}

          {/* Tooltip */}
          {showTooltip && (
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ stroke: CHART_COLORS.grid, strokeWidth: 1 }}
            />
          )}

          {/* Trend line */}
          <Line
            type="monotone"
            dataKey="value"
            stroke={lineColor}
            strokeWidth={2}
            dot={false}
            activeDot={{
              r: 3,
              fill: lineColor,
              stroke: CHART_COLORS.background,
              strokeWidth: 1,
            }}
            isAnimationActive={animate}
            animationDuration={800}
            animationEasing="ease-out"
          />
        </LineChart>
      </ResponsiveContainer>
    </motion.div>
  )
}

/**
 * TrendSparklineMini - Ultra-compact sparkline for inline use
 *
 * A minimal variant without tooltips, suitable for table cells or
 * tight spaces where only the trend shape matters.
 */
export function TrendSparklineMini({
  data,
  direction,
  width = 60,
  height = 20,
}: {
  data: TrendDataPoint[]
  direction: TrendDirection
  width?: number
  height?: number
}) {
  const lineColor = direction === 'positive'
    ? CHART_COLORS.positive
    : direction === 'negative'
      ? CHART_COLORS.negative
      : CHART_COLORS.neutral

  if (!data.length) return null

  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 1, right: 1, bottom: 1, left: 1 }}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={lineColor}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default TrendSparkline
