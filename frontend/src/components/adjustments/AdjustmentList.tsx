'use client'

/**
 * AdjustmentList - Sprint 52
 *
 * List view for adjusting journal entries with:
 * - Status badges and filtering
 * - Expandable entry details
 * - Status update actions
 * - Delete functionality
 *
 * Oat & Obsidian theme compliance.
 */

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { AdjustingEntry, AdjustmentStatus } from '@/types/adjustment'
import {
  ADJUSTMENT_STATUS_COLORS,
  ADJUSTMENT_TYPE_COLORS,
  formatAmount,
  getAdjustmentStatusLabel,
  getAdjustmentTypeLabel,
} from '@/types/adjustment'

interface AdjustmentListProps {
  /** List of adjusting entries */
  entries: AdjustingEntry[]
  /** Currently selected entry ID */
  selectedId?: string | null
  /** Callback when entry is selected */
  onSelect?: (entry: AdjustingEntry) => void
  /** Callback to update status */
  onUpdateStatus?: (id: string, status: AdjustmentStatus) => Promise<void>
  /** Callback to delete entry */
  onDelete?: (id: string) => Promise<void>
  /** Loading state */
  isLoading?: boolean
  /** Empty state message */
  emptyMessage?: string
}

/**
 * Individual entry card component.
 */
