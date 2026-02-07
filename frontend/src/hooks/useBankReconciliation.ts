/**
 * useBankReconciliation Hook (Sprint 78)
 *
 * Manages the dual-file upload -> reconciliation -> results flow.
 * Zero-Storage: files processed on backend, results ephemeral.
 */

import { useState, useCallback } from 'react'
import { useAuth } from '@/context/AuthContext'
import type { BankRecResult } from '@/types/bankRec'

const API_URL = process.env.NEXT_PUBLIC_API_URL

export interface UseBankReconciliationReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: BankRecResult | null
  error: string
  reconcile: (bankFile: File, ledgerFile: File) => Promise<void>
  reset: () => void
}

export function useBankReconciliation(): UseBankReconciliationReturn {
  const { token, user } = useAuth()
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [result, setResult] = useState<BankRecResult | null>(null)
  const [error, setError] = useState('')

  const reconcile = useCallback(async (bankFile: File, ledgerFile: File) => {
    if (user && user.is_verified === false) {
      setStatus('error')
      setError('Please verify your email address before running bank reconciliation.')
      return
    }

    setStatus('loading')
    setError('')
    setResult(null)

    const formData = new FormData()
    formData.append('bank_file', bankFile)
    formData.append('ledger_file', ledgerFile)

    try {
      const response = await fetch(`${API_URL}/audit/bank-reconciliation`, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: formData,
      })

      if (response.status === 401) {
        setStatus('error')
        setError('Please sign in to run bank reconciliation.')
        return
      }
      if (response.status === 403) {
        const errData = await response.json().catch(() => ({}))
        const detail = errData.detail
        if (typeof detail === 'object' && detail?.code === 'EMAIL_NOT_VERIFIED') {
          setStatus('error')
          setError('Please verify your email address before running bank reconciliation.')
          return
        }
        setStatus('error')
        setError('Access denied.')
        return
      }

      const data = await response.json()

      if (response.ok) {
        setStatus('success')
        setResult(data as BankRecResult)
      } else {
        setStatus('error')
        setError(data.detail || data.message || 'Failed to reconcile bank statement.')
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

  return { status, result, error, reconcile, reset }
}
