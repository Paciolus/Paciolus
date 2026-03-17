/**
 * useAuditUpload — Generic Audit Upload Hook (Sprint 82)
 *
 * Extracts the duplicated status/result/error + auth error handling pattern
 * shared by useAPTesting, useJETesting, and useBankReconciliation.
 */

import { useState, useCallback } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import type { UploadStatus } from '@/types/shared'
import { uploadFetch } from '@/utils/uploadTransport'

/** Discriminated union on status — Sprint 226
 *  When `status === 'success'`, `result` is guaranteed non-null `T`.
 *  All other states have `result: null`.
 */
export type UseAuditUploadReturn<T> = {
  run: (...files: File[]) => Promise<void>
  reset: () => void
  error: string
} & (
  | { status: 'idle'; result: null }
  | { status: 'loading'; result: null }
  | { status: 'success'; result: T }
  | { status: 'error'; result: null }
)

interface UseAuditUploadOptions<T> {
  endpoint: string
  toolName: string
  buildFormData: (...files: File[]) => FormData
  parseResult: (data: unknown) => T
}

export function useAuditUpload<T>(options: UseAuditUploadOptions<T>): UseAuditUploadReturn<T> {
  const { token, user } = useAuthSession()
  const engagement = useOptionalEngagementContext()
  const engagementId = engagement?.engagementId
  const [status, setStatus] = useState<UploadStatus>('idle')
  const [result, setResult] = useState<T | null>(null)
  const [error, setError] = useState('')

  const run = useCallback(async (...files: File[]) => {
    if (user && user.is_verified === false) {
      setStatus('error')
      setError(`Please verify your email address before running ${options.toolName}.`)
      return
    }

    setStatus('loading')
    setError('')
    setResult(null)

    const formData = options.buildFormData(...files)

    // Sprint 103: Auto-inject engagement_id when linked to a workspace
    if (engagementId) {
      formData.append('engagement_id', engagementId.toString())
    }

    const result = await uploadFetch(options.endpoint, formData, token ?? null)

    if (!result.ok) {
      setStatus('error')
      if (result.status === 401) {
        setError(`Please sign in to run ${options.toolName}.`)
      } else if (result.errorCode === 'EMAIL_NOT_VERIFIED') {
        setError(`Please verify your email address before running ${options.toolName}.`)
      } else if (result.status === 403) {
        setError('Access denied.')
      } else {
        setError(result.error || `Failed to run ${options.toolName}.`)
      }
      return
    }

    setStatus('success')
    setResult(options.parseResult(result.data))

    // Sprint 103: Refresh tool runs + show toast when linked to workspace
    if (engagement && engagementId) {
      engagement.refreshToolRuns()
      engagement.triggerLinkToast(options.toolName)
    }
  }, [token, user, options, engagement, engagementId])

  const reset = useCallback(() => {
    setStatus('idle')
    setResult(null)
    setError('')
  }, [])

  // Type assertion safe: React 18 batches setStatus + setResult in same callback,
  // so consumers never see status='success' with result=null.
  return { status, result, error, run, reset } as UseAuditUploadReturn<T>
}
