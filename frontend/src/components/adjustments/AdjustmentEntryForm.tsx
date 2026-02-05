'use client'

/**
 * AdjustmentEntryForm - Sprint 52
 *
 * Form for creating adjusting journal entries.
 * Validates that debits equal credits before submission.
 *
 * Features:
 * - Dynamic line item addition/removal
 * - Real-time balance validation
 * - Adjustment type selection
 * - Oat & Obsidian theme compliance
 */

import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type {
  AdjustmentLine,
  AdjustingEntryRequest,
  AdjustmentType,
} from '@/types/adjustment'
import {
  calculateLineTotals,
  formatAmount,
  getAdjustmentTypeLabel,
} from '@/types/adjustment'

interface AdjustmentEntryFormProps {
  /** Initial reference number */
  initialReference?: string
  /** Available accounts for autocomplete */
  accounts?: string[]
  /** Callback when form is submitted */
  onSubmit: (entry: AdjustingEntryRequest) => Promise<void>
  /** Callback when form is cancelled */
  onCancel: () => void
  /** Loading state */
  isLoading?: boolean
  /** Error message */
  error?: string | null
}

const EMPTY_LINE: AdjustmentLine = {
  account_name: '',
  debit: 0,
  credit: 0,
  description: '',
}

const ADJUSTMENT_TYPES: AdjustmentType[] = [
  'accrual',
  'deferral',
  'estimate',
  'error_correction',
  'reclassification',
  'other',
]

