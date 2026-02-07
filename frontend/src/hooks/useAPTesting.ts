/**
 * useAPTesting Hook (Sprint 75)
 *
 * Manages the AP Testing upload -> processing -> results flow.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { useState, useCallback } from 'react'
import { useAuth } from '@/context/AuthContext'
import type { APTestingResult } from '@/types/apTesting'

const API_URL = process.env.NEXT_PUBLIC_API_URL

export interface UseAPTestingReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: APTestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

export function useAPTesting(): UseAPTestingReturn {
  const { token, user } = useAuth()
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [result, setResult] = useState<APTestingResult | null>(null)
  const [error, setError] = useState('')

  const runTests = useCallback(async (file: File) => {
    if (user && user.is_verified === false) {
      setStatus('error')
      setError('Please verify your email address before running AP tests.')
      return
    }

    setStatus('loading')
    setError('')
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_URL}/audit/ap-payments`, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: formData,
      })

      if (response.status === 401) {
        setStatus('error')
        setError('Please sign in to run AP payment tests.')
        return
      }
      if (response.status === 403) {
        const errData = await response.json().catch(() => ({}))
        const detail = errData.detail
        if (typeof detail === 'object' && detail?.code === 'EMAIL_NOT_VERIFIED') {
          setStatus('error')
          setError('Please verify your email address before running AP tests.')
          return
        }
        setStatus('error')
        setError('Access denied.')
        return
      }

      const data = await response.json()

      if (response.ok) {
        setStatus('success')
        setResult(data as APTestingResult)
      } else {
        setStatus('error')
        setError(data.detail || data.message || 'Failed to analyze AP Payment Register.')
      }
    } catch {
      setStatus('error')
      setError('Unable to connect to server. Please try again.')
    }
  }, [token, user])

  const reset = useCallback(() => {
    setStatus('idle')
    setResult(null)
    setError('')
  }, [])

  return { status, result, error, runTests, reset }
}
