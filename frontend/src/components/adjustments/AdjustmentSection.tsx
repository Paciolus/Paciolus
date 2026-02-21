'use client'

/**
 * AdjustmentSection - Sprint 52
 *
 * Main section for adjusting entries in the diagnostic results view.
 * Provides collapsible panel with entry form and list.
 *
 * Features:
 * - Collapsible section header
 * - Entry creation form
 * - Entry list with status management
 * - Statistics summary
 * - Apply adjustments to trial balance
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Adjustments are session-only
 * - Cleared when session ends
 */

import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AdjustmentEntryForm } from './AdjustmentEntryForm'
import { AdjustmentList } from './AdjustmentList'
import type { AdjustingEntryRequest, AdjustmentStatus } from '@/types/adjustment'
import { formatAmount } from '@/types/adjustment'
import { useAdjustments } from '@/hooks/useAdjustments'

interface AdjustmentSectionProps {
  /** Available account names for autocomplete */
  accountNames?: string[]
  /** Trial balance data for applying adjustments */
  trialBalance?: Array<{ account: string; debit: number; credit: number }>
  /** Callback when adjusted TB is generated */
  onAdjustedTBGenerated?: (adjustedTB: unknown) => void
  /** Whether the section is disabled */
  disabled?: boolean
}

export function AdjustmentSection({
  accountNames = [],
  trialBalance = [],
  onAdjustedTBGenerated,
  disabled = false,
}: AdjustmentSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [nextReference, setNextReference] = useState('AJE-001')

  const {
    entries,
    adjustedTB,
    isLoading,
    isSaving,
    error,
    stats,
    fetchEntries,
    createEntry,
    updateStatus,
    deleteEntry,
    clearAll,
    getNextReference,
    applyAdjustments,
    clearError,
    clearAdjustedTB,
  } = useAdjustments()

  // Fetch entries when section is expanded
  useEffect(() => {
    if (isExpanded) {
      fetchEntries()
    }
  }, [isExpanded, fetchEntries])

  // Get next reference when showing form
  useEffect(() => {
    if (showForm) {
      getNextReference().then((ref) => {
        if (ref) setNextReference(ref)
      })
    }
  }, [showForm, getNextReference])

  // Notify parent when adjusted TB is generated
  useEffect(() => {
    if (adjustedTB && onAdjustedTBGenerated) {
      onAdjustedTBGenerated(adjustedTB)
    }
  }, [adjustedTB, onAdjustedTBGenerated])

  /**
   * Handle form submission.
   */
  const handleSubmit = useCallback(
    async (entry: AdjustingEntryRequest) => {
      const result = await createEntry(entry)
      if (result) {
        setShowForm(false)
      }
    },
    [createEntry]
  )

  /**
   * Handle status update.
   */
  const handleUpdateStatus = useCallback(
    async (id: string, status: AdjustmentStatus) => {
      await updateStatus(id, status)
    },
    [updateStatus]
  )

  /**
   * Handle entry deletion.
   */
  const handleDelete = useCallback(
    async (id: string) => {
      await deleteEntry(id)
    },
    [deleteEntry]
  )

  /**
   * Handle clear all.
   */
  const handleClearAll = useCallback(async () => {
    if (!confirm('Are you sure you want to clear all adjusting entries?')) return
    await clearAll()
  }, [clearAll])

  /**
   * Handle apply adjustments.
   */
  const handleApplyAdjustments = useCallback(async () => {
    if (trialBalance.length === 0) {
      return
    }

    // Get IDs of approved/posted entries
    const approvedIds = entries
      .filter((e) => e.status === 'approved' || e.status === 'posted')
      .map((e) => e.id)

    if (approvedIds.length === 0) {
      return
    }

    await applyAdjustments({
      trial_balance: trialBalance,
      adjustment_ids: approvedIds,
      mode: 'official',
    })
  }, [entries, trialBalance, applyAdjustments])

  // Count approved entries
  const approvedCount = stats.approved + stats.posted

  return (
    <section className={`mt-6 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      {/* Section Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 bg-surface-card-secondary rounded-xl border border-theme hover:bg-surface-card transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">📝</span>
          <div className="text-left">
            <h3 className="font-serif text-lg font-semibold text-content-primary">
              Adjusting Entries
            </h3>
            <p className="text-xs text-content-tertiary">
              {stats.total > 0
                ? `${stats.total} entries (${approvedCount} approved)`
                : 'Propose journal adjustments'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {stats.total > 0 && (
            <span className="px-2 py-1 bg-sage-500/20 text-sage-400 text-sm font-mono rounded">
              {formatAmount(stats.totalAmount)}
            </span>
          )}
          <motion.span
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="text-content-tertiary"
          >
            ▼
          </motion.span>
        </div>
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
              {/* Action Buttons */}
              <div className="flex flex-wrap gap-2 mb-4">
                <button
                  onClick={() => setShowForm(!showForm)}
                  className="px-4 py-2 bg-sage-500/20 border border-sage-500/30 rounded-lg text-sage-400 text-sm font-medium hover:bg-sage-500/30 transition-colors"
                >
                  {showForm ? 'Cancel' : '+ New Entry'}
                </button>

                {approvedCount > 0 && trialBalance.length > 0 && (
                  <button
                    onClick={handleApplyAdjustments}
                    disabled={isLoading}
                    className="px-4 py-2 bg-sage-600/20 border border-sage-600/30 rounded-lg text-sage-300 text-sm font-medium hover:bg-sage-600/30 transition-colors disabled:opacity-50"
                  >
                    Apply {approvedCount} Adjustment{approvedCount !== 1 ? 's' : ''}
                  </button>
                )}

                {stats.total > 0 && (
                  <button
                    onClick={handleClearAll}
                    disabled={isSaving}
                    className="px-4 py-2 bg-clay-500/10 border border-clay-500/20 rounded-lg text-clay-500 text-sm hover:bg-clay-500/20 transition-colors disabled:opacity-50 ml-auto"
                  >
                    Clear All
                  </button>
                )}
              </div>

              {/* Error Message */}
              {error && (
                <div className="mb-4 p-3 bg-clay-500/20 border border-clay-500/30 rounded-lg text-clay-400 text-sm flex items-center justify-between">
                  <span>{error}</span>
                  <button
                    onClick={clearError}
                    className="text-clay-400 hover:text-clay-300"
                  >
                    ×
                  </button>
                </div>
              )}

              {/* Entry Form */}
              <AnimatePresence>
                {showForm && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mb-4"
                  >
                    <AdjustmentEntryForm
                      initialReference={nextReference}
                      accounts={accountNames}
                      onSubmit={handleSubmit}
                      onCancel={() => setShowForm(false)}
                      isLoading={isSaving}
                      error={error}
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Statistics Summary */}
              {stats.total > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
                  <div className="bg-surface-card-secondary rounded-lg p-3 text-center">
                    <div className="text-xl font-mono font-bold text-content-primary">
                      {stats.total}
                    </div>
                    <div className="text-xs text-content-tertiary">Total</div>
                  </div>
                  <div className="bg-oatmeal-200/10 rounded-lg p-3 text-center">
                    <div className="text-xl font-mono font-bold text-oatmeal-300">
                      {stats.proposed}
                    </div>
                    <div className="text-xs text-content-tertiary">Proposed</div>
                  </div>
                  <div className="bg-sage-500/10 rounded-lg p-3 text-center">
                    <div className="text-xl font-mono font-bold text-sage-400">
                      {stats.approved}
                    </div>
                    <div className="text-xs text-content-tertiary">Approved</div>
                  </div>
                  <div className="bg-clay-500/10 rounded-lg p-3 text-center">
                    <div className="text-xl font-mono font-bold text-clay-400">
                      {stats.rejected}
                    </div>
                    <div className="text-xs text-content-tertiary">Rejected</div>
                  </div>
                  <div className="bg-sage-600/10 rounded-lg p-3 text-center">
                    <div className="text-xl font-mono font-bold text-sage-300">
                      {stats.posted}
                    </div>
                    <div className="text-xs text-content-tertiary">Posted</div>
                  </div>
                </div>
              )}

              {/* Adjusted Trial Balance Preview */}
              {adjustedTB && (
                <div className="mb-4 p-4 bg-sage-500/10 border border-sage-500/30 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-serif font-semibold text-sage-400">
                      Adjusted Trial Balance
                    </h4>
                    <button
                      onClick={clearAdjustedTB}
                      className="text-sage-500 hover:text-sage-400 text-sm"
                    >
                      Clear
                    </button>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-content-tertiary">Adjustments Applied:</span>{' '}
                      <span className="font-mono text-content-primary">
                        {adjustedTB.adjustment_count}
                      </span>
                    </div>
                    <div>
                      <span className="text-content-tertiary">Accounts Affected:</span>{' '}
                      <span className="font-mono text-content-primary">
                        {adjustedTB.accounts_with_adjustments_count}
                      </span>
                    </div>
                    <div>
                      <span className="text-content-tertiary">Balanced:</span>{' '}
                      <span
                        className={`font-mono ${
                          adjustedTB.is_balanced ? 'text-sage-400' : 'text-clay-400'
                        }`}
                      >
                        {adjustedTB.is_balanced ? 'Yes' : 'No'}
                      </span>
                    </div>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-content-tertiary">Total Adjusted Debits:</span>{' '}
                      <span className="font-mono text-content-primary">
                        {formatAmount(adjustedTB.totals.adjusted_debits)}
                      </span>
                    </div>
                    <div>
                      <span className="text-content-tertiary">Total Adjusted Credits:</span>{' '}
                      <span className="font-mono text-content-primary">
                        {formatAmount(adjustedTB.totals.adjusted_credits)}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Entry List */}
              <AdjustmentList
                entries={entries}
                onUpdateStatus={handleUpdateStatus}
                onDelete={handleDelete}
                isLoading={isLoading}
                emptyMessage="No adjusting entries yet. Click 'New Entry' to create one."
              />

              {/* Zero-Storage Notice */}
              <div className="mt-4 text-xs text-content-disabled text-center">
                Adjusting entries are stored in your session only and will be cleared when you
                log out.
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  )
}

export default AdjustmentSection
