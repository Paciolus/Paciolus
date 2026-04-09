/**
 * useAuditUpload — Generic Audit Upload Hook (Sprint 82)
 *
 * Extracts the duplicated status/result/error + auth error handling pattern
 * shared by useAPTesting, useJETesting, and useBankReconciliation.
 *
 * Sprint 585: Actionable error messages + toast notifications on success/error.
 */

import { useState, useCallback } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import { useToast } from '@/contexts/ToastContext'
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

/** Map error codes to actionable user messages */
function getActionableError(
  toolName: string,
  status: number,
  errorCode?: string,
  serverError?: string,
): string {
  if (status === 401) {
    return `Your session has expired. Please sign in again to run ${toolName}.`
  }
  if (errorCode === 'EMAIL_NOT_VERIFIED') {
    return `Email verification required. Check your inbox for a verification link, then try ${toolName} again.`
  }
  if (status === 403) {
    return `Your current plan doesn't include ${toolName}. Upgrade to unlock all diagnostic tools.`
  }
  if (status === 413) {
    return 'File is too large. Maximum upload size is 50 MB. Try splitting your data into smaller files.'
  }
  if (status === 415) {
    return 'Unsupported file format. Please upload a CSV, Excel (.xlsx/.xls), TSV, TXT, OFX, QBO, IIF, PDF, or ODS file.'
  }
  if (status === 422) {
    // Column mapping / validation errors from backend — pass through
    return serverError || `Could not process the file. Check that it has the expected columns (e.g., Account, Debit, Credit) and try again.`
  }
  if (status === 429) {
    return 'Too many requests. Please wait a moment before trying again.'
  }
  if (status >= 500) {
    return 'Our server encountered an issue. Please try again in a few seconds. If this persists, contact support.'
  }
  if (status === 0) {
    return 'Unable to connect to the server. Check your internet connection and try again.'
  }
  return serverError || `Failed to run ${toolName}. Please try again.`
}

export function useAuditUpload<T>(options: UseAuditUploadOptions<T>): UseAuditUploadReturn<T> {
  const { token, user } = useAuthSession()
  const engagement = useOptionalEngagementContext()
  const engagementId = engagement?.engagementId
  const toast = useToast()
  const [status, setStatus] = useState<UploadStatus>('idle')
  const [result, setResult] = useState<T | null>(null)
  const [error, setError] = useState('')

  const run = useCallback(async (...files: File[]) => {
    if (user && user.is_verified === false) {
      const msg = `Email verification required. Check your inbox for a verification link, then try ${options.toolName} again.`
      setStatus('error')
      setError(msg)
      toast.error('Verification required', msg)
      return
    }

    setStatus('loading')
    setError('')
    setResult(null)

    const formData = options.buildFormData(...files)
    const fileName = files[0]?.name ?? 'file'

    // Sprint 103: Auto-inject engagement_id when linked to a workspace
    if (engagementId) {
      formData.append('engagement_id', engagementId.toString())
    }

    const result = await uploadFetch(options.endpoint, formData, token ?? null)

    if (!result.ok) {
      const actionableMsg = getActionableError(
        options.toolName,
        result.status,
        result.errorCode,
        result.error,
      )
      setStatus('error')
      setError(actionableMsg)
      toast.error(`${options.toolName} failed`, actionableMsg)
      return
    }

    const parsed = options.parseResult(result.data)
    setStatus('success')
    setResult(parsed)

    // Sprint 585: Toast notification on successful analysis
    const recordCount = (parsed as Record<string, unknown>)?.record_count
      ?? (parsed as Record<string, unknown>)?.total_records
      ?? (parsed as Record<string, unknown>)?.row_count
    const desc = typeof recordCount === 'number'
      ? `${fileName} — ${recordCount.toLocaleString()} rows analyzed`
      : `${fileName} processed successfully`
    toast.success(`${options.toolName} complete`, desc)

    // Sprint 103: Refresh tool runs + show toast when linked to workspace
    if (engagement && engagementId) {
      engagement.refreshToolRuns()
      engagement.triggerLinkToast(options.toolName)
    }
  }, [token, user, options, engagement, engagementId, toast])

  const reset = useCallback(() => {
    setStatus('idle')
    setResult(null)
    setError('')
  }, [])

  // Type assertion safe: React 18 batches setStatus + setResult in same callback,
  // so consumers never see status='success' with result=null.
  return { status, result, error, run, reset } as UseAuditUploadReturn<T>
}