export function AdjustmentEntryForm({
  initialReference = 'AJE-001',
  accounts = [],
  onSubmit,
  onCancel,
  isLoading = false,
  error = null,
}: AdjustmentEntryFormProps) {
  const [reference, setReference] = useState(initialReference)
  const [description, setDescription] = useState('')
  const [adjustmentType, setAdjustmentType] = useState<AdjustmentType>('other')
  const [notes, setNotes] = useState('')
  const [isReversing, setIsReversing] = useState(false)
  const [lines, setLines] = useState<AdjustmentLine[]>([
    { ...EMPTY_LINE },
    { ...EMPTY_LINE },
  ])

  const totals = calculateLineTotals(lines)

  // Update reference when prop changes
  useEffect(() => {
    if (initialReference) {
      setReference(initialReference)
    }
  }, [initialReference])

  /**
   * Add a new empty line.
   */
  const addLine = useCallback(() => {
    setLines((prev) => [...prev, { ...EMPTY_LINE }])
  }, [])

  /**
   * Remove a line by index.
   */
  const removeLine = useCallback((index: number) => {
    setLines((prev) => {
      if (prev.length <= 2) return prev // Minimum 2 lines
      return prev.filter((_, i) => i !== index)
    })
  }, [])

  /**
   * Update a line field.
   */
  const updateLine = useCallback(
    (index: number, field: keyof AdjustmentLine, value: string | number) => {
      setLines((prev) => {
        const updated = [...prev]
        updated[index] = {
          ...updated[index],
          [field]: value,
        }

        // Clear the opposite amount when entering debit/credit
        if (field === 'debit' && typeof value === 'number' && value > 0) {
          updated[index].credit = 0
        } else if (field === 'credit' && typeof value === 'number' && value > 0) {
          updated[index].debit = 0
        }

        return updated
      })
    },
    []
  )

  /**
   * Handle form submission.
   */
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()

      // Validate
      if (!reference.trim()) {
        return
      }
      if (!description.trim()) {
        return
      }
      if (!totals.isBalanced) {
        return
      }

      // Filter out empty lines and ensure valid amounts
      const validLines = lines
        .filter((l) => l.account_name.trim() && (l.debit > 0 || l.credit > 0))
        .map((l) => ({
          account_name: l.account_name.trim(),
          debit: l.debit || 0,
          credit: l.credit || 0,
          description: l.description?.trim() || undefined,
        }))

      if (validLines.length < 2) {
        return
      }

      const entry: AdjustingEntryRequest = {
        reference: reference.trim(),
        description: description.trim(),
        adjustment_type: adjustmentType,
        lines: validLines,
        notes: notes.trim() || undefined,
        is_reversing: isReversing,
      }

      await onSubmit(entry)
    },
    [
      reference,
      description,
      adjustmentType,
      lines,
      notes,
      isReversing,
      totals.isBalanced,
      onSubmit,
    ]
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-obsidian-800 border border-obsidian-700 rounded-xl p-6"
    >
      <h3 className="font-serif text-lg font-semibold text-oatmeal-100 mb-4">
        New Adjusting Entry
      </h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Header Fields */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Reference */}
          <div>
            <label className="block text-xs text-oatmeal-500 uppercase tracking-wider mb-1">
              Reference *
            </label>
            <input
              type="text"
              value={reference}
              onChange={(e) => setReference(e.target.value)}
              placeholder="AJE-001"
              className="w-full px-3 py-2 bg-obsidian-700 border border-obsidian-600 rounded-lg text-oatmeal-200 placeholder-oatmeal-500 focus:outline-none focus:ring-2 focus:ring-sage-500/50 focus:border-sage-500"
              required
            />
          </div>

          {/* Adjustment Type */}
          <div>
            <label className="block text-xs text-oatmeal-500 uppercase tracking-wider mb-1">
              Type
            </label>
            <select
              value={adjustmentType}
              onChange={(e) => setAdjustmentType(e.target.value as AdjustmentType)}
              className="w-full px-3 py-2 bg-obsidian-700 border border-obsidian-600 rounded-lg text-oatmeal-200 focus:outline-none focus:ring-2 focus:ring-sage-500/50 focus:border-sage-500"
            >
              {ADJUSTMENT_TYPES.map((type) => (
                <option key={type} value={type}>
                  {getAdjustmentTypeLabel(type)}
                </option>
              ))}
            </select>
          </div>

          {/* Reversing Checkbox */}
          <div className="flex items-end">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isReversing}
                onChange={(e) => setIsReversing(e.target.checked)}
                className="w-4 h-4 rounded border-obsidian-600 bg-obsidian-700 text-sage-500 focus:ring-sage-500/50"
              />
              <span className="text-sm text-oatmeal-300">Auto-Reversing</span>
            </label>
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-xs text-oatmeal-500 uppercase tracking-wider mb-1">
            Description *
          </label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the purpose of this adjustment..."
            className="w-full px-3 py-2 bg-obsidian-700 border border-obsidian-600 rounded-lg text-oatmeal-200 placeholder-oatmeal-500 focus:outline-none focus:ring-2 focus:ring-sage-500/50 focus:border-sage-500"
            required
          />
        </div>

        {/* Journal Entry Lines */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs text-oatmeal-500 uppercase tracking-wider">
              Journal Entry Lines
            </label>
            <button
              type="button"
              onClick={addLine}
              className="text-xs text-sage-400 hover:text-sage-300 transition-colors"
            >
              + Add Line
            </button>
          </div>

          <div className="bg-obsidian-900/50 rounded-lg border border-obsidian-700 overflow-hidden">
            {/* Header Row */}
            <div className="grid grid-cols-12 gap-2 px-3 py-2 bg-obsidian-800 text-xs text-oatmeal-500 uppercase tracking-wider border-b border-obsidian-700">
              <div className="col-span-5">Account</div>
              <div className="col-span-2 text-right">Debit</div>
              <div className="col-span-2 text-right">Credit</div>
              <div className="col-span-2">Memo</div>
              <div className="col-span-1"></div>
            </div>

            {/* Line Items */}
            <AnimatePresence mode="popLayout">
              {lines.map((line, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="grid grid-cols-12 gap-2 px-3 py-2 border-b border-obsidian-700/50 last:border-b-0"
                >
                  {/* Account */}
                  <div className="col-span-5">
                    <input
                      type="text"
                      value={line.account_name}
                      onChange={(e) => updateLine(index, 'account_name', e.target.value)}
                      placeholder="Account name"
                      list={`accounts-${index}`}
                      className="w-full px-2 py-1 bg-obsidian-700 border border-obsidian-600 rounded text-sm text-oatmeal-200 placeholder-oatmeal-600 focus:outline-none focus:ring-1 focus:ring-sage-500/50"
                    />
                    {accounts.length > 0 && (
                      <datalist id={`accounts-${index}`}>
                        {accounts.map((acc) => (
                          <option key={acc} value={acc} />
                        ))}
                      </datalist>
                    )}
                  </div>

                  {/* Debit */}
                  <div className="col-span-2">
                    <input
                      type="number"
                      value={line.debit || ''}
                      onChange={(e) =>
                        updateLine(index, 'debit', parseFloat(e.target.value) || 0)
                      }
                      placeholder="0.00"
                      min="0"
                      step="0.01"
                      className="w-full px-2 py-1 bg-obsidian-700 border border-obsidian-600 rounded text-sm text-right font-mono text-oatmeal-200 placeholder-oatmeal-600 focus:outline-none focus:ring-1 focus:ring-sage-500/50"
                    />
                  </div>

                  {/* Credit */}
                  <div className="col-span-2">
                    <input
                      type="number"
                      value={line.credit || ''}
                      onChange={(e) =>
                        updateLine(index, 'credit', parseFloat(e.target.value) || 0)
                      }
                      placeholder="0.00"
                      min="0"
                      step="0.01"
                      className="w-full px-2 py-1 bg-obsidian-700 border border-obsidian-600 rounded text-sm text-right font-mono text-oatmeal-200 placeholder-oatmeal-600 focus:outline-none focus:ring-1 focus:ring-sage-500/50"
                    />
                  </div>

                  {/* Memo */}
                  <div className="col-span-2">
                    <input
                      type="text"
                      value={line.description || ''}
                      onChange={(e) => updateLine(index, 'description', e.target.value)}
                      placeholder="Memo"
                      className="w-full px-2 py-1 bg-obsidian-700 border border-obsidian-600 rounded text-sm text-oatmeal-200 placeholder-oatmeal-600 focus:outline-none focus:ring-1 focus:ring-sage-500/50"
                    />
                  </div>

                  {/* Remove Button */}
                  <div className="col-span-1 flex justify-center">
                    <button
                      type="button"
                      onClick={() => removeLine(index)}
                      disabled={lines.length <= 2}
                      className="p-1 text-oatmeal-500 hover:text-clay-400 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                      title="Remove line"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Totals Row */}
            <div className="grid grid-cols-12 gap-2 px-3 py-2 bg-obsidian-800 border-t border-obsidian-700">
              <div className="col-span-5 text-right font-medium text-oatmeal-300">
                Totals:
              </div>
              <div className="col-span-2 text-right font-mono font-medium text-oatmeal-200">
                {formatAmount(totals.debits)}
              </div>
              <div className="col-span-2 text-right font-mono font-medium text-oatmeal-200">
                {formatAmount(totals.credits)}
              </div>
              <div className="col-span-3 flex items-center">
                {totals.isBalanced ? (
                  <span className="text-xs text-sage-400 flex items-center gap-1">
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    Balanced
                  </span>
                ) : (
                  <span className="text-xs text-clay-400 flex items-center gap-1">
                    <svg
                      className="w-4 h-4"
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
                    Out of balance: {formatAmount(Math.abs(totals.difference))}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Notes */}
        <div>
          <label className="block text-xs text-oatmeal-500 uppercase tracking-wider mb-1">
            Notes (Optional)
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Additional notes or documentation..."
            rows={2}
            className="w-full px-3 py-2 bg-obsidian-700 border border-obsidian-600 rounded-lg text-oatmeal-200 placeholder-oatmeal-500 focus:outline-none focus:ring-2 focus:ring-sage-500/50 focus:border-sage-500 resize-none"
          />
        </div>

        {/* Error Message */}
        {error && (
          <div className="p-3 bg-clay-500/20 border border-clay-500/30 rounded-lg text-clay-400 text-sm">
            {error}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 pt-2">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="flex-1 px-4 py-2 bg-obsidian-700 border border-obsidian-600 rounded-lg text-oatmeal-300 hover:bg-obsidian-600 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading || !totals.isBalanced || !reference.trim() || !description.trim()}
            className="flex-1 px-4 py-2 bg-sage-500 border border-sage-400 rounded-lg text-white font-medium hover:bg-sage-600 transition-colors disabled:opacity-50"
          >
            {isLoading ? 'Saving...' : 'Create Entry'}
          </button>
        </div>
      </form>
    </motion.div>
  )
}

export default AdjustmentEntryForm
