/**
 * Shared Testing Export Hook — Sprint 90
 * Sprint 220: Migrated from lib/downloadBlob to apiDownload (CSRF, retry, timeout)
 *
 * Extracts the duplicated export logic from AP/Payroll/JE testing pages.
 * Encapsulates: auth token, fetch + blob download, error handling, loading state.
 */

import { useState, useCallback, useRef } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { apiDownload, downloadBlob } from '@/utils'

export type ExportType = 'pdf' | 'csv' | null

/** Export resolution state: idle → exporting → complete (1.5s) → idle */
export type ExportPhase = 'idle' | 'exporting' | 'complete'

export interface UseTestingExportReturn {
  exporting: ExportType
  /** Tracks which export just completed (auto-clears after 1.5s) */
  lastExportSuccess: ExportType
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
  const [lastExportSuccess, setLastExportSuccess] = useState<ExportType>(null)
  const clearTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const markComplete = useCallback((type: ExportType) => {
    setLastExportSuccess(type)
    if (clearTimerRef.current) clearTimeout(clearTimerRef.current)
    clearTimerRef.current = setTimeout(() => {
      setLastExportSuccess(null)
      clearTimerRef.current = null
    }, 1500)
  }, [])

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
        markComplete('pdf')
      }
    } finally {
      setExporting(null)
    }
  }, [token, memoEndpoint, fallbackMemoFilename, markComplete])

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
        markComplete('csv')
      }
    } finally {
      setExporting(null)
    }
  }, [token, csvEndpoint, fallbackCsvFilename, markComplete])

  return { exporting, lastExportSuccess, handleExportMemo, handleExportCSV }
}
