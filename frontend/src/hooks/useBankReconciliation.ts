/**
 * useBankReconciliation Hook (Sprint 78, refactored Sprint 82)
 *
 * Thin wrapper around useAuditUpload for Bank Statement Reconciliation.
 * Zero-Storage: files processed on backend, results ephemeral.
 */

import { useMemo } from 'react'
import { useAuditUpload } from './useAuditUpload'
import type { BankRecResult } from '@/types/bankRec'

export interface UseBankReconciliationReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: BankRecResult | null
  error: string
  reconcile: (bankFile: File, ledgerFile: File) => Promise<void>
  reset: () => void
}

export function useBankReconciliation(): UseBankReconciliationReturn {
  const options = useMemo(() => ({
    endpoint: '/audit/bank-reconciliation',
    toolName: 'bank reconciliation',
    buildFormData: (bankFile: File, ledgerFile: File) => {
      const fd = new FormData()
      fd.append('bank_file', bankFile)
      fd.append('ledger_file', ledgerFile)
      return fd
    },
    parseResult: (data: unknown) => data as BankRecResult,
  }), [])

  const { status, result, error, run, reset } = useAuditUpload<BankRecResult>(options)

  return {
    status,
    result,
    error,
    reconcile: run as (bankFile: File, ledgerFile: File) => Promise<void>,
    reset,
  }
}
