/**
 * useBankReconciliation Hook (Sprint 78, refactored Sprint 82, factory Sprint 161)
 *
 * Wrapper around createTestingHook for Bank Statement Reconciliation.
 * Zero-Storage: files processed on backend, results ephemeral.
 */

import { createTestingHook } from './createTestingHook'
import type { BankRecResult } from '@/types/bankRec'

export interface UseBankReconciliationReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: BankRecResult | null
  error: string
  reconcile: (bankFile: File, ledgerFile: File) => Promise<void>
  reset: () => void
}

const useBase = createTestingHook<BankRecResult>({
  endpoint: '/audit/bank-reconciliation',
  toolName: 'bank reconciliation',
  buildFormData: (bankFile: File, ledgerFile: File) => {
    const fd = new FormData()
    fd.append('bank_file', bankFile)
    fd.append('ledger_file', ledgerFile)
    return fd
  },
})

export function useBankReconciliation(): UseBankReconciliationReturn {
  const { run, ...rest } = useBase()
  return { ...rest, reconcile: run as (bankFile: File, ledgerFile: File) => Promise<void> }
}
