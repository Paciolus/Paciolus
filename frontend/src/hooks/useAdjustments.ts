/**
 * useAdjustments Hook - Sprint 52
 *
 * React hook for managing adjusting journal entries.
 * Provides CRUD operations and adjusted trial balance generation.
 */

import { useState, useCallback } from 'react'
import type {
  AdjustingEntry,
  AdjustingEntryRequest,
  AdjustmentListResponse,
  AdjustedTrialBalance,
  ApplyAdjustmentsRequest,
  AdjustmentStatus,
  CreateEntryResponse,
} from '@/types/adjustment'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
   * Get auth headers for API requests.
   */
  const getHeaders = useCallback(() => {
    const token = localStorage.getItem('token')
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }
  }, [])

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

        const url = `${API_BASE}/audit/adjustments${params.toString() ? `?${params}` : ''}`
        const response = await fetch(url, {
          headers: getHeaders(),
        })

        if (!response.ok) {
          throw new Error('Failed to fetch adjustments')
        }

        const data: AdjustmentListResponse = await response.json()
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
    [getHeaders]
  )

  /**
   * Create a new adjusting entry.
   */
  const createEntry = useCallback(
    async (entry: AdjustingEntryRequest): Promise<CreateEntryResponse | null> => {
      setIsSaving(true)
      setError(null)

      try {
        const response = await fetch(`${API_BASE}/audit/adjustments`, {
          method: 'POST',
          headers: getHeaders(),
          body: JSON.stringify(entry),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.detail || 'Failed to create adjustment')
        }

        const result: CreateEntryResponse = await response.json()

        // Refresh entries list
        await fetchEntries()

        return result
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create adjustment')
        return null
      } finally {
        setIsSaving(false)
      }
    },
    [getHeaders, fetchEntries]
  )

  /**
   * Get a specific entry by ID.
   */
  const getEntry = useCallback(
    async (id: string): Promise<AdjustingEntry | null> => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await fetch(`${API_BASE}/audit/adjustments/${id}`, {
          headers: getHeaders(),
        })

        if (!response.ok) {
          throw new Error('Entry not found')
        }

        const entry: AdjustingEntry = await response.json()
        setSelectedEntry(entry)
        return entry
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to get entry')
        return null
      } finally {
        setIsLoading(false)
      }
    },
    [getHeaders]
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
        const response = await fetch(`${API_BASE}/audit/adjustments/${id}/status`, {
          method: 'PUT',
          headers: getHeaders(),
          body: JSON.stringify({ status, reviewed_by: reviewedBy }),
        })

        if (!response.ok) {
          throw new Error('Failed to update status')
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
    [getHeaders, fetchEntries]
  )

  /**
   * Delete an entry.
   */
  const deleteEntry = useCallback(
    async (id: string): Promise<boolean> => {
      setIsSaving(true)
      setError(null)

      try {
        const response = await fetch(`${API_BASE}/audit/adjustments/${id}`, {
          method: 'DELETE',
          headers: getHeaders(),
        })

        if (!response.ok) {
          throw new Error('Failed to delete entry')
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
    [getHeaders, fetchEntries, selectedEntry]
  )

  /**
   * Clear all entries.
   */
  const clearAll = useCallback(async (): Promise<boolean> => {
    setIsSaving(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/audit/adjustments`, {
        method: 'DELETE',
        headers: getHeaders(),
      })

      if (!response.ok) {
        throw new Error('Failed to clear adjustments')
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
  }, [getHeaders])

  /**
   * Get next sequential reference number.
   */
  const getNextReference = useCallback(
    async (prefix: string = 'AJE'): Promise<string | null> => {
      try {
        const response = await fetch(
          `${API_BASE}/audit/adjustments/reference/next?prefix=${encodeURIComponent(prefix)}`,
          { headers: getHeaders() }
        )

        if (!response.ok) {
          return null
        }

        const data = await response.json()
        return data.next_reference
      } catch {
        return null
      }
    },
    [getHeaders]
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
        const response = await fetch(`${API_BASE}/audit/adjustments/apply`, {
          method: 'POST',
          headers: getHeaders(),
          body: JSON.stringify(request),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.detail || 'Failed to apply adjustments')
        }

        const result: AdjustedTrialBalance = await response.json()
        setAdjustedTB(result)
        return result
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to apply adjustments')
        return null
      } finally {
        setIsLoading(false)
      }
    },
    [getHeaders]
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
