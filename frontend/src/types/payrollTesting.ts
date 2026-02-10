/**
 * Payroll & Employee Testing Types (Sprint 87)
 *
 * TypeScript interfaces matching the backend PayrollTestingResult.to_dict() shape.
 */

export type PayrollRiskTier = 'low' | 'elevated' | 'moderate' | 'high' | 'critical'
export type PayrollTestTier = 'structural' | 'statistical' | 'advanced'
export type PayrollSeverity = 'high' | 'medium' | 'low'

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

export interface FlaggedPayrollEntry {
  entry: PayrollEntryData
  test_name: string
  test_key: string
  test_tier: PayrollTestTier
  severity: PayrollSeverity
  issue: string
  confidence: number
  details: Record<string, unknown> | null
}

export interface PayrollTestResult {
  test_name: string
  test_key: string
  test_tier: PayrollTestTier
  entries_flagged: number
  total_entries: number
  flag_rate: number
  severity: PayrollSeverity
  description: string
  flagged_entries: FlaggedPayrollEntry[]
}

export interface PayrollCompositeScore {
  score: number
  risk_tier: PayrollRiskTier
  tests_run: number
  total_entries: number
  total_flagged: number
  flag_rate: number
  flags_by_severity: { high: number; medium: number; low: number }
  top_findings: Array<{
    employee: string
    test: string
    issue: string
    severity: string
    amount: number
  }>
}

export interface PayrollDataQuality {
  completeness_score: number
  field_fill_rates: Record<string, number>
  detected_issues: string[]
  total_rows: number
}

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

/** Risk tier color mapping for Oat & Obsidian theme — solid fills for light theme */
export const RISK_TIER_COLORS: Record<PayrollRiskTier, { bg: string; border: string; text: string }> = {
  low: { bg: 'bg-sage-50', border: 'border-sage-200', text: 'text-sage-600' },
  elevated: { bg: 'bg-oatmeal-100', border: 'border-oatmeal-300', text: 'text-oatmeal-600' },
  moderate: { bg: 'bg-clay-50', border: 'border-clay-200', text: 'text-content-primary' },
  high: { bg: 'bg-clay-100', border: 'border-clay-300', text: 'text-clay-600' },
  critical: { bg: 'bg-clay-200', border: 'border-clay-400', text: 'text-clay-700' },
}

export const RISK_TIER_LABELS: Record<PayrollRiskTier, string> = {
  low: 'Low Risk',
  elevated: 'Elevated',
  moderate: 'Moderate',
  high: 'High Risk',
  critical: 'Critical',
}

export const SEVERITY_COLORS: Record<PayrollSeverity, string> = {
  high: 'text-clay-600',
  medium: 'text-content-primary',
  low: 'text-content-secondary',
}
