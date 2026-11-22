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
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import { useToast } from '@/contexts/ToastContext'
import { type MovementSummaryResponse } from '@/hooks'
import { deliverDownload } from '@/utils/deliverDownload'
import { withLinkedEngagement } from '@/utils/linkedEngagement'
import { apiDownload } from '@/utils'

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
  // Sprint 886 (OUT-18): the memo resolves the client's reporting framework from it.
  const engagementId = useOptionalEngagementContext()?.engagementId ?? null
  const toast = useToast()

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
          body: withLinkedEngagement({
            prior_label: comparison.prior_label,
            current_label: comparison.current_label,
            budget_label: comparison.budget_label || null,
            total_accounts: comparison.total_accounts,
            movements_by_type: comparison.movements_by_type,
            movements_by_significance: comparison.movements_by_significance,
            significant_movements: comparison.significant_movements,
            lead_sheet_summaries: strippedSummaries,
            dormant_account_count: comparison.dormant_accounts.length,
            // Sprint 886: the names the screen lists, not only their count.
            dormant_accounts: comparison.dormant_accounts,
            // Sprint 887: the summary states the thresholds applied.
            active_thresholds: comparison.active_thresholds ?? null,
            client_name: metadata.clientName || 'Not specified',
            period_tested: metadata.fiscalYearEnd || 'Not specified',
            prepared_by: metadata.practitioner || 'Not specified',
            reviewed_by: metadata.reviewer || 'Not specified',
          }, engagementId),
        })

        // Sprint 893: a failed export says so (the toast pipe the old comment waited for exists).
        deliverDownload(result, 'MultiPeriod_Memo.pdf', 'PDF memo', toast)
      } catch {
        toast.error('Export failed', 'Unable to generate PDF memo. Please try again.')
      } finally {
        setExporting(false)
      }
    },
    [token, engagementId, toast],
  )

  return { exporting, exportMemo }
}
