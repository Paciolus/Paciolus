'use client'

/**
 * JSON Analysis Hook Factory — Sprint 820.
 *
 * The six promoted tools (SoD, Form 1099, W-2/W-3, Book-to-Tax, Intercompany,
 * Cash Flow Projector) post a JSON body and get a JSON result back, plus a CSV
 * export of the same payload. This factory owns that shared state machine; the
 * per-tool hooks pass endpoint config and add their own extras (rules lists,
 * method names) on top. The upload-based testing tools use `createTestingHook`.
 *
 * Sprint 791: the engagement link is injected here, not declared on the
 * request type — the page supplies the analysis inputs and the hook owns the
 * workspace link. Same split as useAuditUpload (which appends engagement_id to
 * FormData) and useStatisticalSampling.
 */

import { useCallback, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import { apiDownload, apiPost, downloadBlob } from '@/utils/apiClient'

export type JsonAnalysisStatus = 'idle' | 'loading' | 'success' | 'error'

export interface JsonAnalysisHookConfig<TRequest> {
  /** POST endpoint returning the JSON result. */
  endpoint: string
  /** POST endpoint returning the CSV export of the same payload. */
  exportEndpoint: string
  /** Tool name shown in the engagement link toast. */
  toolName: string
  /** Fallback message when the analysis call fails without a usable error. */
  analyzeErrorMessage: string
  /** CSV filename used when the response carries none. */
  exportFilename: string | ((payload: TRequest) => string)
  /** Optional rewrite of a server error into a page-specific message. */
  describeError?: (error: string | undefined, payload: TRequest) => string | undefined
}

export interface JsonAnalysisHookReturn<TRequest, TResponse> {
  status: JsonAnalysisStatus
  result: TResponse | null
  error: string
  analyze: (payload: TRequest) => Promise<boolean>
  exportCsv: (payload: TRequest) => Promise<boolean>
  reset: () => void
  /** Bearer token, exposed so wrapping hooks can make their own calls. */
  token: string | null
}

export function createJsonAnalysisHook<TRequest extends object, TResponse>(
  config: JsonAnalysisHookConfig<TRequest>,
): () => JsonAnalysisHookReturn<TRequest, TResponse> {
  const { endpoint, exportEndpoint, toolName, analyzeErrorMessage, exportFilename, describeError } = config
  const describe = (error: string | undefined, payload: TRequest) =>
    describeError ? describeError(error, payload) : error

  return function useJsonAnalysis(): JsonAnalysisHookReturn<TRequest, TResponse> {
    const { token } = useAuthSession()
    const engagement = useOptionalEngagementContext()
    const engagementId = engagement?.engagementId
    const [status, setStatus] = useState<JsonAnalysisStatus>('idle')
    const [result, setResult] = useState<TResponse | null>(null)
    const [error, setError] = useState('')

    const analyze = useCallback(async (payload: TRequest): Promise<boolean> => {
      setStatus('loading')
      setError('')
      const response = await apiPost<TResponse>(
        endpoint,
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
          engagement.triggerLinkToast(toolName)
        }
        return true
      }
      setStatus('error')
      setError(describe(response.error, payload) || analyzeErrorMessage)
      return false
    }, [token, engagement, engagementId])

    const exportCsv = useCallback(async (payload: TRequest): Promise<boolean> => {
      const response = await apiDownload(exportEndpoint, token, {
        method: 'POST',
        body: payload,
      })
      if (response.ok && response.blob) {
        const fallback = typeof exportFilename === 'function' ? exportFilename(payload) : exportFilename
        downloadBlob(response.blob, response.filename || fallback)
        return true
      }
      setError(describe(response.error, payload) || 'Failed to export CSV')
      return false
    }, [token])

    const reset = useCallback(() => {
      setStatus('idle')
      setResult(null)
      setError('')
    }, [])

    return { status, result, error, analyze, exportCsv, reset, token }
  }
}
