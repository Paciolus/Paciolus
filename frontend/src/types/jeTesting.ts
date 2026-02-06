/**
 * Journal Entry Testing Types (Sprint 66)
 *
 * TypeScript interfaces matching the backend JETestingResult.to_dict() shape.
 */

export type JERiskTier = 'low' | 'elevated' | 'moderate' | 'high' | 'critical'
export type JETestTier = 'structural' | 'statistical' | 'advanced'
export type JESeverity = 'high' | 'medium' | 'low'

export interface JournalEntryData {
  entry_id: string | null
  entry_date: string | null
  posting_date: string | null
  account: string
  description: string | null
  debit: number
  credit: number
  posted_by: string | null
  source: string | null
  reference: string | null
  currency: string | null
  row_number: number
}

export interface FlaggedJournalEntry {
  entry: JournalEntryData
  test_name: string
  test_key: string
  test_tier: JETestTier
  severity: JESeverity
  issue: string
  confidence: number
  details: Record<string, unknown> | null
}

export interface JETestResult {
  test_name: string
  test_key: string
  test_tier: JETestTier
  entries_flagged: number
  total_entries: number
  flag_rate: number
  severity: JESeverity
  description: string
  flagged_entries: FlaggedJournalEntry[]
}

export interface JECompositeScore {
  score: number
  risk_tier: JERiskTier
  tests_run: number
  total_entries: number
  total_flagged: number
  flag_rate: number
  flags_by_severity: { high: number; medium: number; low: number }
  top_findings: string[]
}

export interface GLDataQuality {
  completeness_score: number
  field_fill_rates: Record<string, number>
  detected_issues: string[]
  total_rows: number
}

export interface GLColumnDetection {
  date_column: string | null
  account_column: string | null
  debit_column: string | null
  credit_column: string | null
  amount_column: string | null
  entry_date_column: string | null
  posting_date_column: string | null
  description_column: string | null
  reference_column: string | null
  posted_by_column: string | null
  source_column: string | null
  currency_column: string | null
  entry_id_column: string | null
  has_dual_dates: boolean
  has_separate_debit_credit: boolean
  overall_confidence: number
  requires_mapping: boolean
  all_columns: string[]
  detection_notes: string[]
}

export interface MultiCurrencyWarning {
  currencies_found: string[]
  primary_currency: string | null
  entry_counts_by_currency: Record<string, number>
  warning_message: string
}

export interface BenfordResult {
  passed_prechecks: boolean
  precheck_message: string | null
  eligible_count: number
  total_count: number
  expected_distribution: Record<string, number>
  actual_distribution: Record<string, number>
  actual_counts: Record<string, number>
  deviation_by_digit: Record<string, number>
  mad: number
  chi_squared: number
  conformity_level: string
  most_deviated_digits: number[]
}

export interface JETestingResult {
  composite_score: JECompositeScore
  test_results: JETestResult[]
  data_quality: GLDataQuality
  multi_currency_warning: MultiCurrencyWarning | null
  column_detection: GLColumnDetection
  benford_result: BenfordResult | null
}

/** Risk tier color mapping for Oat & Obsidian theme */
export const RISK_TIER_COLORS: Record<JERiskTier, { bg: string; border: string; text: string }> = {
  low: { bg: 'bg-sage-500/10', border: 'border-sage-500/30', text: 'text-sage-400' },
  elevated: { bg: 'bg-oatmeal-500/10', border: 'border-oatmeal-500/30', text: 'text-oatmeal-400' },
  moderate: { bg: 'bg-clay-500/10', border: 'border-clay-500/20', text: 'text-oatmeal-300' },
  high: { bg: 'bg-clay-500/15', border: 'border-clay-500/40', text: 'text-clay-400' },
  critical: { bg: 'bg-clay-500/20', border: 'border-clay-500/60', text: 'text-clay-300' },
}

export const RISK_TIER_LABELS: Record<JERiskTier, string> = {
  low: 'Low Risk',
  elevated: 'Elevated',
  moderate: 'Moderate',
  high: 'High Risk',
  critical: 'Critical',
}

export const SEVERITY_COLORS: Record<JESeverity, string> = {
  high: 'text-clay-400',
  medium: 'text-oatmeal-300',
  low: 'text-oatmeal-500',
}
