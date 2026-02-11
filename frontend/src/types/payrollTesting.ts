/**
 * Payroll & Employee Testing Types (Sprint 87)
 *
 * TypeScript interfaces matching the backend PayrollTestingResult.to_dict() shape.
 */

import type {
  TestingRiskTier,
  TestingTestTier,
  TestingSeverity,
  BaseFlaggedEntry,
  BaseTestResult,
  BaseCompositeScore,
  BaseDataQuality,
} from './testingShared'
import {
  TESTING_RISK_TIER_COLORS,
  TESTING_RISK_TIER_LABELS,
  TESTING_SEVERITY_COLORS,
} from './testingShared'

// Re-export shared types as domain aliases (backward compatibility)
export type PayrollRiskTier = TestingRiskTier
export type PayrollTestTier = TestingTestTier
export type PayrollSeverity = TestingSeverity

export interface PayrollEntryData {
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

export interface PayrollDataQuality extends BaseDataQuality {}

export interface PayrollColumnDetection {
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
  overall_confidence: number
  requires_mapping: boolean
  all_columns: string[]
  detection_notes: string[]
}

export interface PayrollTestingResult {
  composite_score: PayrollCompositeScore
  test_results: PayrollTestResult[]
  data_quality: PayrollDataQuality
  column_detection: PayrollColumnDetection
  filename: string
}

// Re-export standardized color maps (backward compat)
export const RISK_TIER_COLORS = TESTING_RISK_TIER_COLORS
export const RISK_TIER_LABELS = TESTING_RISK_TIER_LABELS
export const SEVERITY_COLORS = TESTING_SEVERITY_COLORS
