'use client'

/**
 * ComparisonSection - Sprint 51 Prior Period Comparison Section
 *
 * Complete section for managing prior period comparison including:
 * - Period selector dropdown
 * - Save period button
 * - Comparison table
 *
 * Features:
 * - Collapsible section
 * - Loading states
 * - Error handling
 * - Oat & Obsidian theme compliance
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Only aggregate totals stored as prior periods
 * - Comparison results are ephemeral (session only)
 */

import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useFocusTrap } from '@/hooks'
import type { PriorPeriodSummary, PeriodComparison, CompareRequest, SavePeriodRequest } from '@/types/priorPeriod'
import { ComparisonTable } from './ComparisonTable'

interface ComparisonSectionProps {
  /** Current period data for comparison */
  currentData: {
    total_assets: number
    current_assets: number
    inventory: number
    total_liabilities: number
    current_liabilities: number
    total_equity: number
    total_revenue: number
    cost_of_goods_sold: number
    total_expenses: number
    operating_expenses: number
    current_ratio?: number | null
    quick_ratio?: number | null
    debt_to_equity?: number | null
    gross_margin?: number | null
    net_profit_margin?: number | null
    operating_margin?: number | null
    return_on_assets?: number | null
    return_on_equity?: number | null
    total_debits: number
    total_credits: number
    was_balanced: boolean
    anomaly_count: number
    materiality_threshold: number
    row_count: number
  }
  /** Client ID for period operations */
  clientId?: number
  /** Available prior periods */
  periods: PriorPeriodSummary[]
  /** Comparison result if available */
  comparison: PeriodComparison | null
  /** Loading state for periods */
  isLoadingPeriods: boolean
  /** Loading state for comparison */
  isLoadingComparison: boolean
  /** Saving state */
  isSaving: boolean
  /** Error message */
  error: string | null
  /** Fetch periods callback */
  onFetchPeriods: (clientId: number) => Promise<void>
  /** Save period callback */
  onSavePeriod: (clientId: number, data: SavePeriodRequest) => Promise<{ period_id: number } | null>
  /** Compare callback */
  onCompare: (data: CompareRequest) => Promise<PeriodComparison | null>
  /** Clear comparison callback */
  onClearComparison: () => void
  /** Disabled state */
  disabled?: boolean
}

/**
 * Save Period Modal
 */
