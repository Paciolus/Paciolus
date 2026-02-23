/**
 * Inventory Testing Types (Sprint 119)
 *
 * TypeScript interfaces matching the backend InvTestingResult.to_dict() shape.
 * IAS 2: Inventories / ISA 501: Specific Considerations / ISA 540: Accounting Estimates.
 */

import {
  TESTING_RISK_TIER_COLORS,
  TESTING_RISK_TIER_LABELS,
  TESTING_SEVERITY_COLORS,
} from './testingShared'
import type {
  TestingRiskTier,
  TestingTestTier,
  TestingSeverity,
  BaseFlaggedEntry,
  BaseTestResult,
  BaseCompositeScore,
  BaseDataQuality,
} from './testingShared'

// Re-export shared types as domain aliases (backward compatibility)
export type InvRiskTier = TestingRiskTier
export type InvTestTier = TestingTestTier
export type InvSeverity = TestingSeverity

export type InventoryEntryData = {
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

export interface FlaggedInventoryEntry extends BaseFlaggedEntry<InventoryEntryData> {}

export interface InvTestResult extends BaseTestResult<FlaggedInventoryEntry> {}

export interface InvCompositeScore extends BaseCompositeScore {
  total_entries: number
  flag_rate: number
}

export interface InvDataQuality extends BaseDataQuality {}

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

// Re-export standardized color maps (backward compat — Inv used prefixed names)
export const INV_RISK_TIER_COLORS = TESTING_RISK_TIER_COLORS
export const INV_RISK_TIER_LABELS = TESTING_RISK_TIER_LABELS
export const INV_SEVERITY_COLORS = TESTING_SEVERITY_COLORS
// Also export unprefixed for consistency with other tools
export const RISK_TIER_COLORS = TESTING_RISK_TIER_COLORS
export const RISK_TIER_LABELS = TESTING_RISK_TIER_LABELS
export const SEVERITY_COLORS = TESTING_SEVERITY_COLORS
