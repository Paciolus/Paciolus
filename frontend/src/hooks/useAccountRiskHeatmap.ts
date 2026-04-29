/**
 * useAccountRiskHeatmap Hook (Sprint 688)
 *
 * POSTs normalized signals to /audit/account-risk-heatmap and optionally
 * downloads the CSV export for the same payload.
 */

'use client'

import { useCallback, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import type {
  HeatmapRequest,
  HeatmapResponse,
} from '@/types/accountRiskHeatmap'
import { apiDownload, apiPost, downloadBlob } from '@/utils/apiClient'

export type HeatmapStatus = 'idle' | 'loading' | 'success' | 'error'

export interface UseAccountRiskHeatmapReturn {
  status: HeatmapStatus
  result: HeatmapResponse | null
  error: string
  exporting: boolean
  generate: (payload: HeatmapRequest) => Promise<void>
  downloadCsv: (payload: HeatmapRequest) => Promise<boolean>
  reset: () => void
}

export function useAccountRiskHeatmap(): UseAccountRiskHeatmapReturn {
  const { token } = useAuthSession()
  const [status, setStatus] = useState<HeatmapStatus>('idle')
  const [result, setResult] = useState<HeatmapResponse | null>(null)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState(false)

  const generate = useCallback(
    async (payload: HeatmapRequest) => {
      setStatus('loading')
      setError('')
      setResult(null)
      const { data, ok, error: apiError } = await apiPost<HeatmapResponse>(
        '/audit/account-risk-heatmap',
        token,
        payload,
      )
      if (ok && data) {
        setResult(data)
        setStatus('success')
        return
      }
      setError(apiError ?? 'Failed to build account risk heatmap')
      setStatus('error')
    },
    [token],
  )

  const downloadCsv = useCallback(
    async (payload: HeatmapRequest): Promise<boolean> => {
      if (!token) {
        setError('Not authenticated')
        return false
      }
      setExporting(true)
      try {
        const result = await apiDownload(
          '/audit/account-risk-heatmap/export.csv',
          token,
          { method: 'POST', body: payload },
        )
        if (!result.ok || !result.blob) {
          setError(result.error ?? 'CSV export failed')
          return false
        }
        downloadBlob(result.blob, result.filename ?? 'account_risk_heatmap.csv')
        return true
      } catch (e) {
        setError(e instanceof Error ? e.message : 'CSV export failed')
        return false
      } finally {
        setExporting(false)
      }
    },
    [token],
  )

  const reset = useCallback(() => {
    setStatus('idle')
    setResult(null)
    setError('')
  }, [])

  return { status, result, error, exporting, generate, downloadCsv, reset }
}
