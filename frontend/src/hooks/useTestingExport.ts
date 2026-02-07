/**
 * Shared Testing Export Hook — Sprint 90
 *
 * Extracts the duplicated export logic from AP/Payroll/JE testing pages.
 * Encapsulates: auth token, fetch + blob download, error handling, loading state.
 */

import { useState, useCallback } from 'react'
import { useAuth } from '@/context/AuthContext'
import { downloadBlob } from '@/lib/downloadBlob'

export type ExportType = 'pdf' | 'csv' | null

export interface UseTestingExportReturn {
  exporting: ExportType
  handleExportMemo: (body: unknown) => Promise<void>
  handleExportCSV: (body: unknown) => Promise<void>
}

export function useTestingExport(
  memoEndpoint: string,
  csvEndpoint: string,
  fallbackMemoFilename: string = 'testing_memo.pdf',
  fallbackCsvFilename: string = 'flagged_entries.csv',
): UseTestingExportReturn {
  const { token } = useAuth()
  const [exporting, setExporting] = useState<ExportType>(null)
  const API_URL = process.env.NEXT_PUBLIC_API_URL

  const handleExportMemo = useCallback(async (body: unknown) => {
    if (!token) return
    setExporting('pdf')
    try {
      await downloadBlob({
        url: `${API_URL}${memoEndpoint}`,
        body,
        token,
        fallbackFilename: fallbackMemoFilename,
      })
    } finally {
      setExporting(null)
    }
  }, [token, API_URL, memoEndpoint, fallbackMemoFilename])

  const handleExportCSV = useCallback(async (body: unknown) => {
    if (!token) return
    setExporting('csv')
    try {
      await downloadBlob({
        url: `${API_URL}${csvEndpoint}`,
        body,
        token,
        fallbackFilename: fallbackCsvFilename,
      })
    } finally {
      setExporting(null)
    }
  }, [token, API_URL, csvEndpoint, fallbackCsvFilename])

  return { exporting, handleExportMemo, handleExportCSV }
}