function SavePeriodModal({
  isOpen,
  onClose,
  onSave,
  isSaving,
}: {
  isOpen: boolean
  onClose: () => void
  onSave: (label: string, periodDate?: string, periodType?: string) => void
  isSaving: boolean
}) {
  const [label, setLabel] = useState('')
  const [periodDate, setPeriodDate] = useState('')
  const [periodType, setPeriodType] = useState('')
  const focusTrapRef = useFocusTrap(isOpen, onClose)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (label.trim()) {
      onSave(label.trim(), periodDate || undefined, periodType || undefined)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-obsidian-900/60 backdrop-blur-xs"
        onClick={onClose}
        role="presentation"
      />

      {/* Modal */}
      <motion.div
        ref={focusTrapRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="save-period-title"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative theme-card p-6 w-full max-w-md mx-4"
      >
        <h3 id="save-period-title" className="font-serif text-lg font-semibold text-content-primary mb-4">
          Save as Prior Period
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="period-label" className="block text-sm text-content-secondary mb-1">
              Period Label *
            </label>
            <input
              id="period-label"
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="e.g., FY2025, Q3 2025"
              className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-content-primary placeholder-content-tertiary focus:outline-hidden focus:ring-2 focus:ring-sage-500/50 focus:border-sage-500"
              required
            />
          </div>

          <div>
            <label htmlFor="period-date" className="block text-sm text-content-secondary mb-1">
              Period End Date
            </label>
            <input
              id="period-date"
              type="date"
              value={periodDate}
              onChange={(e) => setPeriodDate(e.target.value)}
              className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-content-primary focus:outline-hidden focus:ring-2 focus:ring-sage-500/50 focus:border-sage-500"
            />
          </div>

          <div>
            <label htmlFor="period-type" className="block text-sm text-content-secondary mb-1">
              Period Type
            </label>
            <select
              id="period-type"
              value={periodType}
              onChange={(e) => setPeriodType(e.target.value)}
              className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-content-primary focus:outline-hidden focus:ring-2 focus:ring-sage-500/50 focus:border-sage-500"
            >
              <option value="">Select type...</option>
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="annual">Annual</option>
            </select>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-surface-card border border-oatmeal-300 text-content-primary hover:bg-surface-card-secondary rounded-xl transition-colors"
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-sage-600 text-white font-sans font-medium hover:bg-sage-700 rounded-xl transition-colors disabled:opacity-50"
              disabled={isSaving || !label.trim()}
            >
              {isSaving ? 'Saving...' : 'Save Period'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}

/**
 * ComparisonSection Component
 */
export function ComparisonSection({
  currentData,
  clientId,
  periods,
  comparison,
  isLoadingPeriods,
  isLoadingComparison,
  isSaving,
  error,
  onFetchPeriods,
  onSavePeriod,
  onCompare,
  onClearComparison,
  disabled = false,
}: ComparisonSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [selectedPeriodId, setSelectedPeriodId] = useState<number | null>(null)
  const [showSaveModal, setShowSaveModal] = useState(false)

  // Fetch periods when expanded and client is selected
  useEffect(() => {
    if (isExpanded && clientId && periods.length === 0 && !isLoadingPeriods) {
      onFetchPeriods(clientId)
    }
  }, [isExpanded, clientId, periods.length, isLoadingPeriods, onFetchPeriods])

  // Handle period selection
  const handlePeriodChange = useCallback(async (periodId: number) => {
    setSelectedPeriodId(periodId)

    if (periodId) {
      const compareRequest: CompareRequest = {
        prior_period_id: periodId,
        current_label: 'Current Period',
        ...currentData,
      }
      await onCompare(compareRequest)
    } else {
      onClearComparison()
    }
  }, [currentData, onCompare, onClearComparison])

  // Handle save period
  const handleSavePeriod = useCallback(async (
    label: string,
    periodDate?: string,
    periodType?: string
  ) => {
    if (!clientId) return

    const saveRequest: SavePeriodRequest = {
      period_label: label,
      period_date: periodDate,
      period_type: periodType as 'monthly' | 'quarterly' | 'annual' | undefined,
      ...currentData,
    }

    const result = await onSavePeriod(clientId, saveRequest)
    if (result) {
      setShowSaveModal(false)
    }
  }, [clientId, currentData, onSavePeriod])

  // Don't render if no client selected
  if (!clientId) {
    return null
  }

  return (
    <section className={`mt-6 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      {/* Section Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
 className="w-full flex items-center justify-between p-4 theme-card hover:bg-surface-card-secondary transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">📅</span>
          <div className="text-left">
            <h3 className="font-serif text-lg font-semibold text-content-primary">
              Prior Period Comparison
            </h3>
            <p className="text-xs text-content-tertiary">
              Compare against saved prior periods
            </p>
          </div>
        </div>
        <motion.span
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-content-tertiary"
        >
          ▼
        </motion.span>
      </button>

      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-4 border border-t-0 border-theme rounded-b-xl bg-surface-card">
              {/* Controls Row */}
              <div className="flex flex-col sm:flex-row gap-4 mb-4">
                {/* Period Selector */}
                <div className="flex-1">
                  <label htmlFor="compare-period" className="block text-xs text-content-tertiary uppercase tracking-wider mb-1">
                    Compare Against
                  </label>
                  <select
                    id="compare-period"
                    value={selectedPeriodId || ''}
                    onChange={(e) => handlePeriodChange(Number(e.target.value) || 0)}
                    disabled={isLoadingPeriods || isLoadingComparison}
                    className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-content-primary focus:outline-hidden focus:ring-2 focus:ring-sage-500/50 focus:border-sage-500 disabled:opacity-50"
                  >
                    <option value="">
                      {isLoadingPeriods ? 'Loading periods...' : 'Select a prior period...'}
                    </option>
                    {periods.map((period) => (
                      <option key={period.id} value={period.id}>
                        {period.period_label}
                        {period.period_date && ` (${period.period_date})`}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Save Button */}
                <div className="flex items-end">
                  <button
                    onClick={() => setShowSaveModal(true)}
                    disabled={isSaving}
                    className="px-4 py-2 bg-sage-600 text-white rounded-xl text-sm font-sans font-medium hover:bg-sage-700 transition-colors disabled:opacity-50"
                  >
                    Save as Prior Period
                  </button>
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="mb-4 p-3 bg-clay-50 border border-clay-500/30 rounded-lg text-clay-600 text-sm">
                  {error}
                </div>
              )}

              {/* No Periods Message */}
              {!isLoadingPeriods && periods.length === 0 && (
                <div className="text-center py-8 text-content-tertiary text-sm">
                  No prior periods saved for this client yet.
                  <br />
                  Save the current audit as a prior period to enable comparisons.
                </div>
              )}

              {/* Comparison Table */}
              {comparison && (
                <ComparisonTable
                  comparison={comparison}
                  isLoading={isLoadingComparison}
                  disabled={disabled}
                />
              )}

              {/* Loading State */}
              {isLoadingComparison && !comparison && (
                <div className="text-center py-8">
                  <div className="w-8 h-8 border-2 border-sage-500/30 border-t-sage-600 rounded-full animate-spin mx-auto mb-2" />
                  <p className="text-content-tertiary text-sm">Loading comparison...</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Save Period Modal */}
      <AnimatePresence>
        {showSaveModal && (
          <SavePeriodModal
            isOpen={showSaveModal}
            onClose={() => setShowSaveModal(false)}
            onSave={handleSavePeriod}
            isSaving={isSaving}
          />
        )}
      </AnimatePresence>
    </section>
  )
}

export default ComparisonSection
