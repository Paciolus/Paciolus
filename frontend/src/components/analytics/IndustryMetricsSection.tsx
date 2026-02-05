'use client'

/**
 * IndustryMetricsSection - Sprint 36 Industry-Specific Analytics
 *
 * Displays industry-specific ratios based on client classification.
 * Supports Manufacturing, Retail, Professional Services, and Generic fallback.
 *
 * Features:
 * - Industry-relevant ratio display
 * - Benchmark notes for context
 * - Placeholder messaging for unavailable metrics
 * - Oat & Obsidian theme compliance
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Displays only aggregate ratio data
 * - No financial data persisted to localStorage
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  getHealthClasses,
  getHealthLabel,
  createCardStaggerVariants,
  type HealthStatus,
} from '@/utils'

// Industry ratio result from API
export interface IndustryRatioResult {
  name: string
  value: number | null
  display_value: string
  is_calculable: boolean
  interpretation: string
  health_status: 'healthy' | 'warning' | 'concern' | 'neutral'
  industry: string
  benchmark_note?: string | null
}

export interface IndustryRatiosData {
  client_id: number
  client_name: string
  industry: string
  industry_display: string
  industry_type: string
  ratios: Record<string, IndustryRatioResult> | null
  summary_date: string | null
  available_industries: Array<{ value: string; label: string; ratio_count: number }>
  error?: string
  message?: string
}

interface IndustryMetricsSectionProps {
  data: IndustryRatiosData | null
  isLoading?: boolean
  disabled?: boolean
}

// Industry icons for visual context
const INDUSTRY_ICONS: Record<string, string> = {
  manufacturing: '🏭',
  retail: '🏪',
  professional_services: '💼',
  technology: '💻',
  healthcare: '🏥',
  financial_services: '🏦',
  real_estate: '🏢',
  construction: '🏗️',
  hospitality: '🏨',
  nonprofit: '🤝',
  education: '🎓',
  other: '📊',
}

// Industry descriptions
const INDUSTRY_DESCRIPTIONS: Record<string, string> = {
  manufacturing: 'Inventory and asset efficiency metrics',
  retail: 'Inventory turnover and margin optimization',
  professional_services: 'Productivity and utilization metrics',
  other: 'General performance indicators',
}

/**
 * Single industry metric card with benchmark tooltip
 */
function IndustryMetricCard({
  ratio,
  index,
}: {
  ratio: IndustryRatioResult
  index: number
}) {
  const [showTooltip, setShowTooltip] = useState(false)

  const cardVariants = createCardStaggerVariants(index, 50)
  const healthClasses = getHealthClasses(ratio.health_status as HealthStatus)
  const healthLabel = getHealthLabel(ratio.health_status as HealthStatus)

  // Determine if this is a placeholder (data required)
  const isPlaceholder = ratio.display_value === 'Data Required'

  // Get text color based on health status
  const getValueTextColor = () => {
    if (isPlaceholder) return 'text-oatmeal-500'
    switch (ratio.health_status) {
      case 'healthy':
        return 'text-sage-600'
      case 'warning':
        return 'text-amber-600'
      case 'concern':
        return 'text-clay-600'
      default:
        return 'text-obsidian-700'
    }
  }

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      custom={index}
      className={`
        relative rounded-lg border p-4 transition-all duration-base
        ${isPlaceholder
          ? 'border-oatmeal-300 bg-oatmeal-50'
          : 'border-oatmeal-200 bg-oatmeal-50 hover:shadow-md hover:border-oatmeal-400'
        }
      `}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {/* Benchmark Tooltip */}
      <AnimatePresence>
        {showTooltip && ratio.benchmark_note && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            className="absolute left-0 right-0 -top-2 transform -translate-y-full z-10"
          >
            <div className="bg-obsidian-800 text-oatmeal-100 text-xs rounded-md px-3 py-2 shadow-lg mx-2">
              <div className="font-medium text-oatmeal-200 mb-1">Industry Benchmark</div>
              <div>{ratio.benchmark_note}</div>
              {/* Arrow */}
              <div className="absolute left-1/2 transform -translate-x-1/2 bottom-0 translate-y-full">
                <div className="border-8 border-transparent border-t-obsidian-800" />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Metric Name */}
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-serif text-sm font-medium text-obsidian-700">
          {ratio.name}
        </h4>
        {ratio.benchmark_note && (
          <span className="text-oatmeal-500 text-xs cursor-help" title="Has benchmark info">
            ℹ️
          </span>
        )}
      </div>

      {/* Value */}
      <div className={`font-mono text-2xl font-bold mb-2 ${getValueTextColor()}`}>
        {ratio.display_value}
      </div>

      {/* Interpretation */}
      <p className={`text-xs leading-relaxed ${
        isPlaceholder ? 'text-oatmeal-600' : 'text-obsidian-600'
      }`}>
        {ratio.interpretation}
      </p>

      {/* Health Status Badge (only for calculable ratios) */}
      {ratio.is_calculable && (
        <div className="mt-3 flex items-center gap-2">
          <span className={`
            inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
            ${healthClasses.bg} ${healthClasses.badge}
          `}>
            {healthLabel}
          </span>
        </div>
      )}
    </motion.div>
  )
}