function EntryCard({
  entry,
  isSelected,
  isExpanded,
  onToggle,
  onSelect,
  onUpdateStatus,
  onDelete,
}: {
  entry: AdjustingEntry
  isSelected: boolean
  isExpanded: boolean
  onToggle: () => void
  onSelect?: () => void
  onUpdateStatus?: (status: AdjustmentStatus) => Promise<void>
  onDelete?: () => Promise<void>
}) {
  const [isUpdating, setIsUpdating] = useState(false)

  const statusColors = ADJUSTMENT_STATUS_COLORS[entry.status]
  const typeColors = ADJUSTMENT_TYPE_COLORS[entry.adjustment_type]

  const handleStatusChange = async (newStatus: AdjustmentStatus) => {
    if (!onUpdateStatus || isUpdating) return
    setIsUpdating(true)
    try {
      await onUpdateStatus(newStatus)
    } finally {
      setIsUpdating(false)
    }
  }

  const handleDelete = async () => {
    if (!onDelete || isUpdating) return
    if (!confirm('Are you sure you want to delete this entry?')) return
    setIsUpdating(true)
    try {
      await onDelete()
    } finally {
      setIsUpdating(false)
    }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`
        border rounded-lg overflow-hidden transition-colors
        ${isSelected
          ? 'border-sage-500/50 bg-obsidian-700/50'
          : 'border-obsidian-700 bg-obsidian-800/50 hover:border-obsidian-600'
        }
      `}
    >
      {/* Header Row */}
      <div
        className="flex items-center gap-3 p-3 cursor-pointer"
        onClick={onToggle}
      >
        {/* Expand Icon */}
        <motion.div
          animate={{ rotate: isExpanded ? 90 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-oatmeal-500"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </motion.div>

        {/* Reference & Description */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-medium text-oatmeal-200">
              {entry.reference}
            </span>
            <span className={`px-1.5 py-0.5 rounded text-xs ${typeColors.bg} ${typeColors.text}`}>
              {getAdjustmentTypeLabel(entry.adjustment_type)}
            </span>
          </div>
          <p className="text-sm text-oatmeal-400 truncate">{entry.description}</p>
        </div>

        {/* Amount */}
        <div className="text-right">
          <div className="font-mono text-sm font-medium text-oatmeal-200">
            {formatAmount(entry.entry_total)}
          </div>
          <div className="text-xs text-oatmeal-500">
            {entry.account_count} accounts
          </div>
        </div>

        {/* Status Badge */}
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium border ${statusColors.bg} ${statusColors.text} ${statusColors.border}`}
        >
          {getAdjustmentStatusLabel(entry.status)}
        </span>
      </div>

      {/* Expanded Details */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 border-t border-obsidian-700">
              {/* Entry Lines */}
              <div className="mt-3">
                <div className="text-xs text-oatmeal-500 uppercase tracking-wider mb-2">
                  Journal Entry Lines
                </div>
                <div className="bg-obsidian-900/50 rounded-lg overflow-hidden">
                  <div className="grid grid-cols-3 gap-2 px-3 py-2 bg-obsidian-800 text-xs text-oatmeal-500 uppercase tracking-wider">
                    <div>Account</div>
                    <div className="text-right">Debit</div>
                    <div className="text-right">Credit</div>
                  </div>
                  {entry.lines.map((line, idx) => (
                    <div
                      key={idx}
                      className="grid grid-cols-3 gap-2 px-3 py-2 border-t border-obsidian-700/50 text-sm"
                    >
                      <div className="text-oatmeal-300 truncate">{line.account_name}</div>
                      <div className="text-right font-mono text-oatmeal-200">
                        {line.debit > 0 ? formatAmount(line.debit) : '-'}
                      </div>
                      <div className="text-right font-mono text-oatmeal-200">
                        {line.credit > 0 ? formatAmount(line.credit) : '-'}
                      </div>
                    </div>
                  ))}
                  {/* Totals */}
                  <div className="grid grid-cols-3 gap-2 px-3 py-2 border-t border-obsidian-700 bg-obsidian-800 text-sm font-medium">
                    <div className="text-oatmeal-400">Totals</div>
                    <div className="text-right font-mono text-oatmeal-200">
                      {formatAmount(entry.total_debits)}
                    </div>
                    <div className="text-right font-mono text-oatmeal-200">
                      {formatAmount(entry.total_credits)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Metadata */}
              <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-oatmeal-500">Prepared by:</span>{' '}
                  <span className="text-oatmeal-300">{entry.prepared_by || 'N/A'}</span>
                </div>
                {entry.reviewed_by && (
                  <div>
                    <span className="text-oatmeal-500">Reviewed by:</span>{' '}
                    <span className="text-oatmeal-300">{entry.reviewed_by}</span>
                  </div>
                )}
                <div>
                  <span className="text-oatmeal-500">Created:</span>{' '}
                  <span className="text-oatmeal-300">
                    {new Date(entry.created_at).toLocaleDateString()}
                  </span>
                </div>
                {entry.is_reversing && (
                  <div>
                    <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-400 text-xs rounded">
                      Auto-Reversing
                    </span>
                  </div>
                )}
              </div>

              {/* Notes */}
              {entry.notes && (
                <div className="mt-3">
                  <div className="text-xs text-oatmeal-500 uppercase tracking-wider mb-1">
                    Notes
                  </div>
                  <p className="text-sm text-oatmeal-400">{entry.notes}</p>
                </div>
              )}

              {/* Actions */}
              <div className="mt-4 flex flex-wrap gap-2">
                {entry.status === 'proposed' && onUpdateStatus && (
                  <>
                    <button
                      onClick={() => handleStatusChange('approved')}
                      disabled={isUpdating}
                      className="px-3 py-1.5 bg-sage-500/20 border border-sage-500/30 rounded text-sage-400 text-sm hover:bg-sage-500/30 transition-colors disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => handleStatusChange('rejected')}
                      disabled={isUpdating}
                      className="px-3 py-1.5 bg-clay-500/20 border border-clay-500/30 rounded text-clay-400 text-sm hover:bg-clay-500/30 transition-colors disabled:opacity-50"
                    >
                      Reject
                    </button>
                  </>
                )}
                {entry.status === 'approved' && onUpdateStatus && (
                  <button
                    onClick={() => handleStatusChange('posted')}
                    disabled={isUpdating}
                    className="px-3 py-1.5 bg-sage-600/20 border border-sage-600/30 rounded text-sage-300 text-sm hover:bg-sage-600/30 transition-colors disabled:opacity-50"
                  >
                    Mark as Posted
                  </button>
                )}
                {entry.status === 'rejected' && onUpdateStatus && (
                  <button
                    onClick={() => handleStatusChange('proposed')}
                    disabled={isUpdating}
                    className="px-3 py-1.5 bg-oatmeal-400/20 border border-oatmeal-400/30 rounded text-oatmeal-300 text-sm hover:bg-oatmeal-400/30 transition-colors disabled:opacity-50"
                  >
                    Re-open
                  </button>
                )}
                {onSelect && (
                  <button
                    onClick={onSelect}
                    className="px-3 py-1.5 bg-obsidian-700 border border-obsidian-600 rounded text-oatmeal-300 text-sm hover:bg-obsidian-600 transition-colors"
                  >
                    View Details
                  </button>
                )}
                {onDelete && (
                  <button
                    onClick={handleDelete}
                    disabled={isUpdating}
                    className="px-3 py-1.5 bg-clay-500/10 border border-clay-500/20 rounded text-clay-500 text-sm hover:bg-clay-500/20 transition-colors disabled:opacity-50 ml-auto"
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export function AdjustmentList({
  entries,
  selectedId,
  onSelect,
  onUpdateStatus,
  onDelete,
  isLoading = false,
  emptyMessage = 'No adjusting entries yet.',
}: AdjustmentListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<AdjustmentStatus | 'all'>('all')

  const toggleExpanded = useCallback((id: string) => {
    setExpandedId((prev) => (prev === id ? null : id))
  }, [])

  // Filter entries
  const filteredEntries =
    statusFilter === 'all'
      ? entries
      : entries.filter((e) => e.status === statusFilter)

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-20 bg-obsidian-800/50 rounded-lg animate-pulse border border-obsidian-700"
          />
        ))}
      </div>
    )
  }

  // Empty state
  if (entries.length === 0) {
    return (
      <div className="text-center py-12 text-oatmeal-500">
        <svg
          className="w-12 h-12 mx-auto mb-3 opacity-50"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p>{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filter Bar */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-oatmeal-500 uppercase tracking-wider">Filter:</span>
        {(['all', 'proposed', 'approved', 'rejected', 'posted'] as const).map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-2 py-1 rounded text-xs transition-colors ${
              statusFilter === status
                ? 'bg-sage-500/20 text-sage-400 border border-sage-500/30'
                : 'bg-obsidian-700 text-oatmeal-400 border border-obsidian-600 hover:bg-obsidian-600'
            }`}
          >
            {status === 'all' ? 'All' : getAdjustmentStatusLabel(status)}
            {status !== 'all' && (
              <span className="ml-1 opacity-70">
                ({entries.filter((e) => e.status === status).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Entry List */}
      <div className="space-y-2">
        <AnimatePresence mode="popLayout">
          {filteredEntries.map((entry) => (
            <EntryCard
              key={entry.id}
              entry={entry}
              isSelected={selectedId === entry.id}
              isExpanded={expandedId === entry.id}
              onToggle={() => toggleExpanded(entry.id)}
              onSelect={onSelect ? () => onSelect(entry) : undefined}
              onUpdateStatus={
                onUpdateStatus
                  ? (status) => onUpdateStatus(entry.id, status)
                  : undefined
              }
              onDelete={onDelete ? () => onDelete(entry.id) : undefined}
            />
          ))}
        </AnimatePresence>
      </div>

      {/* No Results After Filter */}
      {filteredEntries.length === 0 && entries.length > 0 && (
        <div className="text-center py-8 text-oatmeal-500">
          No entries with status &quot;{statusFilter}&quot;
        </div>
      )}
    </div>
  )
}

export default AdjustmentList
