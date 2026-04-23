'use client'

/**
 * Segregation of Duties hook — Sprint 689b.
 *
 * Wraps the three SoD endpoints: GET /audit/sod/rules, POST /audit/sod/analyze,
 * POST /audit/sod/analyze.csv. All endpoints are Enterprise-only
 * (backend returns 403 with {feature: 'sod_checker'} for lower tiers).
 */

import { useCallback, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import type {
  SODAnalysisRequest,
  SODAnalysisResponse,
  SODRule,
  SODRulesResponse,
} from '@/types/sod'
import { apiDownload, apiGet, apiPost, downloadBlob } from '@/utils/apiClient'

export type SODStatus = 'idle' | 'loading' | 'success' | 'error'

export interface UseSODReturn {
  status: SODStatus
  result: SODAnalysisResponse | null
  rules: SODRule[]
  error: string
  analyze: (payload: SODAnalysisRequest) => Promise<boolean>
  loadRules: () => Promise<void>
  exportCsv: (payload: SODAnalysisRequest) => Promise<boolean>
  reset: () => void
}

export function useSOD(): UseSODReturn {
  const { token } = useAuthSession()
  const [status, setStatus] = useState<SODStatus>('idle')
  const [result, setResult] = useState<SODAnalysisResponse | null>(null)
  const [rules, setRules] = useState<SODRule[]>([])
  const [error, setError] = useState('')

  const loadRules = useCallback(async () => {
    const response = await apiGet<SODRulesResponse>('/audit/sod/rules', token)
    if (response.ok && response.data) {
      setRules(response.data.rules)
    }
  }, [token])

  const analyze = useCallback(async (payload: SODAnalysisRequest): Promise<boolean> => {
    setStatus('loading')
    setError('')
    const response = await apiPost<SODAnalysisResponse>('/audit/sod/analyze', token, payload)
    if (response.ok && response.data) {
      setResult(response.data)
      setStatus('success')
      return true
    }
    setStatus('error')
    setError(response.error || 'Failed to run SoD analysis')
    return false
  }, [token])

  const exportCsv = useCallback(async (payload: SODAnalysisRequest): Promise<boolean> => {
    const response = await apiDownload('/audit/sod/analyze.csv', token, {
      method: 'POST',
      body: payload,
    })
    if (response.ok && response.blob) {
      downloadBlob(response.blob, response.filename || 'sod_analysis.csv')
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

  return { status, result, rules, error, analyze, loadRules, exportCsv, reset }
}
