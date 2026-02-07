/**
 * useAPTesting Hook (Sprint 75, refactored Sprint 82)
 *
 * Thin wrapper around useAuditUpload for AP Payment Testing.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { useMemo } from 'react'
import { useAuditUpload } from './useAuditUpload'
import type { APTestingResult } from '@/types/apTesting'

export interface UseAPTestingReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: APTestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

export function useAPTesting(): UseAPTestingReturn {
  const options = useMemo(() => ({
    endpoint: '/audit/ap-payments',
    toolName: 'AP tests',
    buildFormData: (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return fd
    },
    parseResult: (data: unknown) => data as APTestingResult,
  }), [])

  const { status, result, error, run, reset } = useAuditUpload<APTestingResult>(options)

  return { status, result, error, runTests: run as (file: File) => Promise<void>, reset }
}
