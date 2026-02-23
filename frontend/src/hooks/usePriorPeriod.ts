/**
 * usePriorPeriod Hook - Sprint 51
 * Sprint 147: Migrated from direct fetch to apiClient for caching, retry, deduplication.
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
import { apiGet, apiPost } from '@/utils'

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
      const { data, ok, error: apiError } = await apiGet<PriorPeriodSummary[]>(
        `/clients/${clientId}/periods`,
        token,
      )

      if (!ok || !data) {
        throw new Error(apiError || 'Failed to fetch periods')
      }

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
      const { data: result, ok, error: apiError } = await apiPost<{ period_id: number }>(
        `/clients/${clientId}/periods`,
        token,
        data,
      )

      if (!ok || !result) {
        throw new Error(apiError || 'Failed to save period')
      }

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
      const { data: result, ok, error: apiError } = await apiPost<PeriodComparison>(
        '/audit/compare',
        token,
        data,
      )

      if (!ok || !result) {
        throw new Error(apiError || 'Failed to compare periods')
      }

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
