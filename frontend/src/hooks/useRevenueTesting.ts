/**
 * useRevenueTesting Hook (Sprint 106)
 *
 * Thin wrapper around useAuditUpload for Revenue Testing.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { useMemo } from 'react'
import { useAuditUpload } from './useAuditUpload'
import type { RevenueTestingResult } from '@/types/revenueTesting'

export interface UseRevenueTestingReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: RevenueTestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

export function useRevenueTesting(): UseRevenueTestingReturn {
  const options = useMemo(() => ({
    endpoint: '/audit/revenue-testing',
    toolName: 'Revenue tests',
    buildFormData: (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return fd
    },
    parseResult: (data: unknown) => data as RevenueTestingResult,
  }), [])

  const { status, result, error, run, reset } = useAuditUpload<RevenueTestingResult>(options)

  return { status, result, error, runTests: run as (file: File) => Promise<void>, reset }
}
