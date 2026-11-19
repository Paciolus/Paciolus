/**
 * Payroll & Employee Testing Types (Sprint 87)
 *
 * TypeScript interfaces matching the backend PayrollTestingResult.to_dict() shape.
 */

import {
  TESTING_RISK_TIER_COLORS,
  TESTING_RISK_TIER_LABELS,
  TESTING_SEVERITY_COLORS,
} from './testingShared'
import type {
  SavedSettingsDisclosure,
  TestingRiskTier,
  TestingTestTier,
  TestingSeverity,
  BaseFlaggedEntry,
  BaseTestResult,
  BaseCompositeScore,
  RowDataQuality,
  BaseColumnDetection,
} from './testingShared'

// Re-export shared types as domain aliases (backward compatibility)
export type PayrollRiskTier = TestingRiskTier
export type PayrollTestTier = TestingTestTier
export type PayrollSeverity = TestingSeverity

export type PayrollEntryData = {
  employee_id: string
  employee_name: string
  department: string
  pay_date: string | null
  gross_pay: number
  net_pay: number
  deductions: number
  check_number: string
  pay_type: string
  hours: number
  rate: number
  term_date: string | null
  bank_account: string
  address: string
  tax_id: string
  row_index: number
}

export interface FlaggedPayrollEntry extends BaseFlaggedEntry<PayrollEntryData> {}

export interface PayrollTestResult extends BaseTestResult<FlaggedPayrollEntry> {}

export interface PayrollTopFinding {
  employee: string
  test: string
  issue: string
  severity: string
  amount: number
}

export interface PayrollCompositeScore extends BaseCompositeScore<PayrollTopFinding> {
  total_entries: number
  flag_rate: number
}

export interface PayrollDataQuality extends RowDataQuality {}

export interface PayrollColumnDetection extends BaseColumnDetection {
  employee_name_column: string | null
  gross_pay_column: string | null
  pay_date_column: string | null
  employee_id_column: string | null
  department_column: string | null
  net_pay_column: string | null
  deductions_column: string | null
  check_number_column: string | null
  pay_type_column: string | null
  hours_column: string | null
  rate_column: string | null
  term_date_column: string | null
  bank_account_column: string | null
  address_column: string | null
  tax_id_column: string | null
  has_check_numbers: boolean
  has_term_dates: boolean
  has_bank_accounts: boolean
  has_addresses: boolean
  has_tax_ids: boolean
  requires_mapping: boolean
}

export interface PayrollTestingResult extends SavedSettingsDisclosure {
  composite_score: PayrollCompositeScore
  test_results: PayrollTestResult[]
  data_quality: PayrollDataQuality
  column_detection: PayrollColumnDetection
  filename: string
  /** Sprint 886 (OUT-12): supplemental schedules the memo prints. */
  payroll_register_total?: number | null
  department_summary?: Array<{ department: string; employee_count: number; total_gross_pay: number; pct_of_total: number }> | null
  headcount_rollforward?: {
    period_start: string
    period_end: string
    beginning_headcount: number
    new_hires: number
    terminations: number
    computed_ending: number
    final_period_headcount: number
    variance: number
  } | null
}

// Re-export standardized color maps (backward compat)
export const RISK_TIER_COLORS = TESTING_RISK_TIER_COLORS
export const RISK_TIER_LABELS = TESTING_RISK_TIER_LABELS
export const SEVERITY_COLORS = TESTING_SEVERITY_COLORS
