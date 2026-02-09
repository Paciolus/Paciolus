/**
 * Inventory Testing Types (Sprint 119)
 *
 * TypeScript interfaces matching the backend InvTestingResult.to_dict() shape.
 * IAS 2: Inventories / ISA 501: Specific Considerations / ISA 540: Accounting Estimates.
 */

export type InvRiskTier = 'low' | 'elevated' | 'moderate' | 'high' | 'critical'
export type InvTestTier = 'structural' | 'statistical' | 'advanced'
export type InvSeverity = 'high' | 'medium' | 'low'

export interface InventoryEntryData {
  item_id: string | null
  description: string | null
  quantity: number
  unit_cost: number
  extended_value: number
  location: string | null
  last_movement_date: string | null
  category: string | null
  row_number: number
}

export interface FlaggedInventoryEntry {
  entry: InventoryEntryData
  test_name: string
  test_key: string
  test_tier: InvTestTier
  severity: InvSeverity
  issue: string
  confidence: number
  details: Record<string, unknown> | null
}

export interface InvTestResult {
  test_name: string
  test_key: string
  test_tier: InvTestTier
  entries_flagged: number
  total_entries: number
  flag_rate: number
  severity: InvSeverity
  description: string
  flagged_entries: FlaggedInventoryEntry[]
}

export interface InvCompositeScore {
  score: number
  risk_tier: InvRiskTier
  tests_run: number
  total_entries: number
  total_flagged: number
  flag_rate: number
  flags_by_severity: { high: number; medium: number; low: number }
  top_findings: string[]
}

export interface InvDataQuality {
  completeness_score: number
  field_fill_rates: Record<string, number>
  detected_issues: string[]
  total_rows: number
}

export interface InvColumnDetection {
  item_id_column: string | null
  description_column: string | null
  quantity_column: string | null
  unit_cost_column: string | null
  extended_value_column: string | null
  location_column: string | null
  last_movement_date_column: string | null
  category_column: string | null
  overall_confidence: number
  all_columns: string[]
  detection_notes: string[]
}

export interface InventoryTestingResult {
  composite_score: InvCompositeScore
  test_results: InvTestResult[]
  data_quality: InvDataQuality
  column_detection: InvColumnDetection
}

/** Risk tier color mapping for Oat & Obsidian theme */
export const INV_RISK_TIER_COLORS: Record<InvRiskTier, { bg: string; border: string; text: string }> = {
  low: { bg: 'bg-sage-500/10', border: 'border-sage-500/30', text: 'text-sage-400' },
  elevated: { bg: 'bg-oatmeal-500/10', border: 'border-oatmeal-500/30', text: 'text-oatmeal-400' },
  moderate: { bg: 'bg-clay-500/10', border: 'border-clay-500/20', text: 'text-oatmeal-300' },
  high: { bg: 'bg-clay-500/15', border: 'border-clay-500/40', text: 'text-clay-400' },
  critical: { bg: 'bg-clay-500/20', border: 'border-clay-500/60', text: 'text-clay-300' },
}

export const INV_RISK_TIER_LABELS: Record<InvRiskTier, string> = {
  low: 'Low Risk',
  elevated: 'Elevated',
  moderate: 'Moderate',
  high: 'High Risk',
  critical: 'Critical',
}

export const INV_SEVERITY_COLORS: Record<InvSeverity, string> = {
  high: 'text-clay-400',
  medium: 'text-oatmeal-300',
  low: 'text-oatmeal-500',
}
