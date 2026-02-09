/**
 * useFixedAssetTesting Hook (Sprint 116)
 *
 * Thin wrapper around useAuditUpload for Fixed Asset Testing.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { useMemo } from 'react'
import { useAuditUpload } from './useAuditUpload'
import type { FixedAssetTestingResult } from '@/types/fixedAssetTesting'

export interface UseFixedAssetTestingReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: FixedAssetTestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

export function useFixedAssetTesting(): UseFixedAssetTestingReturn {
  const options = useMemo(() => ({
    endpoint: '/audit/fixed-assets',
    toolName: 'Fixed asset tests',
    buildFormData: (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return fd
    },
    parseResult: (data: unknown) => data as FixedAssetTestingResult,
  }), [])

  const { status, result, error, run, reset } = useAuditUpload<FixedAssetTestingResult>(options)

  return { status, result, error, runTests: run as (file: File) => Promise<void>, reset }
}
