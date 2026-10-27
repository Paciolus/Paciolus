'use client'

/**
 * Book-to-Tax hook — Sprint 689f.
 */

import { useCallback, useState } from 'react'
import type {
  BookToTaxRequest,
  BookToTaxResponse,
  StandardAdjustment,
  StandardAdjustmentsResponse,
} from '@/types/bookToTax'
import { apiGet } from '@/utils/apiClient'
import { createJsonAnalysisHook, type JsonAnalysisStatus } from './createJsonAnalysisHook'

export type BookToTaxStatus = JsonAnalysisStatus

export interface UseBookToTaxReturn {
  status: BookToTaxStatus
  result: BookToTaxResponse | null
  standardAdjustments: StandardAdjustment[]
  error: string
  analyze: (payload: BookToTaxRequest) => Promise<boolean>
  exportCsv: (payload: BookToTaxRequest) => Promise<boolean>
  loadStandardAdjustments: () => Promise<void>
  reset: () => void
}

const useBookToTaxAnalysis = createJsonAnalysisHook<BookToTaxRequest, BookToTaxResponse>({
  endpoint: '/audit/book-to-tax',
  exportEndpoint: '/audit/book-to-tax/export.csv',
  toolName: 'Book-to-Tax Reconciliation',
  analyzeErrorMessage: 'Failed to compute book-to-tax reconciliation',
  exportFilename: payload => `book_to_tax_${payload.tax_year}.csv`,
})

export function useBookToTax(): UseBookToTaxReturn {
  const { status, result, error, analyze, exportCsv, reset, token } = useBookToTaxAnalysis()
  const [standardAdjustments, setStandardAdjustments] = useState<StandardAdjustment[]>([])

  const loadStandardAdjustments = useCallback(async () => {
    const response = await apiGet<StandardAdjustmentsResponse>('/audit/book-to-tax/standard-adjustments', token)
    if (response.ok && response.data) {
      setStandardAdjustments(response.data.standard_adjustments)
    }
  }, [token])

  return { status, result, standardAdjustments, error, analyze, exportCsv, loadStandardAdjustments, reset }
}
