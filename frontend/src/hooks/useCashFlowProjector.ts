'use client'

/**
 * Cash Flow Projector hook — Sprint 689g.
 */

import { useCallback, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
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
  const [status, setStatus] = useState<CashFlowStatus>('idle')
  const [result, setResult] = useState<CashFlowForecastResponse | null>(null)
  const [error, setError] = useState('')

  const project = useCallback(async (payload: CashFlowProjectionRequest): Promise<boolean> => {
    setStatus('loading')
    setError('')
    const response = await apiPost<CashFlowForecastResponse>('/audit/cash-flow-projector', token, payload)
    if (response.ok && response.data) {
      setResult(response.data)
      setStatus('success')
      return true
    }
    setStatus('error')
    setError(response.error || 'Failed to run cash flow projection')
    return false
  }, [token])

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
