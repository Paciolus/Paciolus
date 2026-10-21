'use client'

/**
 * Book-to-Tax hook — Sprint 689f.
 */

import { useCallback, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import type {
  BookToTaxRequest,
  BookToTaxResponse,
  StandardAdjustment,
  StandardAdjustmentsResponse,
} from '@/types/bookToTax'
import { apiDownload, apiGet, apiPost, downloadBlob } from '@/utils/apiClient'

export type BookToTaxStatus = 'idle' | 'loading' | 'success' | 'error'

export interface UseBookToTaxReturn {
  status: BookToTaxStatus
  result: BookToTaxResponse | null
  standardAdjustments: StandardAdjustment[]
  error: string
  analyze: (payload: BookToTaxRequest) => Promise<boolean>
  exportCsv: (payload: BookToTaxRequest) => Promise<boolean>
  loadStandardAdjustments: () => Promise<void>
  reset: () => void
}

export function useBookToTax(): UseBookToTaxReturn {
  const { token } = useAuthSession()
  // Sprint 791: the engagement link is injected by the hook, not declared on
  // the request type — the page supplies the analysis inputs and the hook owns
  // the workspace link. Same split as useAuditUpload (which appends
  // engagement_id to FormData) and useStatisticalSampling.
  const engagement = useOptionalEngagementContext()
  const engagementId = engagement?.engagementId
  const [status, setStatus] = useState<BookToTaxStatus>('idle')
  const [result, setResult] = useState<BookToTaxResponse | null>(null)
  const [standardAdjustments, setStandardAdjustments] = useState<StandardAdjustment[]>([])
  const [error, setError] = useState('')

  const loadStandardAdjustments = useCallback(async () => {
    const response = await apiGet<StandardAdjustmentsResponse>('/audit/book-to-tax/standard-adjustments', token)
    if (response.ok && response.data) {
      setStandardAdjustments(response.data.standard_adjustments)
    }
  }, [token])

  const analyze = useCallback(async (payload: BookToTaxRequest): Promise<boolean> => {
    setStatus('loading')
    setError('')
    const response = await apiPost<BookToTaxResponse>(
      '/audit/book-to-tax',
      token,
      { ...payload, engagement_id: engagementId ?? undefined },
    )
    if (response.ok && response.data) {
      setResult(response.data)
      setStatus('success')
      // Sprint 791: mirror useAuditUpload's follow-through so the
      // workspace reflects the new workpaper entry instead of going stale.
      if (engagement && engagementId) {
        engagement.refreshToolRuns()
        engagement.triggerLinkToast('Book-to-Tax Reconciliation')
      }
      return true
    }
    setStatus('error')
    setError(response.error || 'Failed to compute book-to-tax reconciliation')
    return false
  }, [token, engagement, engagementId])

  const exportCsv = useCallback(async (payload: BookToTaxRequest): Promise<boolean> => {
    const response = await apiDownload('/audit/book-to-tax/export.csv', token, {
      method: 'POST',
      body: payload,
    })
    if (response.ok && response.blob) {
      downloadBlob(response.blob, response.filename || `book_to_tax_${payload.tax_year}.csv`)
      return true
    }
    setError(response.error || 'Failed to export CSV')
    return false
  }, [token])

  const reset = useCallback(() => {
    setStatus('idle')
    setResult(null)
    setError('')
  }, [])

  return { status, result, standardAdjustments, error, analyze, exportCsv, loadStandardAdjustments, reset }
}
