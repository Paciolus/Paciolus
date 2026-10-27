'use client'

/**
 * Cash Flow Projector hook — Sprint 689g.
 */

import type {
  CashFlowForecastResponse,
  CashFlowProjectionRequest,
} from '@/types/cashFlowProjector'
import { createJsonAnalysisHook, type JsonAnalysisStatus } from './createJsonAnalysisHook'

export type CashFlowStatus = JsonAnalysisStatus

export interface UseCashFlowProjectorReturn {
  status: CashFlowStatus
  result: CashFlowForecastResponse | null
  error: string
  project: (payload: CashFlowProjectionRequest) => Promise<boolean>
  exportCsv: (payload: CashFlowProjectionRequest) => Promise<boolean>
  reset: () => void
}

const useCashFlowAnalysis = createJsonAnalysisHook<CashFlowProjectionRequest, CashFlowForecastResponse>({
  endpoint: '/audit/cash-flow-projector',
  exportEndpoint: '/audit/cash-flow-projector/export.csv',
  toolName: 'Cash Flow Projector',
  analyzeErrorMessage: 'Failed to run cash flow projection',
  exportFilename: 'cash_flow_projection.csv',
})

export function useCashFlowProjector(): UseCashFlowProjectorReturn {
  const { status, result, error, analyze, exportCsv, reset } = useCashFlowAnalysis()
  return { status, result, error, project: analyze, exportCsv, reset }
}
