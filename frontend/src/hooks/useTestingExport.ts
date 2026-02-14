/**
 * Shared Testing Export Hook — Sprint 90
 * Sprint 220: Migrated from lib/downloadBlob to apiDownload (CSRF, retry, timeout)
 *
 * Extracts the duplicated export logic from AP/Payroll/JE testing pages.
 * Encapsulates: auth token, fetch + blob download, error handling, loading state.
 */

import { useState, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { apiDownload, downloadBlob } from '@/utils'

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

  const handleExportMemo = useCallback(async (body: unknown) => {
    if (!token) return
    setExporting('pdf')
    try {
      const { blob, filename, ok } = await apiDownload(
        memoEndpoint,
        token,
        { method: 'POST', body: body as Record<string, unknown> },
      )
      if (ok && blob) {
        downloadBlob(blob, filename || fallbackMemoFilename)
      }
    } finally {
      setExporting(null)
    }
  }, [token, memoEndpoint, fallbackMemoFilename])

  const handleExportCSV = useCallback(async (body: unknown) => {
    if (!token) return
    setExporting('csv')
    try {
      const { blob, filename, ok } = await apiDownload(
        csvEndpoint,
        token,
        { method: 'POST', body: body as Record<string, unknown> },
      )
      if (ok && blob) {
        downloadBlob(blob, filename || fallbackCsvFilename)
      }
    } finally {
      setExporting(null)
    }
  }, [token, csvEndpoint, fallbackCsvFilename])

  return { exporting, handleExportMemo, handleExportCSV }
}
