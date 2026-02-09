/**
 * Revenue Testing Types (Sprint 106)
 *
 * TypeScript interfaces matching the backend RevenueTestingResult.to_dict() shape.
 * ISA 240: Presumed fraud risk in revenue recognition.
 */

export type RevenueRiskTier = 'low' | 'elevated' | 'moderate' | 'high' | 'critical'
export type RevenueTestTier = 'structural' | 'statistical' | 'advanced'
export type RevenueSeverity = 'high' | 'medium' | 'low'

export interface RevenueEntryData {
  date: string | null
  amount: number
  account_name: string | null
  account_number: string | null
  description: string | null
  entry_type: string | null
  reference: string | null
  posted_by: string | null
  row_number: number
}

export interface FlaggedRevenueEntry {
  entry: RevenueEntryData
  test_name: string
  test_key: string
  test_tier: RevenueTestTier
  severity: RevenueSeverity
  issue: string
  confidence: number
  details: Record<string, unknown> | null
}

export interface RevenueTestResult {
  test_name: string
  test_key: string
  test_tier: RevenueTestTier
  entries_flagged: number
  total_entries: number
  flag_rate: number
  severity: RevenueSeverity
  description: string
  flagged_entries: FlaggedRevenueEntry[]
}

export interface RevenueCompositeScore {
  score: number
  risk_tier: RevenueRiskTier
  tests_run: number
  total_entries: number
  total_flagged: number
  flag_rate: number
  flags_by_severity: { high: number; medium: number; low: number }
  top_findings: string[]
}

export interface RevenueDataQuality {
  completeness_score: number
  field_fill_rates: Record<string, number>
  detected_issues: string[]
  total_rows: number
}

export interface RevenueColumnDetection {
  date_column: string | null
  amount_column: string | null
  account_name_column: string | null
  account_number_column: string | null
  description_column: string | null
  entry_type_column: string | null
  reference_column: string | null
  posted_by_column: string | null
  overall_confidence: number
  requires_mapping: boolean
  all_columns: string[]
  detection_notes: string[]
}

export interface RevenueTestingResult {
  composite_score: RevenueCompositeScore
  test_results: RevenueTestResult[]
  data_quality: RevenueDataQuality
  column_detection: RevenueColumnDetection
}

/** Risk tier color mapping for Oat & Obsidian theme */
export const RISK_TIER_COLORS: Record<RevenueRiskTier, { bg: string; border: string; text: string }> = {
  low: { bg: 'bg-sage-500/10', border: 'border-sage-500/30', text: 'text-sage-400' },
  elevated: { bg: 'bg-oatmeal-500/10', border: 'border-oatmeal-500/30', text: 'text-oatmeal-400' },
  moderate: { bg: 'bg-clay-500/10', border: 'border-clay-500/20', text: 'text-oatmeal-300' },
  high: { bg: 'bg-clay-500/15', border: 'border-clay-500/40', text: 'text-clay-400' },
  critical: { bg: 'bg-clay-500/20', border: 'border-clay-500/60', text: 'text-clay-300' },
}

export const RISK_TIER_LABELS: Record<RevenueRiskTier, string> = {
  low: 'Low Risk',
  elevated: 'Elevated',
  moderate: 'Moderate',
  high: 'High Risk',
  critical: 'Critical',
}

export const SEVERITY_COLORS: Record<RevenueSeverity, string> = {
  high: 'text-clay-400',
  medium: 'text-oatmeal-300',
  low: 'text-oatmeal-500',
}
