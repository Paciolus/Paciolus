'use client'

/**
 * LeadSheetSection - Sprint 50 Lead Sheet Dashboard Section
 *
 * Dashboard section displaying lead sheet groupings for audit workpapers.
 * Organizes accounts by standard lead sheet categories (A-Z).
 *
 * Features:
 * - Grid of LeadSheetCard components
 * - Collapsible section
 * - Summary statistics
 * - Filter by category type
 * - Oat & Obsidian theme compliance
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Display component only, no data persistence
 * - Lead sheet data computed at audit time
 */

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { LeadSheetGrouping } from '@/types/leadSheet'
import { CONTAINER_VARIANTS } from '@/utils'
import { LeadSheetCard } from './LeadSheetCard'

interface LeadSheetSectionProps {
  /** Grouping data from audit result */
  data: LeadSheetGrouping | null
  /** Loading state */
  isLoading?: boolean
  /** Disabled state */
  disabled?: boolean
}

/** Category filter options */
const CATEGORY_FILTERS = [
  { value: 'all', label: 'All Categories' },
  { value: 'asset', label: 'Assets' },
  { value: 'liability', label: 'Liabilities' },
  { value: 'equity', label: 'Equity' },
  { value: 'revenue', label: 'Revenue' },
  { value: 'expense', label: 'Expenses' },
] as const

type CategoryFilter = typeof CATEGORY_FILTERS[number]['value']

/**
 * Loading skeleton for lead sheet section
 */
function LeadSheetSkeleton() {
  return (
    <div className="animate-pulse">
      {/* Header skeleton */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-oatmeal-200 rounded-lg" />
          <div>
            <div className="h-5 w-48 bg-oatmeal-200 rounded mb-1" />
            <div className="h-3 w-32 bg-oatmeal-200/50 rounded" />
          </div>
        </div>
        <div className="h-10 w-40 bg-oatmeal-200 rounded-lg" />
      </div>

      {/* Cards skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="border border-theme rounded-xl p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-oatmeal-200 rounded-lg" />
              <div>
                <div className="h-4 w-24 bg-oatmeal-200 rounded mb-1" />
                <div className="h-3 w-16 bg-oatmeal-200/50 rounded" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {[1, 2, 3].map((j) => (
                <div key={j} className="h-12 bg-oatmeal-200/50 rounded-lg" />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * Empty state when no lead sheet data
 */
function EmptyState() {
  return (
    <div className="text-center py-12 px-6 bg-surface-card rounded-xl border border-theme">
      <div className="text-4xl mb-4">📋</div>
      <h4 className="font-serif text-lg text-content-primary mb-2">
        No Lead Sheet Grouping Available
      </h4>
      <p className="text-sm text-content-tertiary max-w-md mx-auto">
        Run a diagnostic assessment to view accounts organized by standard
        lead sheet categories (A-Z).
      </p>
    </div>
  )
}

/**
 * LeadSheetSection Component
 */
export function LeadSheetSection({
  data,
  isLoading = false,
  disabled = false,
}: LeadSheetSectionProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>('all')

  // Filter summaries by category
  const filteredSummaries = useMemo(() => {
    if (!data?.summaries) return []
    if (categoryFilter === 'all') return data.summaries
    return data.summaries.filter(
      s => s.category.toLowerCase() === categoryFilter
    )
  }, [data?.summaries, categoryFilter])

  // Loading state
  if (isLoading) {
    return (
      <section className="mt-8">
        <LeadSheetSkeleton />
      </section>
    )
  }

  // Empty state
  if (!data || data.summaries.length === 0) {
    return (
      <section className="mt-8">
        <EmptyState />
      </section>
    )
  }

  return (
    <section className={`mt-8 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      {/* Section Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6"
      >
        {/* Title */}
        <div className="flex items-center gap-3">
          <span className="text-2xl" role="img" aria-label="Lead Sheet">
            📋
          </span>
          <div>
            <h3 className="font-serif text-lg font-semibold text-content-primary">
              Lead Sheet Grouping
            </h3>
            <p className="text-xs text-content-tertiary">
              {data.total_accounts} accounts • {data.summaries.length} lead sheets
              {data.unmapped_count > 0 && (
                <span className="text-clay-400">
                  {' '}• {data.unmapped_count} unclassified
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Category Filter */}
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value as CategoryFilter)}
          className="
            px-4 py-2 rounded-lg
            bg-surface-input border border-theme
            text-content-primary text-sm
            focus:outline-none focus:ring-2 focus:ring-sage-500/50
            cursor-pointer
          "
        >
          {CATEGORY_FILTERS.map((filter) => (
            <option key={filter.value} value={filter.value}>
              {filter.label}
            </option>
          ))}
        </select>
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
          {isExpanded ? 'Collapse' : 'Expand'} ({filteredSummaries.length} shown)
        </button>
      </div>

      {/* Lead Sheet Cards Grid */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            variants={CONTAINER_VARIANTS.standard}
            initial="hidden"
            animate="visible"
            exit={{ opacity: 0, height: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {filteredSummaries.map((summary, index) => (
              <LeadSheetCard
                key={summary.lead_sheet}
                summary={summary}
                index={index}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty filter state */}
      {isExpanded && filteredSummaries.length === 0 && (
        <div className="text-center py-8 text-content-tertiary text-sm">
          No lead sheets match the selected filter.
        </div>
      )}

      {/* Footer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-6 pt-4 border-t border-theme"
      >
        <div className="p-3 rounded-lg bg-surface-card-secondary border border-theme">
          <p className="text-[11px] text-content-tertiary leading-relaxed">
            <span className="font-medium text-content-secondary">About Lead Sheets:</span>{' '}
            Lead sheets (A-Z) are standard audit workpaper categories used to organize
            accounts for review. This grouping follows industry-standard conventions
            for trial balance presentation.
          </p>
        </div>
      </motion.div>
    </section>
  )
}

export default LeadSheetSection
