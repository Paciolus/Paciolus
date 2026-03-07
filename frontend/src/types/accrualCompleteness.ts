/**
 * Accrual Completeness Estimator Types
 */

export interface AccrualAccount {
  account_name: string
  balance: number
  matched_keyword: string
  classification: string
}

export interface ReasonablenessResult {
  account_name: string
  recorded_balance: number
  annual_driver: number | null
  driver_source: string
  months_to_accrue: number
  expected_balance: number | null
  variance: number | null
  variance_pct: number | null
  status: string
}

export interface DeferredRevenueAnalysis {
  deferred_balance: number
  total_revenue: number | null
  deferred_pct_of_revenue: number | null
}

export interface AccrualFinding {
  area: string
  finding: string
  risk: string
  action_required: string
}

export interface AccrualProcedure {
  priority: string
  area: string
  procedure: string
}

export interface ExpectedAccrualCheck {
  expected_name: string
  detected: boolean
  balance: number | null
  risk_if_absent: string
  basis: string
  recommended_action: string
}

export interface AccrualCompletenessReport {
  accrual_accounts: AccrualAccount[]
  total_accrued_balance: number
  accrual_account_count: number
  deferred_revenue_accounts: AccrualAccount[]
  total_deferred_revenue: number
  monthly_run_rate: number | null
  accrual_to_run_rate_pct: number | null
  threshold_pct: number
  meets_threshold: boolean
  below_threshold: boolean
  prior_operating_expenses: number | null
  prior_available: boolean
  narrative: string
  reasonableness_results: ReasonablenessResult[]
  expected_accrual_checklist: ExpectedAccrualCheck[]
  deferred_revenue_analysis: DeferredRevenueAnalysis | null
  findings: AccrualFinding[]
  suggested_procedures: AccrualProcedure[]
}
