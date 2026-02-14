/**
 * Fixed Asset Testing Types (Sprint 116)
 *
 * TypeScript interfaces matching the backend FATestingResult.to_dict() shape.
 * IAS 16: Property, Plant and Equipment / ISA 540: Accounting Estimates.
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
export type FARiskTier = TestingRiskTier
export type FATestTier = TestingTestTier
export type FASeverity = TestingSeverity

export type FixedAssetEntryData = {
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

export interface FlaggedFixedAssetEntry extends BaseFlaggedEntry<FixedAssetEntryData> {}

export interface FATestResult extends BaseTestResult<FlaggedFixedAssetEntry> {}

export interface FACompositeScore extends BaseCompositeScore {
  total_entries: number
  flag_rate: number
}

export interface FADataQuality extends BaseDataQuality {}

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

// Re-export standardized color maps (backward compat — FA used prefixed names)
export const FA_RISK_TIER_COLORS = TESTING_RISK_TIER_COLORS
export const FA_RISK_TIER_LABELS = TESTING_RISK_TIER_LABELS
export const FA_SEVERITY_COLORS = TESTING_SEVERITY_COLORS
// Also export unprefixed for consistency with other tools
export const RISK_TIER_COLORS = TESTING_RISK_TIER_COLORS
export const RISK_TIER_LABELS = TESTING_RISK_TIER_LABELS
export const SEVERITY_COLORS = TESTING_SEVERITY_COLORS
