'use client'

/**
 * Intercompany Elimination hook — Sprint 689c.
 *
 * Wraps POST /audit/intercompany-elimination (JSON → result) and
 * POST /audit/intercompany-elimination/export.csv (JSON → CSV blob).
 * Free tier receives 403 TIER_LIMIT_EXCEEDED after the Sprint 689c
 * backend gate — `UpgradeGate` on the page prevents reaching this code
 * path for Free, but the hook still surfaces the server-side error if
 * the gate is ever bypassed.
 */

import type {
  IntercompanyEliminationRequest,
  IntercompanyEliminationResponse,
} from '@/types/intercompany'
import { createJsonAnalysisHook, type JsonAnalysisStatus } from './createJsonAnalysisHook'

export type IntercompanyStatus = JsonAnalysisStatus

export interface UseIntercompanyEliminationReturn {
  status: IntercompanyStatus
  result: IntercompanyEliminationResponse | null
  error: string
  analyze: (payload: IntercompanyEliminationRequest) => Promise<boolean>
  exportCsv: (payload: IntercompanyEliminationRequest) => Promise<boolean>
  reset: () => void
}

const useIntercompanyAnalysis = createJsonAnalysisHook<IntercompanyEliminationRequest, IntercompanyEliminationResponse>({
  endpoint: '/audit/intercompany-elimination',
  exportEndpoint: '/audit/intercompany-elimination/export.csv',
  toolName: 'Intercompany Elimination',
  analyzeErrorMessage: 'Failed to run intercompany elimination',
  exportFilename: 'intercompany_consolidation.csv',
})

export function useIntercompanyElimination(): UseIntercompanyEliminationReturn {
  const { status, result, error, analyze, exportCsv, reset } = useIntercompanyAnalysis()
  return { status, result, error, analyze, exportCsv, reset }
}
