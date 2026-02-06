/**
 * useJETesting Hook (Sprint 66)
 *
 * Manages the JE Testing upload → processing → results flow.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { useState, useCallback } from 'react'
import { useAuth } from '@/context/AuthContext'
import type { JETestingResult } from '@/types/jeTesting'

const API_URL = process.env.NEXT_PUBLIC_API_URL

export interface UseJETestingReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: JETestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

export function useJETesting(): UseJETestingReturn {
  const { token, user } = useAuth()
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [result, setResult] = useState<JETestingResult | null>(null)
  const [error, setError] = useState('')

  const runTests = useCallback(async (file: File) => {
    if (user && user.is_verified === false) {
      setStatus('error')
      setError('Please verify your email address before running JE tests.')
      return
    }

    setStatus('loading')
    setError('')
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_URL}/audit/journal-entries`, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: formData,
      })

      if (response.status === 401) {
        setStatus('error')
        setError('Please sign in to run journal entry tests.')
        return
      }
      if (response.status === 403) {
        const errData = await response.json().catch(() => ({}))
        const detail = errData.detail
        if (typeof detail === 'object' && detail?.code === 'EMAIL_NOT_VERIFIED') {
          setStatus('error')
          setError('Please verify your email address before running JE tests.')
          return
        }
        setStatus('error')
        setError('Access denied.')
        return
      }

      const data = await response.json()

      if (response.ok) {
        setStatus('success')
        setResult(data as JETestingResult)
      } else {
        setStatus('error')
        setError(data.detail || data.message || 'Failed to analyze GL file.')
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
