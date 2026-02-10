/**
 * Fixed Asset Testing Types (Sprint 116)
 *
 * TypeScript interfaces matching the backend FATestingResult.to_dict() shape.
 * IAS 16: Property, Plant and Equipment / ISA 540: Accounting Estimates.
 */

export type FARiskTier = 'low' | 'elevated' | 'moderate' | 'high' | 'critical'
export type FATestTier = 'structural' | 'statistical' | 'advanced'
export type FASeverity = 'high' | 'medium' | 'low'

export interface FixedAssetEntryData {
  asset_id: string | null
  description: string | null
  cost: number
  accumulated_depreciation: number
  acquisition_date: string | null
  useful_life: number | null
  depreciation_method: string | null
  residual_value: number
  location: string | null
  category: string | null
  net_book_value: number | null
  row_number: number
}

export interface FlaggedFixedAssetEntry {
  entry: FixedAssetEntryData
  test_name: string
  test_key: string
  test_tier: FATestTier
  severity: FASeverity
  issue: string
  confidence: number
  details: Record<string, unknown> | null
}

export interface FATestResult {
  test_name: string
  test_key: string
  test_tier: FATestTier
  entries_flagged: number
  total_entries: number
  flag_rate: number
  severity: FASeverity
  description: string
  flagged_entries: FlaggedFixedAssetEntry[]
}

export interface FACompositeScore {
  score: number
  risk_tier: FARiskTier
  tests_run: number
  total_entries: number
  total_flagged: number
  flag_rate: number
  flags_by_severity: { high: number; medium: number; low: number }
  top_findings: string[]
}

export interface FADataQuality {
  completeness_score: number
  field_fill_rates: Record<string, number>
  detected_issues: string[]
  total_rows: number
}

export interface FAColumnDetection {
  asset_id_column: string | null
  description_column: string | null
  cost_column: string | null
  accumulated_depreciation_column: string | null
  acquisition_date_column: string | null
  useful_life_column: string | null
  depreciation_method_column: string | null
  residual_value_column: string | null
  location_column: string | null
  category_column: string | null
  net_book_value_column: string | null
  overall_confidence: number
  all_columns: string[]
  detection_notes: string[]
}

export interface FixedAssetTestingResult {
  composite_score: FACompositeScore
  test_results: FATestResult[]
  data_quality: FADataQuality
  column_detection: FAColumnDetection
}

/** Risk tier color mapping for Oat & Obsidian theme */
export const FA_RISK_TIER_COLORS: Record<FARiskTier, { bg: string; border: string; text: string }> = {
  low: { bg: 'bg-sage-50', border: 'border-sage-200', text: 'text-sage-700' },
  elevated: { bg: 'bg-oatmeal-100', border: 'border-oatmeal-300', text: 'text-oatmeal-700' },
  moderate: { bg: 'bg-clay-50', border: 'border-clay-200', text: 'text-clay-700' },
  high: { bg: 'bg-clay-100', border: 'border-clay-300', text: 'text-clay-700' },
  critical: { bg: 'bg-clay-200', border: 'border-clay-400', text: 'text-clay-800' },
}

export const FA_RISK_TIER_LABELS: Record<FARiskTier, string> = {
  low: 'Low Risk',
  elevated: 'Elevated',
  moderate: 'Moderate',
  high: 'High Risk',
  critical: 'Critical',
}

export const FA_SEVERITY_COLORS: Record<FASeverity, string> = {
  high: 'text-clay-600',
  medium: 'text-content-primary',
  low: 'text-content-secondary',
}
