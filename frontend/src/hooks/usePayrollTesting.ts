/**
 * usePayrollTesting Hook (Sprint 87)
 *
 * Thin wrapper around useAuditUpload for Payroll & Employee Testing.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { useMemo } from 'react'
import { useAuditUpload } from './useAuditUpload'
import type { PayrollTestingResult } from '@/types/payrollTesting'

export interface UsePayrollTestingReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: PayrollTestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

export function usePayrollTesting(): UsePayrollTestingReturn {
  const options = useMemo(() => ({
    endpoint: '/audit/payroll-testing',
    toolName: 'payroll tests',
    buildFormData: (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return fd
    },
    parseResult: (data: unknown) => data as PayrollTestingResult,
  }), [])

  const { status, result, error, run, reset } = useAuditUpload<PayrollTestingResult>(options)

  return { status, result, error, runTests: run as (file: File) => Promise<void>, reset }
}
