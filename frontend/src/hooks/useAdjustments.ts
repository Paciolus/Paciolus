/**
 * useAdjustments Hook - Sprint 52
 * Sprint 147: Migrated from direct fetch to apiClient for caching, retry, deduplication.
 *
 * React hook for managing adjusting journal entries.
 * Provides CRUD operations and adjusted trial balance generation.
 */

import { useState, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import type {
  AdjustingEntry,
  AdjustingEntryRequest,
  AdjustmentListResponse,
  AdjustedTrialBalance,
  ApplyAdjustmentsRequest,
  AdjustmentStatus,
  CreateEntryResponse,
} from '@/types/adjustment'
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils'

export interface UseAdjustmentsReturn {
  // State
  entries: AdjustingEntry[]
  selectedEntry: AdjustingEntry | null
  adjustedTB: AdjustedTrialBalance | null
  isLoading: boolean
  isSaving: boolean
  error: string | null

  // Statistics
  stats: {
    total: number
    proposed: number
    approved: number
    rejected: number
    posted: number
    totalAmount: number
  }

  // CRUD Operations
  fetchEntries: (status?: AdjustmentStatus | null, type?: string | null) => Promise<void>
  createEntry: (entry: AdjustingEntryRequest) => Promise<CreateEntryResponse | null>
  getEntry: (id: string) => Promise<AdjustingEntry | null>
  updateStatus: (
    id: string,
    status: AdjustmentStatus,
    reviewedBy?: string
  ) => Promise<boolean>
  deleteEntry: (id: string) => Promise<boolean>
  clearAll: () => Promise<boolean>

  // Utility
  getNextReference: (prefix?: string) => Promise<string | null>
  applyAdjustments: (request: ApplyAdjustmentsRequest) => Promise<AdjustedTrialBalance | null>

  // Selection
  selectEntry: (entry: AdjustingEntry | null) => void
  clearError: () => void
  clearAdjustedTB: () => void
}

export function useAdjustments(): UseAdjustmentsReturn {
  const { token } = useAuth()
  const [entries, setEntries] = useState<AdjustingEntry[]>([])
  const [selectedEntry, setSelectedEntry] = useState<AdjustingEntry | null>(null)
  const [adjustedTB, setAdjustedTB] = useState<AdjustedTrialBalance | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState({
    total: 0,
    proposed: 0,
    approved: 0,
    rejected: 0,
    posted: 0,
    totalAmount: 0,
  })

  /**
   * Fetch all adjusting entries.
   */
  const fetchEntries = useCallback(
    async (status?: AdjustmentStatus | null, type?: string | null) => {
      setIsLoading(true)
      setError(null)

      try {
        const params = new URLSearchParams()
        if (status) params.append('status', status)
        if (type) params.append('type', type)

        const endpoint = `/audit/adjustments${params.toString() ? `?${params}` : ''}`
        const { data, ok, error: apiError } = await apiGet<AdjustmentListResponse>(
          endpoint,
          token ?? null,
          { skipCache: true },
        )

        if (!ok || !data) {
          throw new Error(apiError || 'Failed to fetch adjustments')
        }

        setEntries(data.entries)
        setStats({
          total: data.total_adjustments,
          proposed: data.proposed_count,
          approved: data.approved_count,
          rejected: data.rejected_count,
          posted: data.posted_count,
          totalAmount: data.total_adjustment_amount,
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch adjustments')
      } finally {
        setIsLoading(false)
      }
    },
    [token]
  )

  /**
   * Create a new adjusting entry.
   */
  const createEntry = useCallback(
    async (entry: AdjustingEntryRequest): Promise<CreateEntryResponse | null> => {
      setIsSaving(true)
      setError(null)

      try {
        const { data, ok, error: apiError } = await apiPost<CreateEntryResponse>(
          '/audit/adjustments',
          token ?? null,
          entry,
        )

        if (!ok || !data) {
          throw new Error(apiError || 'Failed to create adjustment')
        }

        // Refresh entries list
        await fetchEntries()

        return data
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create adjustment')
        return null
      } finally {
        setIsSaving(false)
      }
    },
    [token, fetchEntries]
  )

  /**
   * Get a specific entry by ID.
   */
  const getEntry = useCallback(
    async (id: string): Promise<AdjustingEntry | null> => {
      setIsLoading(true)
      setError(null)

      try {
        const { data, ok, error: apiError } = await apiGet<AdjustingEntry>(
          `/audit/adjustments/${id}`,
          token ?? null,
        )

        if (!ok || !data) {
          throw new Error(apiError || 'Entry not found')
        }

        setSelectedEntry(data)
        return data
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to get entry')
        return null
      } finally {
        setIsLoading(false)
      }
    },
    [token]
  )

  /**
   * Update the status of an entry.
   */
  const updateStatus = useCallback(
    async (
      id: string,
      status: AdjustmentStatus,
      reviewedBy?: string
    ): Promise<boolean> => {
      setIsSaving(true)
      setError(null)

      try {
        const { ok, error: apiError } = await apiPut(
          `/audit/adjustments/${id}/status`,
          token ?? null,
          { status, reviewed_by: reviewedBy },
        )

        if (!ok) {
          throw new Error(apiError || 'Failed to update status')
        }

        // Refresh entries
        await fetchEntries()
        return true
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to update status')
        return false
      } finally {
        setIsSaving(false)
      }
    },
    [token, fetchEntries]
  )

  /**
   * Delete an entry.
   */
  const deleteEntry = useCallback(
    async (id: string): Promise<boolean> => {
      setIsSaving(true)
      setError(null)

      try {
        const { ok, error: apiError } = await apiDelete(
          `/audit/adjustments/${id}`,
          token ?? null,
        )

        if (!ok) {
          throw new Error(apiError || 'Failed to delete entry')
        }

        // Clear selection if deleted entry was selected
        if (selectedEntry?.id === id) {
          setSelectedEntry(null)
        }

        // Refresh entries
        await fetchEntries()
        return true
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete entry')
        return false
      } finally {
        setIsSaving(false)
      }
    },
    [token, fetchEntries, selectedEntry]
  )

  /**
   * Clear all entries.
   */
  const clearAll = useCallback(async (): Promise<boolean> => {
    setIsSaving(true)
    setError(null)

    try {
      const { ok, error: apiError } = await apiDelete(
        '/audit/adjustments',
        token ?? null,
      )

      if (!ok) {
        throw new Error(apiError || 'Failed to clear adjustments')
      }

      setEntries([])
      setSelectedEntry(null)
      setStats({
        total: 0,
        proposed: 0,
        approved: 0,
        rejected: 0,
        posted: 0,
        totalAmount: 0,
      })

      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear adjustments')
      return false
    } finally {
      setIsSaving(false)
    }
  }, [token])

  /**
   * Get next sequential reference number.
   */
  const getNextReference = useCallback(
    async (prefix: string = 'AJE'): Promise<string | null> => {
      try {
        const { data, ok } = await apiGet<{ next_reference: string }>(
          `/audit/adjustments/reference/next?prefix=${encodeURIComponent(prefix)}`,
          token ?? null,
          { skipCache: true },
        )

        if (!ok || !data) {
          return null
        }

        return data.next_reference
      } catch {
        return null
      }
    },
    [token]
  )

  /**
   * Apply adjustments to a trial balance.
   */
  const applyAdjustments = useCallback(
    async (
      request: ApplyAdjustmentsRequest
    ): Promise<AdjustedTrialBalance | null> => {
      setIsLoading(true)
      setError(null)

      try {
        const { data, ok, error: apiError } = await apiPost<AdjustedTrialBalance>(
          '/audit/adjustments/apply',
          token ?? null,
          request,
        )

        if (!ok || !data) {
          throw new Error(apiError || 'Failed to apply adjustments')
        }

        setAdjustedTB(data)
        return data
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to apply adjustments')
        return null
      } finally {
        setIsLoading(false)
      }
    },
    [token]
  )

  /**
   * Select an entry for detail view.
   */
  const selectEntry = useCallback((entry: AdjustingEntry | null) => {
    setSelectedEntry(entry)
  }, [])

  /**
   * Clear error state.
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  /**
   * Clear adjusted trial balance.
   */
  const clearAdjustedTB = useCallback(() => {
    setAdjustedTB(null)
  }, [])

  return {
    entries,
    selectedEntry,
    adjustedTB,
    isLoading,
    isSaving,
    error,
    stats,
    fetchEntries,
    createEntry,
    getEntry,
    updateStatus,
    deleteEntry,
    clearAll,
    getNextReference,
    applyAdjustments,
    selectEntry,
    clearError,
    clearAdjustedTB,
  }
}

export default useAdjustments
