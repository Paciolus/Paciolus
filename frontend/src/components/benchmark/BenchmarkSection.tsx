'use client'

/**
 * BenchmarkSection - Sprint 46 Benchmark Dashboard Section
 *
 * Dashboard section displaying all benchmark comparisons for a client.
 * Includes overall score, health assessment, and individual ratio cards.
 *
 * Features:
 * - Overall score display with health indicator
 * - Grid of BenchmarkCard components
 * - Collapsible section
 * - Source attribution footer
 * - Disclaimer for compliance
 * - Oat & Obsidian theme compliance
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Display component only, no data persistence
 * - Comparison data is ephemeral (session only)
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { BenchmarkComparisonResponse } from '@/hooks/useBenchmarks'
import { CONTAINER_VARIANTS } from '@/utils'
import { BenchmarkCard } from './BenchmarkCard'

interface BenchmarkSectionProps {
  /** Comparison results from API */
  data: BenchmarkComparisonResponse | null
  /** Loading state */
  isLoading?: boolean
  /** Industry display name */
  industryDisplay?: string
  /** Disabled state */
  disabled?: boolean
}

/** Industry icons for visual context */
const INDUSTRY_ICONS: Record<string, string> = {
  retail: '🏪',
  manufacturing: '🏭',
  professional_services: '💼',
  technology: '💻',
  healthcare: '🏥',
  financial_services: '🏦',
}

/** Get overall health color classes */
function getHealthClasses(health: 'strong' | 'moderate' | 'concerning'): {
  bg: string
  text: string
  border: string
  glow: string
} {
  switch (health) {
    case 'strong':
      return {
        bg: 'bg-sage-500/20',
        text: 'text-sage-400',
        border: 'border-sage-500/30',
        glow: 'shadow-sage-500/20',
      }
    case 'moderate':
      return {
        bg: 'bg-oatmeal-500/20',
        text: 'text-oatmeal-400',
        border: 'border-oatmeal-500/30',
        glow: 'shadow-oatmeal-500/20',
      }
    case 'concerning':
      return {
        bg: 'bg-clay-500/20',
        text: 'text-clay-400',
        border: 'border-clay-500/30',
        glow: 'shadow-clay-500/20',
      }
    default:
      return {
        bg: 'bg-obsidian-700',
        text: 'text-oatmeal-400',
        border: 'border-obsidian-600',
        glow: '',
      }
  }
}

/** Format industry name for display */
function formatIndustryName(industry: string): string {
  return industry
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * Loading skeleton for benchmark section
 */
function BenchmarkSkeleton() {
  return (
    <div className="animate-pulse">
      {/* Header skeleton */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-oatmeal-200 rounded-lg" />
          <div>
            <div className="h-5 w-48 bg-oatmeal-200 rounded-sm mb-1" />
            <div className="h-3 w-32 bg-oatmeal-200/50 rounded-sm" />
          </div>
        </div>
        <div className="h-16 w-32 bg-oatmeal-200 rounded-xl" />
      </div>

      {/* Cards skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="border border-theme rounded-xl p-4">
            <div className="flex justify-between mb-3">
              <div className="h-4 w-24 bg-oatmeal-200 rounded-sm" />
              <div className="h-4 w-16 bg-oatmeal-200 rounded-sm" />
            </div>
            <div className="h-8 w-20 bg-oatmeal-200 rounded-sm mb-4" />
            <div className="h-2 w-full bg-oatmeal-200 rounded-full mb-4" />
            <div className="h-3 w-full bg-oatmeal-200/50 rounded-sm" />
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * Empty state when no benchmark data
 */
function EmptyState() {
  return (
    <div className="text-center py-12 px-6 bg-surface-card rounded-xl border border-theme">
      <div className="text-4xl mb-4">📊</div>
      <h4 className="font-serif text-lg text-content-primary mb-2">
        No Benchmark Comparison Available
      </h4>
      <p className="text-sm text-content-tertiary max-w-md mx-auto">
        Run a diagnostic assessment to compare your client&apos;s financial ratios
        against industry benchmarks.
      </p>
    </div>
  )
}

/**
 * BenchmarkSection Component
 */
export function BenchmarkSection({
  data,
  isLoading = false,
  industryDisplay,
  disabled = false,
}: BenchmarkSectionProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  // Loading state
  if (isLoading) {
    return (
      <section className="mt-8">
        <BenchmarkSkeleton />
      </section>
    )
  }

  // Empty state
  if (!data || data.comparisons.length === 0) {
    return (
      <section className="mt-8">
        <EmptyState />
      </section>
    )
  }

  const healthClasses = getHealthClasses(data.overall_health)
  const industryIcon = INDUSTRY_ICONS[data.industry] || '📊'
  const displayName = industryDisplay || formatIndustryName(data.industry)

  return (
    <section className={`mt-8 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      {/* Section Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6"
      >
        {/* Title & Industry */}
        <div className="flex items-center gap-3">
          <span className="text-2xl" role="img" aria-label={displayName}>
            {industryIcon}
          </span>
          <div>
            <h3 className="font-serif text-lg font-semibold text-content-primary">
              Industry Benchmark Comparison
            </h3>
            <p className="text-xs text-content-tertiary">
              {displayName} • FY {data.fiscal_year}
            </p>
          </div>
        </div>

        {/* Overall Score Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className={`
            flex items-center gap-4 px-5 py-3 rounded-xl border
            ${healthClasses.bg} ${healthClasses.border}
            shadow-lg ${healthClasses.glow}
          `}
        >
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wider text-content-tertiary mb-0.5">
              Overall Score
            </div>
            <div className={`font-mono text-2xl font-bold ${healthClasses.text}`}>
              {data.overall_score.toFixed(0)}
            </div>
          </div>
          <div className={`
            px-3 py-1.5 rounded-lg text-sm font-medium capitalize
            ${healthClasses.bg} ${healthClasses.text} border ${healthClasses.border}
          `}>
            {data.overall_health}
          </div>
        </motion.div>
      </motion.div>

      {/* Expand/Collapse Button */}
      <div className="flex justify-end mb-4">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-sm text-content-tertiary hover:text-content-primary transition-colors"
        >
          <motion.span
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            ▼
          </motion.span>
          {isExpanded ? 'Collapse' : 'Expand'} ({data.comparisons.length} ratios)
        </button>
      </div>

      {/* Comparison Cards Grid */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            variants={CONTAINER_VARIANTS.standard}
            initial="hidden"
            animate="visible"
            exit={{ opacity: 0, height: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {data.comparisons.map((comparison, index) => (
              <BenchmarkCard
                key={comparison.ratio_name}
                comparison={comparison}
                index={index}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer: Source Attribution & Disclaimer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-6 pt-4 border-t border-theme"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-oatmeal-600">
          <div>
            <span className="text-content-tertiary">Source:</span>{' '}
            {data.source_attribution}
          </div>
          <div>
            Generated: {new Date(data.generated_at).toLocaleString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
            })}
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mt-3 p-3 rounded-lg bg-surface-card-secondary border border-theme">
          <p className="text-[11px] text-content-tertiary leading-relaxed">
            <span className="font-medium text-content-secondary">Disclaimer:</span>{' '}
            {data.disclaimer}
          </p>
        </div>
      </motion.div>
    </section>
  )
}

export default BenchmarkSection
