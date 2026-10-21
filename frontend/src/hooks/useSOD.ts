'use client'

/**
 * Segregation of Duties hook — Sprint 689b.
 *
 * Wraps the three SoD endpoints: GET /audit/sod/rules, POST /audit/sod/analyze,
 * POST /audit/sod/analyze.csv. Available on every paid tier as of Sprint 789
 * (previously Enterprise-only, which contradicted the pricing page and Terms);
 * Free tier still gets a 403 from the standard entitlement check.
 */

import { useCallback, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
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
  // Sprint 791: the engagement link is injected by the hook, not declared on
  // the request type — the page supplies the analysis inputs and the hook owns
  // the workspace link. Same split as useAuditUpload (which appends
  // engagement_id to FormData) and useStatisticalSampling.
  const engagement = useOptionalEngagementContext()
  const engagementId = engagement?.engagementId
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
    const response = await apiPost<SODAnalysisResponse>(
      '/audit/sod/analyze',
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
        engagement.triggerLinkToast('Segregation of Duties')
      }
      return true
    }
    setStatus('error')
    setError(response.error || 'Failed to run SoD analysis')
    return false
  }, [token, engagement, engagementId])

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
