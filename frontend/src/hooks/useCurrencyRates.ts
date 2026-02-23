'use client'

/**
 * Currency Rate Management Hook — Sprint 258
 *
 * Manages exchange rate table upload, manual entry, and status for
 * multi-currency TB conversion.
 */

import { useState, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import type { UploadStatus } from '@/types/shared'
import { apiPost, apiFetch, apiDelete } from '@/utils/apiClient'

// =============================================================================
// TYPES
// =============================================================================

export interface RateTableStatus {
  has_rates: boolean
  rate_count: number
  presentation_currency: string | null
  currency_pairs: string[]
}

export interface RateUploadResult {
  rate_count: number
  presentation_currency: string
  currency_pairs: string[]
  uploaded_at: string
}

export interface SingleRateResult {
  from_currency: string
  to_currency: string
  rate: string
  presentation_currency: string
  total_rates: number
}

// =============================================================================
// HOOK
// =============================================================================

interface UseCurrencyRatesReturn {
  /** Current rate table status */
  rateStatus: RateTableStatus | null
  /** Upload status for rate table CSV */
  uploadStatus: UploadStatus
  /** Error message if any */
  error: string
  /** Upload a CSV rate table file */
  uploadRateTable: (file: File, presentationCurrency: string) => Promise<boolean>
  /** Add a single manual rate */
  addSingleRate: (from: string, to: string, rate: string, presentationCurrency?: string) => Promise<boolean>
  /** Refresh rate table status from server */
  refreshStatus: () => Promise<void>
  /** Clear all rates from session */
  clearRates: () => Promise<boolean>
}

export function useCurrencyRates(): UseCurrencyRatesReturn {
  const { token } = useAuth()
  const [rateStatus, setRateStatus] = useState<RateTableStatus | null>(null)
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle')
  const [error, setError] = useState('')

  const refreshStatus = useCallback(async () => {
    const response = await apiFetch<RateTableStatus>('/audit/currency-rates', token)
    if (response.ok && response.data) {
      setRateStatus(response.data)
    }
  }, [token])

  const uploadRateTable = useCallback(async (file: File, presentationCurrency: string): Promise<boolean> => {
    setUploadStatus('loading')
    setError('')

    const formData = new FormData()
    formData.append('file', file)
    formData.append('presentation_currency', presentationCurrency)

    const response = await apiPost<RateUploadResult>('/audit/currency-rates', token, formData)

    if (response.ok && response.data) {
      setUploadStatus('success')
      setRateStatus({
        has_rates: true,
        rate_count: response.data.rate_count,
        presentation_currency: response.data.presentation_currency,
        currency_pairs: response.data.currency_pairs,
      })
      return true
    } else {
      setUploadStatus('error')
      setError(response.error || 'Failed to upload rate table')
      return false
    }
  }, [token])

  const addSingleRate = useCallback(async (
    from: string,
    to: string,
    rate: string,
    presentationCurrency?: string,
  ): Promise<boolean> => {
    setError('')

    const response = await apiPost<SingleRateResult>('/audit/currency-rate', token, {
      from_currency: from.toUpperCase(),
      to_currency: to.toUpperCase(),
      rate,
      presentation_currency: presentationCurrency?.toUpperCase() || undefined,
    })

    if (response.ok && response.data) {
      setRateStatus({
        has_rates: true,
        rate_count: response.data.total_rates,
        presentation_currency: response.data.presentation_currency,
        currency_pairs: [],
      })
      return true
    } else {
      setError(response.error || 'Failed to add rate')
      return false
    }
  }, [token])

  const clearRates = useCallback(async (): Promise<boolean> => {
    const response = await apiDelete('/audit/currency-rates', token)
    if (response.ok) {
      setRateStatus(null)
      setUploadStatus('idle')
      setError('')
      return true
    }
    return false
  }, [token])

  return {
    rateStatus,
    uploadStatus,
    error,
    uploadRateTable,
    addSingleRate,
    refreshStatus,
    clearRates,
  }
}
