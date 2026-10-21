'use client'

/**
 * Intercompany Elimination hook — Sprint 689c.
 *
 * Wraps POST /audit/intercompany-elimination (JSON → result) and
 * POST /audit/intercompany-elimination/export.csv (JSON → CSV blob).
 * Free tier receives 403 TIER_LIMIT_EXCEEDED after the Sprint 689c
 * backend gate — `UpgradeGate` on the page prevents reaching this code
 * path for Free, but the hook still surfaces the server-side error if
 * the gate is ever bypassed.
 */

import { useCallback, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import type {
  IntercompanyEliminationRequest,
  IntercompanyEliminationResponse,
} from '@/types/intercompany'
import { apiDownload, apiPost, downloadBlob } from '@/utils/apiClient'

export type IntercompanyStatus = 'idle' | 'loading' | 'success' | 'error'

export interface UseIntercompanyEliminationReturn {
  status: IntercompanyStatus
  result: IntercompanyEliminationResponse | null
  error: string
  analyze: (payload: IntercompanyEliminationRequest) => Promise<boolean>
  exportCsv: (payload: IntercompanyEliminationRequest) => Promise<boolean>
  reset: () => void
}

export function useIntercompanyElimination(): UseIntercompanyEliminationReturn {
  const { token } = useAuthSession()
  // Sprint 791: the engagement link is injected by the hook, not declared on
  // the request type — the page supplies the analysis inputs and the hook owns
  // the workspace link. Same split as useAuditUpload (which appends
  // engagement_id to FormData) and useStatisticalSampling.
  const engagement = useOptionalEngagementContext()
  const engagementId = engagement?.engagementId
  const [status, setStatus] = useState<IntercompanyStatus>('idle')
  const [result, setResult] = useState<IntercompanyEliminationResponse | null>(null)
  const [error, setError] = useState('')

  const analyze = useCallback(async (payload: IntercompanyEliminationRequest): Promise<boolean> => {
    setStatus('loading')
    setError('')
    const response = await apiPost<IntercompanyEliminationResponse>(
      '/audit/intercompany-elimination',
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
        engagement.triggerLinkToast('Intercompany Elimination')
      }
      return true
    }
    setStatus('error')
    setError(response.error || 'Failed to run intercompany elimination')
    return false
  }, [token, engagement, engagementId])

  const exportCsv = useCallback(async (payload: IntercompanyEliminationRequest): Promise<boolean> => {
    const response = await apiDownload('/audit/intercompany-elimination/export.csv', token, {
      method: 'POST',
      body: payload,
    })
    if (response.ok && response.blob) {
      downloadBlob(response.blob, response.filename || 'intercompany_consolidation.csv')
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
