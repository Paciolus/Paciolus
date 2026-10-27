'use client'

/**
 * W-2 / W-3 Reconciliation hook — Sprint 689d.
 */

import { useEffect, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { describeW2Error } from '@/components/w2Reconciliation/taxYearSupport'
import type {
  W2ReconciliationRequest,
  W2ReconciliationResponse,
} from '@/types/w2Reconciliation'
import { apiGet } from '@/utils/apiClient'
import { createJsonAnalysisHook, type JsonAnalysisStatus } from './createJsonAnalysisHook'

export interface W2SupportedYears {
  tax_years: number[]
  note: string
}

/** Sprint 839: tax years the app can run, read from the backend (never hard-coded). */
export function useW2SupportedYears(): { supported: W2SupportedYears | null; loaded: boolean } {
  const { token } = useAuthSession()
  const [supported, setSupported] = useState<W2SupportedYears | null>(null)
  const [loaded, setLoaded] = useState(false)
  useEffect(() => {
    let cancelled = false
    apiGet<W2SupportedYears>('/audit/w2-reconciliation/supported-years', token ?? null).then(response => {
      if (cancelled) return
      if (response.ok && response.data && Array.isArray(response.data.tax_years)) setSupported(response.data)
      setLoaded(true)
    })
    return () => { cancelled = true }
  }, [token])
  return { supported, loaded }
}

export type W2Status = JsonAnalysisStatus

export interface UseW2ReconciliationReturn {
  status: W2Status
  result: W2ReconciliationResponse | null
  error: string
  analyze: (payload: W2ReconciliationRequest) => Promise<boolean>
  exportCsv: (payload: W2ReconciliationRequest) => Promise<boolean>
  reset: () => void
}

const useW2Analysis = createJsonAnalysisHook<W2ReconciliationRequest, W2ReconciliationResponse>({
  endpoint: '/audit/w2-reconciliation',
  exportEndpoint: '/audit/w2-reconciliation/export.csv',
  toolName: 'W-2/W-3 Reconciliation',
  analyzeErrorMessage: 'Failed to run W-2 reconciliation',
  exportFilename: 'w2_reconciliation.csv',
  describeError: (error, payload) => describeW2Error(error, payload.tax_year),
})

export function useW2Reconciliation(): UseW2ReconciliationReturn {
  const { status, result, error, analyze, exportCsv, reset } = useW2Analysis()
  return { status, result, error, analyze, exportCsv, reset }
}
