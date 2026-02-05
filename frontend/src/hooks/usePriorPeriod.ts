/**
 * usePriorPeriod Hook - Sprint 51
 *
 * Hook for prior period comparison functionality.
 * Manages period saving, listing, and comparison API calls.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Uses token-based auth for API calls
 * - Comparison results are ephemeral (session only)
 */

import { useState, useCallback } from 'react'
import type {
  PriorPeriodSummary,
  PeriodComparison,
  SavePeriodRequest,
  CompareRequest,
} from '@/types/priorPeriod'

const API_URL = process.env.NEXT_PUBLIC_API_URL

export interface UsePriorPeriodReturn {
  // State
  periods: PriorPeriodSummary[]
  comparison: PeriodComparison | null
  isLoadingPeriods: boolean
  isLoadingComparison: boolean
  isSaving: boolean
  error: string | null

  // Actions
  fetchPeriods: (clientId: number) => Promise<void>
  savePeriod: (clientId: number, data: SavePeriodRequest) => Promise<{ period_id: number } | null>
  comparePeriods: (data: CompareRequest) => Promise<PeriodComparison | null>
  clearComparison: () => void
  clearError: () => void
}

/**
 * Hook for managing prior period comparison
 */
export function usePriorPeriod(token?: string): UsePriorPeriodReturn {
  const [periods, setPeriods] = useState<PriorPeriodSummary[]>([])
  const [comparison, setComparison] = useState<PeriodComparison | null>(null)
  const [isLoadingPeriods, setIsLoadingPeriods] = useState(false)
  const [isLoadingComparison, setIsLoadingComparison] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Fetch list of prior periods for a client
   */
  const fetchPeriods = useCallback(async (clientId: number) => {
    if (!token) {
      setError('Authentication required')
      return
    }

    setIsLoadingPeriods(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/clients/${clientId}/periods`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to fetch periods')
      }

      const data = await response.json()
      setPeriods(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch periods')
      setPeriods([])
    } finally {
      setIsLoadingPeriods(false)
    }
  }, [token])

  /**
   * Save current audit as a prior period
   */
  const savePeriod = useCallback(async (
    clientId: number,
    data: SavePeriodRequest
  ): Promise<{ period_id: number } | null> => {
    if (!token) {
      setError('Authentication required')
      return null
    }

    setIsSaving(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/clients/${clientId}/periods`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to save period')
      }

      const result = await response.json()

      // Refresh periods list
      await fetchPeriods(clientId)

      return { period_id: result.period_id }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save period')
      return null
    } finally {
      setIsSaving(false)
    }
  }, [token, fetchPeriods])

  /**
   * Compare current audit to a prior period
   */
  const comparePeriods = useCallback(async (
    data: CompareRequest
  ): Promise<PeriodComparison | null> => {
    if (!token) {
      setError('Authentication required')
      return null
    }

    setIsLoadingComparison(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/audit/compare`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to compare periods')
      }

      const result: PeriodComparison = await response.json()
      setComparison(result)
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compare periods')
      return null
    } finally {
      setIsLoadingComparison(false)
    }
  }, [token])

  /**
   * Clear comparison result
   */
  const clearComparison = useCallback(() => {
    setComparison(null)
  }, [])

  /**
   * Clear error
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    periods,
    comparison,
    isLoadingPeriods,
    isLoadingComparison,
    isSaving,
    error,
    fetchPeriods,
    savePeriod,
    comparePeriods,
    clearComparison,
    clearError,
  }
}

export default usePriorPeriod
