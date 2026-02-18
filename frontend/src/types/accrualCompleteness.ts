/**
 * Accrual Completeness Estimator Types
 * Sprint 290: Phase XXXIX — Accrual Completeness Estimator
 */

export interface AccrualAccount {
  account_name: string
  balance: number
  matched_keyword: string
}

export interface AccrualCompletenessReport {
  accrual_accounts: AccrualAccount[]
  total_accrued_balance: number
  accrual_account_count: number
  monthly_run_rate: number | null
  accrual_to_run_rate_pct: number | null
  threshold_pct: number
  below_threshold: boolean
  prior_operating_expenses: number | null
  prior_available: boolean
  narrative: string
}
