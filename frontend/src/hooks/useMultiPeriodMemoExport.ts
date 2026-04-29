/**
 * Multi-period memo PDF export hook (Sprint 750).
 *
 * Owns the memo PDF download workflow: assembles the export payload from a
 * `MovementSummaryResponse` + engagement metadata, calls `apiDownload`,
 * triggers the browser blob download. Tracks `exporting` state for button
 * disabling.
 */
'use client'

import { useCallback, useState } from 'react'
import { type MovementSummaryResponse } from '@/hooks'
import { apiDownload, downloadBlob } from '@/utils'

export interface MemoMetadata {
  clientName: string
  fiscalYearEnd: string
  practitioner: string
  reviewer: string
}

export interface UseMultiPeriodMemoExportReturn {
  exporting: boolean
  exportMemo: (
    comparison: MovementSummaryResponse,
    metadata: MemoMetadata,
  ) => Promise<void>
}

export function useMultiPeriodMemoExport(token: string | null): UseMultiPeriodMemoExportReturn {
  const [exporting, setExporting] = useState(false)

  const exportMemo = useCallback(
    async (comparison: MovementSummaryResponse, metadata: MemoMetadata) => {
      if (!token) return
      setExporting(true)
      try {
        const strippedSummaries = comparison.lead_sheet_summaries.map(ls => ({
          lead_sheet: ls.lead_sheet,
          lead_sheet_name: ls.lead_sheet_name,
          account_count: ls.account_count,
          prior_total: ls.prior_total,
          current_total: ls.current_total,
          net_change: ls.net_change,
        }))

        const result = await apiDownload('/export/multi-period-memo', token, {
          method: 'POST',
          body: {
            prior_label: comparison.prior_label,
            current_label: comparison.current_label,
            budget_label: comparison.budget_label || null,
            total_accounts: comparison.total_accounts,
            movements_by_type: comparison.movements_by_type,
            movements_by_significance: comparison.movements_by_significance,
            significant_movements: comparison.significant_movements,
            lead_sheet_summaries: strippedSummaries,
            dormant_account_count: comparison.dormant_accounts.length,
            client_name: metadata.clientName || 'Not specified',
            period_tested: metadata.fiscalYearEnd || 'Not specified',
            prepared_by: metadata.practitioner || 'Not specified',
            reviewed_by: metadata.reviewer || 'Not specified',
          },
        })

        if (result.ok && result.blob) {
          downloadBlob(result.blob, result.filename || 'MultiPeriod_Memo.pdf')
        }
      } catch {
        // Silent failure — caller's button state resets via the finally block,
        // and the user can retry. Surfacing transport errors here would
        // require a toast pipe; defer until a downstream sprint introduces one.
      } finally {
        setExporting(false)
      }
    },
    [token],
  )

  return { exporting, exportMemo }
}
