/**
 * useBankReconciliation Hook (Sprint 78, refactored Sprint 82, factory Sprint 161)
 *
 * Bank Statement Reconciliation upload hook. Sprint 839: sends per-run
 * materiality and performance materiality when the user enters them; an
 * empty field sends nothing and the Paciolus default applies (the result's
 * `active_thresholds` says which).
 * Zero-Storage: files processed on backend, results ephemeral.
 */

import { useMemo } from 'react'
import type { BankRecResult } from '@/types/bankRec'
import type { UploadStatus } from '@/types/shared'
import { useAuditUpload } from './useAuditUpload'

export interface UseBankReconciliationReturn {
  status: UploadStatus
  result: BankRecResult | null
  error: string
  reconcile: (bankFile: File, ledgerFile: File) => Promise<void>
  reset: () => void
}

/** Per-run thresholds in dollars; undefined = not set for this run. */
export interface BankRecRunThresholds {
  materiality?: number
  performanceMateriality?: number
}

export function buildBankRecFormData(
  bankFile: File | undefined,
  ledgerFile: File | undefined,
  thresholds?: BankRecRunThresholds,
): FormData {
  const fd = new FormData()
  if (bankFile) fd.append('bank_file', bankFile)
  if (ledgerFile) fd.append('ledger_file', ledgerFile)
  if (thresholds?.materiality !== undefined) fd.append('materiality', String(thresholds.materiality))
  if (thresholds?.performanceMateriality !== undefined) {
    fd.append('performance_materiality', String(thresholds.performanceMateriality))
  }
  return fd
}

export function useBankReconciliation(thresholds?: BankRecRunThresholds): UseBankReconciliationReturn {
  const materiality = thresholds?.materiality
  const performanceMateriality = thresholds?.performanceMateriality
  const options = useMemo(() => ({
    endpoint: '/audit/bank-reconciliation',
    toolName: 'bank reconciliation',
    buildFormData: (...files: File[]) => buildBankRecFormData(files[0], files[1], { materiality, performanceMateriality }),
    parseResult: (data: unknown) => data as BankRecResult,
  }), [materiality, performanceMateriality])

  const { run, ...rest } = useAuditUpload<BankRecResult>(options)
  return { ...rest, reconcile: run as (bankFile: File, ledgerFile: File) => Promise<void> }
}
