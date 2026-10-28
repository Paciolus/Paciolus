'use client'

/**
 * Segregation of Duties hook — Sprint 689b.
 *
 * Wraps the three SoD endpoints: GET /audit/sod/rules, POST /audit/sod/analyze,
 * POST /audit/sod/analyze.csv. Available on every paid tier as of Sprint 789
 * (previously Enterprise-only, which contradicted the pricing page and Terms);
 * Free tier still gets a 403 from the standard entitlement check.
 */

import { useCallback, useState } from 'react'
import type {
  SODAnalysisRequest,
  SODAnalysisResponse,
  SODRule,
  SODRulesResponse,
} from '@/types/sod'
import { apiGet } from '@/utils/apiClient'
import { createJsonAnalysisHook, type JsonAnalysisStatus } from './createJsonAnalysisHook'

export type SODStatus = JsonAnalysisStatus

export interface UseSODReturn {
  status: SODStatus
  result: SODAnalysisResponse | null
  rules: SODRule[]
  error: string
  analyze: (payload: SODAnalysisRequest) => Promise<boolean>
  loadRules: () => Promise<void>
  exportCsv: (payload: SODAnalysisRequest) => Promise<boolean>
  reset: () => void
}

const useSODAnalysis = createJsonAnalysisHook<SODAnalysisRequest, SODAnalysisResponse>({
  endpoint: '/audit/sod/analyze',
  exportEndpoint: '/audit/sod/analyze.csv',
  toolName: 'Segregation of Duties',
  analyzeErrorMessage: 'Failed to run SoD analysis',
  exportFilename: 'sod_analysis.csv',
})

export function useSOD(): UseSODReturn {
  const { status, result, error, analyze, exportCsv, reset, token } = useSODAnalysis()
  const [rules, setRules] = useState<SODRule[]>([])

  const loadRules = useCallback(async () => {
    const response = await apiGet<SODRulesResponse>('/audit/sod/rules', token)
    if (response.ok && response.data) {
      setRules(response.data.rules)
    }
  }, [token])

  return { status, result, rules, error, analyze, loadRules, exportCsv, reset }
}
