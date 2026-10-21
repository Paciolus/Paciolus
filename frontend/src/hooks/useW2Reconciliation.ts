'use client'

/**
 * W-2 / W-3 Reconciliation hook — Sprint 689d.
 */

import { useCallback, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import type {
  W2ReconciliationRequest,
  W2ReconciliationResponse,
} from '@/types/w2Reconciliation'
import { apiDownload, apiPost, downloadBlob } from '@/utils/apiClient'

export type W2Status = 'idle' | 'loading' | 'success' | 'error'

export interface UseW2ReconciliationReturn {
  status: W2Status
  result: W2ReconciliationResponse | null
  error: string
  analyze: (payload: W2ReconciliationRequest) => Promise<boolean>
  exportCsv: (payload: W2ReconciliationRequest) => Promise<boolean>
  reset: () => void
}

export function useW2Reconciliation(): UseW2ReconciliationReturn {
  const { token } = useAuthSession()
  // Sprint 791: the engagement link is injected by the hook, not declared on
  // the request type — the page supplies the analysis inputs and the hook owns
  // the workspace link. Same split as useAuditUpload (which appends
  // engagement_id to FormData) and useStatisticalSampling.
  const engagement = useOptionalEngagementContext()
  const engagementId = engagement?.engagementId
  const [status, setStatus] = useState<W2Status>('idle')
  const [result, setResult] = useState<W2ReconciliationResponse | null>(null)
  const [error, setError] = useState('')

  const analyze = useCallback(async (payload: W2ReconciliationRequest): Promise<boolean> => {
    setStatus('loading')
    setError('')
    const response = await apiPost<W2ReconciliationResponse>(
      '/audit/w2-reconciliation',
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
        engagement.triggerLinkToast('W-2/W-3 Reconciliation')
      }
      return true
    }
    setStatus('error')
    setError(response.error || 'Failed to run W-2 reconciliation')
    return false
  }, [token, engagement, engagementId])

  const exportCsv = useCallback(async (payload: W2ReconciliationRequest): Promise<boolean> => {
    const response = await apiDownload('/audit/w2-reconciliation/export.csv', token, {
      method: 'POST',
      body: payload,
    })
    if (response.ok && response.blob) {
      downloadBlob(response.blob, response.filename || 'w2_reconciliation.csv')
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

  return { status, result, error, analyze, exportCsv, reset }
}
