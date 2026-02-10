/**
 * AP Payment Testing Types (Sprint 75)
 *
 * TypeScript interfaces matching the backend APTestingResult.to_dict() shape.
 */

export type APRiskTier = 'low' | 'elevated' | 'moderate' | 'high' | 'critical'
export type APTestTier = 'structural' | 'statistical' | 'advanced'
export type APSeverity = 'high' | 'medium' | 'low'

export interface APPaymentData {
  invoice_number: string | null
  invoice_date: string | null
  payment_date: string | null
  vendor_name: string
  vendor_id: string | null
  amount: number
  check_number: string | null
  description: string | null
  gl_account: string | null
  payment_method: string | null
  row_number: number
}

export interface FlaggedAPPayment {
  entry: APPaymentData
  test_name: string
  test_key: string
  test_tier: APTestTier
  severity: APSeverity
  issue: string
  confidence: number
  details: Record<string, unknown> | null
}

export interface APTestResult {
  test_name: string
  test_key: string
  test_tier: APTestTier
  entries_flagged: number
  total_entries: number
  flag_rate: number
  severity: APSeverity
  description: string
  flagged_entries: FlaggedAPPayment[]
}

export interface APCompositeScore {
  score: number
  risk_tier: APRiskTier
  tests_run: number
  total_entries: number
  total_flagged: number
  flag_rate: number
  flags_by_severity: { high: number; medium: number; low: number }
  top_findings: string[]
}

export interface APDataQuality {
  completeness_score: number
  field_fill_rates: Record<string, number>
  detected_issues: string[]
  total_rows: number
}

export interface APColumnDetection {
  vendor_name_column: string | null
  amount_column: string | null
  payment_date_column: string | null
  invoice_number_column: string | null
  invoice_date_column: string | null
  vendor_id_column: string | null
  check_number_column: string | null
  description_column: string | null
  gl_account_column: string | null
  payment_method_column: string | null
  has_dual_dates: boolean
  has_check_numbers: boolean
  overall_confidence: number
  requires_mapping: boolean
  all_columns: string[]
  detection_notes: string[]
}

export interface APTestingResult {
  composite_score: APCompositeScore
  test_results: APTestResult[]
  data_quality: APDataQuality
  column_detection: APColumnDetection
}

/** Risk tier color mapping for Oat & Obsidian theme (light-mode semantic tokens) */
export const RISK_TIER_COLORS: Record<APRiskTier, { bg: string; border: string; text: string }> = {
  low: { bg: 'bg-sage-50', border: 'border-sage-200', text: 'text-sage-600' },
  elevated: { bg: 'bg-oatmeal-100', border: 'border-oatmeal-300', text: 'text-content-secondary' },
  moderate: { bg: 'bg-clay-50', border: 'border-clay-200', text: 'text-content-primary' },
  high: { bg: 'bg-clay-100', border: 'border-clay-300', text: 'text-clay-600' },
  critical: { bg: 'bg-clay-200', border: 'border-clay-400', text: 'text-clay-700' },
}

export const RISK_TIER_LABELS: Record<APRiskTier, string> = {
  low: 'Low Risk',
  elevated: 'Elevated',
  moderate: 'Moderate',
  high: 'High Risk',
  critical: 'Critical',
}

export const SEVERITY_COLORS: Record<APSeverity, string> = {
  high: 'text-clay-600',
  medium: 'text-content-primary',
  low: 'text-content-secondary',
}
