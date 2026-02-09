/**
 * useARAging Hook (Sprint 109)
 *
 * Dual-file upload wrapper around useAuditUpload for AR Aging Analysis.
 * TB file required, sub-ledger file optional.
 * Zero-Storage: files processed on backend, results ephemeral.
 */

import { useMemo } from 'react'
import { useAuditUpload } from './useAuditUpload'
import type { ARAgingResult } from '@/types/arAging'

export interface UseARAgingReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: ARAgingResult | null
  error: string
  runTests: (tbFile: File, slFile?: File) => Promise<void>
  reset: () => void
}

export function useARAging(): UseARAgingReturn {
  const options = useMemo(() => ({
    endpoint: '/audit/ar-aging',
    toolName: 'AR aging analysis',
    buildFormData: (tbFile: File, slFile?: File) => {
      const fd = new FormData()
      fd.append('tb_file', tbFile)
      if (slFile) {
        fd.append('subledger_file', slFile)
      }
      return fd
    },
    parseResult: (data: unknown) => data as ARAgingResult,
  }), [])

  const { status, result, error, run, reset } = useAuditUpload<ARAgingResult>(options)

  return {
    status,
    result,
    error,
    runTests: run as (tbFile: File, slFile?: File) => Promise<void>,
    reset,
  }
}
