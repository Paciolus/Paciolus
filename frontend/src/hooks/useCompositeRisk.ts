/**
 * useCompositeRisk Hook (Sprint 688)
 *
 * POSTs auditor-provided risk assessments to /composite-risk/profile and
 * returns the structured ISA 315 composite risk profile.
 */

'use client'

import { useCallback, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import type {
  CompositeRiskProfileRequest,
  CompositeRiskProfileResponse,
} from '@/types/compositeRisk'
import { apiPost } from '@/utils/apiClient'

export type CompositeRiskStatus = 'idle' | 'loading' | 'success' | 'error'

export interface UseCompositeRiskReturn {
  status: CompositeRiskStatus
  result: CompositeRiskProfileResponse | null
  error: string
  buildProfile: (payload: CompositeRiskProfileRequest) => Promise<void>
  reset: () => void
}

export function useCompositeRisk(): UseCompositeRiskReturn {
  const { token } = useAuthSession()
  const [status, setStatus] = useState<CompositeRiskStatus>('idle')
  const [result, setResult] = useState<CompositeRiskProfileResponse | null>(null)
  const [error, setError] = useState('')

  const buildProfile = useCallback(
    async (payload: CompositeRiskProfileRequest) => {
      setStatus('loading')
      setError('')
      setResult(null)
      const { data, ok, error: apiError } = await apiPost<CompositeRiskProfileResponse>(
        '/composite-risk/profile',
        token,
        payload,
      )
      if (ok && data) {
        setResult(data)
        setStatus('success')
        return
      }
      setError(apiError ?? 'Failed to build composite risk profile')
      setStatus('error')
    },
    [token],
  )

  const reset = useCallback(() => {
    setStatus('idle')
    setResult(null)
    setError('')
  }, [])

  return { status, result, error, buildProfile, reset }
}
