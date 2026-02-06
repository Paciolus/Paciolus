/**
 * useMultiPeriodComparison Hook - Sprint 62 / Sprint 63
 *
 * Manages the dual-file or three-file upload and comparison flow for the
 * Multi-Period Comparison tool.
 *
 * Sprint 63: Three-way comparison (Prior + Current + Budget/Forecast)
 * and CSV export support.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - All files processed in-memory only
 * - Comparison results are ephemeral (React state only)
 */

import { useState, useCallback } from 'react'
import { apiPost } from '@/utils'

const API_URL = process.env.NEXT_PUBLIC_API_URL

// =============================================================================
// TYPES
// =============================================================================

export interface BudgetVariance {
  budget_balance: number
  variance_amount: number
  variance_percent: number | null
  variance_significance: string
}

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
  budget_variance?: BudgetVariance | null
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
  // Three-way fields (Sprint 63)
  budget_total?: number | null
  budget_variance?: number | null
  budget_variance_percent?: number | null
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
  // Three-way fields (Sprint 63)
  budget_label?: string
  budget_total_debits?: number
  budget_total_credits?: number
  budget_variances_by_significance?: Record<string, number>
  accounts_over_budget?: number
  accounts_under_budget?: number
  accounts_on_budget?: number
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
  isExporting: boolean
  error: string | null
  compareResults: (
    priorResult: AuditResultForComparison,
    currentResult: AuditResultForComparison,
    priorLabel: string,
    currentLabel: string,
    materialityThreshold: number,
    token: string | null,
    budgetResult?: AuditResultForComparison | null,
    budgetLabel?: string,
  ) => Promise<boolean>
  exportCsv: (
    priorResult: AuditResultForComparison,
    currentResult: AuditResultForComparison,
    priorLabel: string,
    currentLabel: string,
    materialityThreshold: number,
    token: string | null,
    budgetResult?: AuditResultForComparison | null,
    budgetLabel?: string,
  ) => Promise<void>
  clear: () => void
}

// =============================================================================
// HOOK
// =============================================================================

export function useMultiPeriodComparison(): UseMultiPeriodComparisonReturn {
  const [comparison, setComparison] = useState<MovementSummaryResponse | null>(null)
  const [isComparing, setIsComparing] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
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
    budgetResult?: AuditResultForComparison | null,
    budgetLabel?: string,
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

      const hasBudget = budgetResult != null
      const budgetAccounts = hasBudget ? extractAccounts(budgetResult) : null

      if (hasBudget && budgetAccounts && budgetAccounts.length === 0) {
        setError('Could not extract account data from the budget file.')
        setIsComparing(false)
        return false
      }

      // Use three-way endpoint if budget exists, otherwise two-way
      const endpoint = hasBudget ? '/audit/compare-three-way' : '/audit/compare-periods'
      const payload: Record<string, unknown> = {
        prior_accounts: priorAccounts,
        current_accounts: currentAccounts,
        prior_label: priorLabel,
        current_label: currentLabel,
        materiality_threshold: materialityThreshold,
      }

      if (hasBudget && budgetAccounts) {
        payload.budget_accounts = budgetAccounts
        payload.budget_label = budgetLabel || 'Budget'
      }

      const { data, error: apiError, ok } = await apiPost<MovementSummaryResponse>(
        endpoint,
        token,
        payload,
      )

      if (!ok || !data) {
        setError(apiError || 'Failed to compare periods.')
        setIsComparing(false)
        return false
      }

      setComparison(data)
      setIsComparing(false)
      return true
    } catch {
      setError('An unexpected error occurred during comparison.')
      setIsComparing(false)
      return false
    }
  }, [extractAccounts])

  const exportCsv = useCallback(async (
    priorResult: AuditResultForComparison,
    currentResult: AuditResultForComparison,
    priorLabel: string,
    currentLabel: string,
    materialityThreshold: number,
    token: string | null,
    budgetResult?: AuditResultForComparison | null,
    budgetLabel?: string,
  ) => {
    setIsExporting(true)
    try {
      const priorAccounts = extractAccounts(priorResult)
      const currentAccounts = extractAccounts(currentResult)

      const payload: Record<string, unknown> = {
        prior_accounts: priorAccounts,
        current_accounts: currentAccounts,
        prior_label: priorLabel,
        current_label: currentLabel,
        materiality_threshold: materialityThreshold,
      }

      if (budgetResult) {
        payload.budget_accounts = extractAccounts(budgetResult)
        payload.budget_label = budgetLabel || 'Budget'
      }

      const response = await fetch(`${API_URL}/export/csv/movements`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        setError('Failed to export CSV.')
        return
      }

      // Download the CSV blob
      const blob = await response.blob()
      const disposition = response.headers.get('Content-Disposition') || ''
      const filenameMatch = disposition.match(/filename="?([^"]+)"?/)
      const filename = filenameMatch ? filenameMatch[1] : 'Movement_Comparison.csv'

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      setError('Failed to download CSV export.')
    } finally {
      setIsExporting(false)
    }
  }, [extractAccounts])

  const clear = useCallback(() => {
    setComparison(null)
    setError(null)
  }, [])

  return {
    comparison,
    isComparing,
    isExporting,
    error,
    compareResults,
    exportCsv,
    clear,
  }
}
