'use client'

/**
 * Form 1099 Preparation hook — Sprint 689e.
 */

import { useCallback, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import type { Form1099Request, Form1099Response } from '@/types/form1099'
import { apiDownload, apiPost, downloadBlob } from '@/utils/apiClient'

export type Form1099Status = 'idle' | 'loading' | 'success' | 'error'

export interface UseForm1099Return {
  status: Form1099Status
  result: Form1099Response | null
  error: string
  analyze: (payload: Form1099Request) => Promise<boolean>
  exportCsv: (payload: Form1099Request) => Promise<boolean>
  reset: () => void
}

export function useForm1099(): UseForm1099Return {
  const { token } = useAuthSession()
  // Sprint 791: the engagement link is injected by the hook, not declared on
  // the request type — the page supplies the analysis inputs and the hook owns
  // the workspace link. Same split as useAuditUpload (which appends
  // engagement_id to FormData) and useStatisticalSampling.
  const engagement = useOptionalEngagementContext()
  const engagementId = engagement?.engagementId
  const [status, setStatus] = useState<Form1099Status>('idle')
  const [result, setResult] = useState<Form1099Response | null>(null)
  const [error, setError] = useState('')

  const analyze = useCallback(async (payload: Form1099Request): Promise<boolean> => {
    setStatus('loading')
    setError('')
    const response = await apiPost<Form1099Response>(
      '/audit/form-1099',
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
        engagement.triggerLinkToast('Form 1099 Preparation')
      }
      return true
    }
    setStatus('error')
    setError(response.error || 'Failed to prepare 1099 candidates')
    return false
  }, [token, engagement, engagementId])

  const exportCsv = useCallback(async (payload: Form1099Request): Promise<boolean> => {
    const response = await apiDownload('/audit/form-1099/export.csv', token, {
      method: 'POST',
      body: payload,
    })
    if (response.ok && response.blob) {
      downloadBlob(response.blob, response.filename || `form_1099_candidates_${payload.tax_year}.csv`)
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
