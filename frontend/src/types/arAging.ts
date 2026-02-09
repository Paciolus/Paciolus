/**
 * AR Aging Types (Sprint 109)
 *
 * TypeScript interfaces matching the backend ARAgingResult.to_dict() shape.
 * ISA 500/540: Audit Evidence + Auditing Accounting Estimates.
 * Dual-input: TB (required) + optional AR sub-ledger.
 */

export type ARRiskTier = 'low' | 'elevated' | 'moderate' | 'high' | 'critical'
export type ARTestTier = 'structural' | 'statistical' | 'advanced'
export type ARSeverity = 'high' | 'medium' | 'low'

export interface AREntryData {
  account_name: string | null
  account_number: string | null
  customer_name: string | null
  invoice_number: string | null
  date: string | null
  amount: number
  aging_days: number | null
  row_number: number
  entry_source: 'tb' | 'subledger'
}

export interface FlaggedAREntry {
  entry: AREntryData
  test_name: string
  test_key: string
  test_tier: ARTestTier
  severity: ARSeverity
  issue: string
  confidence: number
  details: Record<string, unknown> | null
}

export interface ARTestResult {
  test_name: string
  test_key: string
  test_tier: ARTestTier
  entries_flagged: number
  total_entries: number
  flag_rate: number
  severity: ARSeverity
  description: string
  flagged_entries: FlaggedAREntry[]
  skipped: boolean
  skip_reason: string | null
}

export interface ARCompositeScore {
  score: number
  risk_tier: ARRiskTier
  tests_run: number
  tests_skipped: number
  total_flagged: number
  flags_by_severity: { high: number; medium: number; low: number }
  top_findings: string[]
  has_subledger: boolean
}

export interface ARDataQuality {
  completeness_score: number
  field_fill_rates: Record<string, number>
  detected_issues: string[]
  total_tb_accounts: number
  total_subledger_entries: number
  has_subledger: boolean
}

export interface ARAgingResult {
  composite_score: ARCompositeScore
  test_results: ARTestResult[]
  data_quality: ARDataQuality
  tb_column_detection: Record<string, unknown> | null
  sl_column_detection: Record<string, unknown> | null
  ar_summary: {
    total_ar_balance: number
    total_allowance: number
    allowance_ratio: number
    ar_account_count: number
  } | null
}

/** Risk tier color mapping for Oat & Obsidian theme */
export const RISK_TIER_COLORS: Record<ARRiskTier, { bg: string; border: string; text: string }> = {
  low: { bg: 'bg-sage-500/10', border: 'border-sage-500/30', text: 'text-sage-400' },
  elevated: { bg: 'bg-oatmeal-500/10', border: 'border-oatmeal-500/30', text: 'text-oatmeal-400' },
  moderate: { bg: 'bg-clay-500/10', border: 'border-clay-500/20', text: 'text-oatmeal-300' },
  high: { bg: 'bg-clay-500/15', border: 'border-clay-500/40', text: 'text-clay-400' },
  critical: { bg: 'bg-clay-500/20', border: 'border-clay-500/60', text: 'text-clay-300' },
}

export const RISK_TIER_LABELS: Record<ARRiskTier, string> = {
  low: 'Low Risk',
  elevated: 'Elevated',
  moderate: 'Moderate',
  high: 'High Risk',
  critical: 'Critical',
}

export const SEVERITY_COLORS: Record<ARSeverity, string> = {
  high: 'text-clay-400',
  medium: 'text-oatmeal-300',
  low: 'text-oatmeal-500',
}
