/**
 * Shared Testing Export Hook — Sprint 90
 * Sprint 220: Migrated from lib/downloadBlob to apiDownload (CSRF, retry, timeout)
 *
 * Extracts the duplicated export logic from AP/Payroll/JE testing pages.
 * Encapsulates: auth token, fetch + blob download, error handling, loading state.
 */

import { useState, useCallback, useRef } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import { useToast } from '@/contexts/ToastContext'
import { useSonification } from '@/hooks/useSonification'
import { withLinkedEngagement } from '@/utils/linkedEngagement'
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

/** Message for an export that came back without a file (Sprint 890). */
function exportFailureMessage(ok: boolean, error: string | undefined, what: string): string {
  if (!ok) return error || `Unable to generate ${what}. Please try again.`
  return `The server returned no file for the ${what}. Please try again.`
}

export function useTestingExport(
  memoEndpoint: string,
  csvEndpoint: string,
  fallbackMemoFilename: string = 'testing_memo.pdf',
  fallbackCsvFilename: string = 'flagged_entries.csv',
): UseTestingExportReturn {
  const { token } = useAuthSession()
  // Sprint 886 (OUT-18): the memo resolves the client's reporting framework from it.
  const engagementId = useOptionalEngagementContext()?.engagementId ?? null
  const toast = useToast()
  const { playTone } = useSonification()
  const [exporting, setExporting] = useState<ExportType>(null)
  const [lastExportSuccess, setLastExportSuccess] = useState<ExportType>(null)
  const clearTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const markComplete = useCallback((type: ExportType) => {
    setLastExportSuccess(type)
    playTone('exportDone')
    if (clearTimerRef.current) clearTimeout(clearTimerRef.current)
    clearTimerRef.current = setTimeout(() => {
      setLastExportSuccess(null)
      clearTimerRef.current = null
    }, 1500)
  }, [playTone])

  const handleExportMemo = useCallback(async (body: unknown) => {
    if (!token) return
    setExporting('pdf')
    try {
      const { blob, filename, ok, error } = await apiDownload(
        memoEndpoint,
        token,
        { method: 'POST', body: withLinkedEngagement(body as Record<string, unknown>, engagementId) },
      )
      if (ok && blob) {
        downloadBlob(blob, filename || fallbackMemoFilename)
        markComplete('pdf')
        toast.success('PDF memo exported', filename || fallbackMemoFilename)
      } else {
        // Sprint 890 (15A): apiDownload resolves ok: false on failure; it does not throw.
        toast.error('Export failed', exportFailureMessage(ok, error, 'PDF memo'))
      }
    } catch {
      toast.error('Export failed', 'Unable to generate PDF memo. Please try again.')
    } finally {
      setExporting(null)
    }
  }, [token, memoEndpoint, fallbackMemoFilename, markComplete, toast, engagementId])

  const handleExportCSV = useCallback(async (body: unknown) => {
    if (!token) return
    setExporting('csv')
    try {
      const { blob, filename, ok, error } = await apiDownload(
        csvEndpoint,
        token,
        { method: 'POST', body: body as Record<string, unknown> },
      )
      if (ok && blob) {
        downloadBlob(blob, filename || fallbackCsvFilename)
        markComplete('csv')
        toast.success('CSV exported', filename || fallbackCsvFilename)
      } else {
        toast.error('Export failed', exportFailureMessage(ok, error, 'CSV export'))
      }
    } catch {
      toast.error('Export failed', 'Unable to generate CSV export. Please try again.')
    } finally {
      setExporting(null)
    }
  }, [token, csvEndpoint, fallbackCsvFilename, markComplete, toast])

  return { exporting, lastExportSuccess, handleExportMemo, handleExportCSV }
}
