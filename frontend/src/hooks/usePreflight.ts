'use client'

import { useState, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import { API_URL } from '@/utils/constants'
import { getCsrfToken } from '@/utils/apiClient'
import type { PreFlightReport } from '@/types/preflight'
import type { UploadStatus } from '@/types/shared'

export interface UsePreflightReturn {
  status: UploadStatus
  report: PreFlightReport | null
  error: string
  runPreflight: (file: File) => Promise<void>
  reset: () => void
}

export function usePreflight(): UsePreflightReturn {
  const { token } = useAuth()
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

    try {
      const csrfToken = getCsrfToken()
      const response = await fetch(`${API_URL}/audit/preflight`, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
        },
        body: formData,
      })

      if (response.status === 401) {
        setStatus('error')
        setError('Please sign in to run pre-flight checks.')
        return
      }
      if (response.status === 403) {
        setStatus('error')
        setError('Please verify your email address before running pre-flight checks.')
        return
      }

      const data = await response.json()

      if (response.ok) {
        setStatus('success')
        setReport(data as PreFlightReport)
      } else {
        setStatus('error')
        setError(data.detail || 'Pre-flight check failed')
      }
    } catch {
      setStatus('error')
      setError('Unable to connect to server. Please try again.')
    }
  }, [token, engagement])

  const reset = useCallback(() => {
    setStatus('idle')
    setReport(null)
    setError('')
  }, [])

  return { status, report, error, runPreflight, reset }
}
