/**
 * useMultiPeriodComparison Hook - Sprint 62
 *
 * Manages the dual-file upload and comparison flow for the
 * Multi-Period Comparison tool.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Both files processed in-memory only
 * - Comparison results are ephemeral (React state only)
 */

import { useState, useCallback } from 'react'
import { apiPost } from '@/utils'

// =============================================================================
// TYPES
// =============================================================================

export interface AccountMovement {
  account_name: string
  account_type: string
  prior_balance: number
  current_balance: number
  change_amount: number
  change_percent: number | null
  movement_type: string
  significance: string
  lead_sheet: string
  lead_sheet_name: string
  lead_sheet_category: string
  is_dormant: boolean
}

export interface LeadSheetMovementSummary {
  lead_sheet: string
  lead_sheet_name: string
  lead_sheet_category: string
  prior_total: number
  current_total: number
  net_change: number
  change_percent: number | null
  account_count: number
  movements: AccountMovement[]
}

export interface MovementSummaryResponse {
  prior_label: string
  current_label: string
  total_accounts: number
  movements_by_type: Record<string, number>
  movements_by_significance: Record<string, number>
  all_movements: AccountMovement[]
  lead_sheet_summaries: LeadSheetMovementSummary[]
  significant_movements: AccountMovement[]
  new_accounts: string[]
  closed_accounts: string[]
  dormant_accounts: string[]
  prior_total_debits: number
  prior_total_credits: number
  current_total_debits: number
  current_total_credits: number
}

export interface AuditResultForComparison {
  lead_sheet_grouping?: {
    summaries: Array<{
      accounts: Array<{
        account: string
        debit: number
        credit: number
        type: string
      }>
    }>
  }
}

export interface UseMultiPeriodComparisonReturn {
  comparison: MovementSummaryResponse | null
  isComparing: boolean
  error: string | null
  compareResults: (
    priorResult: AuditResultForComparison,
    currentResult: AuditResultForComparison,
    priorLabel: string,
    currentLabel: string,
    materialityThreshold: number,
    token: string | null,
  ) => Promise<boolean>
  clear: () => void
}

// =============================================================================
// HOOK
// =============================================================================

export function useMultiPeriodComparison(): UseMultiPeriodComparisonReturn {
  const [comparison, setComparison] = useState<MovementSummaryResponse | null>(null)
  const [isComparing, setIsComparing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const extractAccounts = useCallback((result: AuditResultForComparison) => {
    const accounts: Array<{ account: string; debit: number; credit: number; type: string }> = []
    if (result.lead_sheet_grouping?.summaries) {
      for (const summary of result.lead_sheet_grouping.summaries) {
        if (summary.accounts) {
          for (const acct of summary.accounts) {
            accounts.push({
              account: acct.account,
              debit: acct.debit || 0,
              credit: acct.credit || 0,
              type: acct.type || 'unknown',
            })
          }
        }
      }
    }
    return accounts
  }, [])

  const compareResults = useCallback(async (
    priorResult: AuditResultForComparison,
    currentResult: AuditResultForComparison,
    priorLabel: string,
    currentLabel: string,
    materialityThreshold: number,
    token: string | null,
  ): Promise<boolean> => {
    setIsComparing(true)
    setError(null)

    try {
      const priorAccounts = extractAccounts(priorResult)
      const currentAccounts = extractAccounts(currentResult)

      if (priorAccounts.length === 0 || currentAccounts.length === 0) {
        setError('Could not extract account data from one or both audit results.')
        setIsComparing(false)
        return false
      }

      const { data, error: apiError, ok } = await apiPost<MovementSummaryResponse>(
        '/audit/compare-periods',
        token,
        {
          prior_accounts: priorAccounts,
          current_accounts: currentAccounts,
          prior_label: priorLabel,
          current_label: currentLabel,
          materiality_threshold: materialityThreshold,
        } as unknown as Record<string, unknown>,
      )

      if (!ok || !data) {
        setError(apiError || 'Failed to compare periods.')
        setIsComparing(false)
        return false
      }

      setComparison(data)
      setIsComparing(false)
      return true
    } catch (err) {
      setError('An unexpected error occurred during comparison.')
      setIsComparing(false)
      return false
    }
  }, [extractAccounts])

  const clear = useCallback(() => {
    setComparison(null)
    setError(null)
  }, [])

  return {
    comparison,
    isComparing,
    error,
    compareResults,
    clear,
  }
}