/**
 * Loading skeleton for industry metrics
 */
function IndustryMetricsSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-6 w-48 bg-oatmeal-200 rounded mb-4" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="border border-oatmeal-200 rounded-lg p-4">
            <div className="h-4 w-32 bg-oatmeal-200 rounded mb-3" />
            <div className="h-8 w-24 bg-oatmeal-200 rounded mb-2" />
            <div className="h-3 w-full bg-oatmeal-100 rounded" />
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * IndustryMetricsSection - Main component
 */
export function IndustryMetricsSection({
  data,
  isLoading = false,
  disabled = false,
}: IndustryMetricsSectionProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  // Loading state
  if (isLoading) {
    return (
      <section className="mt-8">
        <IndustryMetricsSkeleton />
      </section>
    )
  }

  // No data state
  if (!data) {
    return null
  }

  // Error state (no diagnostic data yet)
  if (data.error || !data.ratios) {
    return (
      <section className="mt-8">
        <div className="border border-oatmeal-200 rounded-lg p-6 bg-oatmeal-50">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-2xl">{INDUSTRY_ICONS[data.industry] || INDUSTRY_ICONS.other}</span>
            <h3 className="font-serif text-lg font-semibold text-obsidian-800">
              Industry Metrics
            </h3>
          </div>
          <p className="text-oatmeal-600 text-sm">
            {data.message || 'Run a diagnostic assessment to view industry-specific ratios.'}
          </p>
        </div>
      </section>
    )
  }

  const industryIcon = INDUSTRY_ICONS[data.industry_type] || INDUSTRY_ICONS.other
  const industryDesc = INDUSTRY_DESCRIPTIONS[data.industry_type] || INDUSTRY_DESCRIPTIONS.other
  const ratioEntries = Object.entries(data.ratios)

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

  return (
    <section className={`mt-8 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      {/* Section Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-4"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl" role="img" aria-label={data.industry_display}>
            {industryIcon}
          </span>
          <div>
            <h3 className="font-serif text-lg font-semibold text-obsidian-800">
              {data.industry_display} Metrics
            </h3>
            <p className="text-xs text-oatmeal-600">{industryDesc}</p>
          </div>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-sm text-obsidian-600 hover:text-obsidian-800 transition-colors"
        >
          <motion.span
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            ▼
          </motion.span>
          {isExpanded ? 'Collapse' : 'Expand'}
        </button>
      </motion.div>

      {/* Ratios Grid */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            exit={{ opacity: 0, height: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {ratioEntries.map(([key, ratio], index) => (
              <IndustryMetricCard
                key={key}
                ratio={ratio}
                index={index}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Summary Date */}
      {data.summary_date && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 text-xs text-oatmeal-500 text-right"
        >
          Based on diagnostic from {new Date(data.summary_date).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
          })}
        </motion.p>
      )}
    </section>
  )
}

export default IndustryMetricsSection
