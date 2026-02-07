/**
 * useJETesting Hook (Sprint 66, refactored Sprint 82)
 *
 * Thin wrapper around useAuditUpload for Journal Entry Testing.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { useMemo } from 'react'
import { useAuditUpload } from './useAuditUpload'
import type { JETestingResult } from '@/types/jeTesting'

export interface UseJETestingReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: JETestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

export function useJETesting(): UseJETestingReturn {
  const options = useMemo(() => ({
    endpoint: '/audit/journal-entries',
    toolName: 'JE tests',
    buildFormData: (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return fd
    },
    parseResult: (data: unknown) => data as JETestingResult,
  }), [])

  const { status, result, error, run, reset } = useAuditUpload<JETestingResult>(options)

  return { status, result, error, runTests: run as (file: File) => Promise<void>, reset }
}
