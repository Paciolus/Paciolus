'use client'

/**
 * 1099 Vendor Threshold Review hook — Sprint 689e.
 */

import type { Form1099Request, Form1099Response } from '@/types/form1099'
import { createJsonAnalysisHook, type JsonAnalysisStatus } from './createJsonAnalysisHook'

export type Form1099Status = JsonAnalysisStatus

export interface UseForm1099Return {
  status: Form1099Status
  result: Form1099Response | null
  error: string
  analyze: (payload: Form1099Request) => Promise<boolean>
  exportCsv: (payload: Form1099Request) => Promise<boolean>
  reset: () => void
}

const useForm1099Analysis = createJsonAnalysisHook<Form1099Request, Form1099Response>({
  endpoint: '/audit/form-1099',
  exportEndpoint: '/audit/form-1099/export.csv',
  toolName: '1099 Vendor Threshold Review',
  analyzeErrorMessage: 'Failed to prepare 1099 candidates',
  exportFilename: payload => `form_1099_candidates_${payload.tax_year}.csv`,
})

export function useForm1099(): UseForm1099Return {
  const { status, result, error, analyze, exportCsv, reset } = useForm1099Analysis()
  return { status, result, error, analyze, exportCsv, reset }
}
