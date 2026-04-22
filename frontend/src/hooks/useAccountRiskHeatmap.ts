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
import { apiPost } from '@/utils/apiClient'

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
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || ''}/audit/account-risk-heatmap/export.csv`,
          {
            method: 'POST',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
              'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify(payload),
          },
        )
        if (!response.ok) {
          setError('CSV export failed')
          return false
        }
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = 'account_risk_heatmap.csv'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
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
