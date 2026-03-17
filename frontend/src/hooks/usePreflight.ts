'use client'

import { useState, useCallback } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import type { PreFlightReport } from '@/types/preflight'
import type { UploadStatus } from '@/types/shared'
import { uploadFetch } from '@/utils/uploadTransport'

export interface UsePreflightReturn {
  status: UploadStatus
  report: PreFlightReport | null
  error: string
  runPreflight: (file: File) => Promise<void>
  reset: () => void
}

export function usePreflight(): UsePreflightReturn {
  const { token } = useAuthSession()
  const engagement = useOptionalEngagementContext()

  const [status, setStatus] = useState<UploadStatus>('idle')
  const [report, setReport] = useState<PreFlightReport | null>(null)
  const [error, setError] = useState('')

  const runPreflight = useCallback(async (file: File) => {
    setStatus('loading')
    setReport(null)
    setError('')

    const formData = new FormData()
    formData.append('file', file)

    if (engagement?.engagementId) {
      formData.append('engagement_id', engagement.engagementId.toString())
    }

    const result = await uploadFetch<PreFlightReport>('/audit/preflight', formData, token ?? null)

    if (!result.ok) {
      setStatus('error')
      if (result.status === 401) {
        setError('Please sign in to run pre-flight checks.')
      } else if (result.status === 403) {
        setError('Please verify your email address before running pre-flight checks.')
      } else {
        setError(result.error || 'Pre-flight check failed')
      }
      return
    }

    setStatus('success')
    setReport(result.data as PreFlightReport)
  }, [token, engagement])

  const reset = useCallback(() => {
    setStatus('idle')
    setReport(null)
    setError('')
  }, [])

  return { status, report, error, runPreflight, reset }
}
