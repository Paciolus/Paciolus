'use client'

/**
 * Cash Flow Projector hook — Sprint 689g.
 */

import { useCallback, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import type {
  CashFlowForecastResponse,
  CashFlowProjectionRequest,
} from '@/types/cashFlowProjector'
import { apiDownload, apiPost, downloadBlob } from '@/utils/apiClient'

export type CashFlowStatus = 'idle' | 'loading' | 'success' | 'error'

export interface UseCashFlowProjectorReturn {
  status: CashFlowStatus
  result: CashFlowForecastResponse | null
  error: string
  project: (payload: CashFlowProjectionRequest) => Promise<boolean>
  exportCsv: (payload: CashFlowProjectionRequest) => Promise<boolean>
  reset: () => void
}

export function useCashFlowProjector(): UseCashFlowProjectorReturn {
  const { token } = useAuthSession()
  // Sprint 791: the engagement link is injected by the hook, not declared on
  // the request type — the page supplies the analysis inputs and the hook owns
  // the workspace link. Same split as useAuditUpload (which appends
  // engagement_id to FormData) and useStatisticalSampling.
  const engagement = useOptionalEngagementContext()
  const engagementId = engagement?.engagementId
  const [status, setStatus] = useState<CashFlowStatus>('idle')
  const [result, setResult] = useState<CashFlowForecastResponse | null>(null)
  const [error, setError] = useState('')

  const project = useCallback(async (payload: CashFlowProjectionRequest): Promise<boolean> => {
    setStatus('loading')
    setError('')
    const response = await apiPost<CashFlowForecastResponse>(
      '/audit/cash-flow-projector',
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
        engagement.triggerLinkToast('Cash Flow Projector')
      }
      return true
    }
    setStatus('error')
    setError(response.error || 'Failed to run cash flow projection')
    return false
  }, [token, engagement, engagementId])

  const exportCsv = useCallback(async (payload: CashFlowProjectionRequest): Promise<boolean> => {
    const response = await apiDownload('/audit/cash-flow-projector/export.csv', token, {
      method: 'POST',
      body: payload,
    })
    if (response.ok && response.blob) {
      downloadBlob(response.blob, response.filename || 'cash_flow_projection.csv')
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

  return { status, result, error, project, exportCsv, reset }
}
