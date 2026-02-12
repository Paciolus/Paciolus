/**
 * usePayrollTesting Hook (Sprint 87, factory Sprint 161)
 *
 * Thin wrapper around createTestingHook for Payroll & Employee Testing.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { createTestingHook } from './createTestingHook'
import type { PayrollTestingResult } from '@/types/payrollTesting'

export interface UsePayrollTestingReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: PayrollTestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

const useBase = createTestingHook<PayrollTestingResult>({ endpoint: '/audit/payroll-testing', toolName: 'payroll tests' })

export function usePayrollTesting(): UsePayrollTestingReturn {
  const { run, ...rest } = useBase()
  return { ...rest, runTests: run as (file: File) => Promise<void> }
}
