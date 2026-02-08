/**
 * useAuditUpload — Generic Audit Upload Hook (Sprint 82)
 *
 * Extracts the duplicated status/result/error + auth error handling pattern
 * shared by useAPTesting, useJETesting, and useBankReconciliation.
 */

import { useState, useCallback } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'

const API_URL = process.env.NEXT_PUBLIC_API_URL

type AuditStatus = 'idle' | 'loading' | 'success' | 'error'

export interface UseAuditUploadReturn<T> {
  status: AuditStatus
  result: T | null
  error: string
  run: (...files: File[]) => Promise<void>
  reset: () => void
}

interface UseAuditUploadOptions<T> {
  endpoint: string
  toolName: string
  buildFormData: (...files: File[]) => FormData
  parseResult: (data: unknown) => T
}

export function useAuditUpload<T>(options: UseAuditUploadOptions<T>): UseAuditUploadReturn<T> {
  const { token, user } = useAuth()
  const engagement = useOptionalEngagementContext()
  const engagementId = engagement?.activeEngagement?.id
  const [status, setStatus] = useState<AuditStatus>('idle')
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

    try {
      const response = await fetch(`${API_URL}${options.endpoint}`, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: formData,
      })

      if (response.status === 401) {
        setStatus('error')
        setError(`Please sign in to run ${options.toolName}.`)
        return
      }
      if (response.status === 403) {
        const errData = await response.json().catch(() => ({}))
        const detail = errData.detail
        if (typeof detail === 'object' && detail?.code === 'EMAIL_NOT_VERIFIED') {
          setStatus('error')
          setError(`Please verify your email address before running ${options.toolName}.`)
          return
        }
        setStatus('error')
        setError('Access denied.')
        return
      }

      const data = await response.json()

      if (response.ok) {
        setStatus('success')
        setResult(options.parseResult(data))

        // Sprint 103: Refresh tool runs + show toast when linked to workspace
        if (engagement && engagementId) {
          engagement.refreshToolRuns()
          engagement.triggerLinkToast(options.toolName)
        }
      } else {
        setStatus('error')
        setError(data.detail || data.message || `Failed to run ${options.toolName}.`)
      }
    } catch {
      setStatus('error')
      setError('Unable to connect to server. Please try again.')
    }
  }, [token, user, options, engagement, engagementId])

  const reset = useCallback(() => {
    setStatus('idle')
    setResult(null)
    setError('')
  }, [])

  return { status, result, error, run, reset }
}
