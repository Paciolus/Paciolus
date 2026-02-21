/**
 * Revenue Testing Types (Sprint 106)
 *
 * TypeScript interfaces matching the backend RevenueTestingResult.to_dict() shape.
 * ISA 240: Presumed fraud risk in revenue recognition.
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
export type RevenueRiskTier = TestingRiskTier
export type RevenueTestTier = TestingTestTier
export type RevenueSeverity = TestingSeverity

export type RevenueEntryData = {
  date: string | null
  amount: number
  account_name: string | null
  account_number: string | null
  description: string | null
  entry_type: string | null
  reference: string | null
  posted_by: string | null
  row_number: number
  // Contract-aware fields (ASC 606 / IFRS 15 — Sprint 353)
  contract_id: string | null
  performance_obligation_id: string | null
  recognition_method: string | null
  contract_modification: string | null
  allocation_basis: string | null
  obligation_satisfaction_date: string | null
}

export interface FlaggedRevenueEntry extends BaseFlaggedEntry<RevenueEntryData> {}

export interface RevenueTestResult extends BaseTestResult<FlaggedRevenueEntry> {
  skipped?: boolean
  skip_reason?: string | null
}

export interface RevenueCompositeScore extends BaseCompositeScore {
  total_entries: number
  flag_rate: number
}

export interface RevenueDataQuality extends BaseDataQuality {}

export interface RevenueColumnDetection {
  date_column: string | null
  amount_column: string | null
  account_name_column: string | null
  account_number_column: string | null
  description_column: string | null
  entry_type_column: string | null
  reference_column: string | null
  posted_by_column: string | null
  // Contract-aware columns (ASC 606 / IFRS 15 — Sprint 353)
  contract_id_column: string | null
  performance_obligation_id_column: string | null
  recognition_method_column: string | null
  contract_modification_column: string | null
  allocation_basis_column: string | null
  obligation_satisfaction_date_column: string | null
  overall_confidence: number
  requires_mapping: boolean
  all_columns: string[]
  detection_notes: string[]
}

export interface ContractEvidenceLevel {
  level: 'full' | 'partial' | 'minimal' | 'none'
  confidence_modifier: number
  detected_fields: string[]
  total_contract_fields: number
  detected_count: number
}

export interface RevenueTestingResult {
  composite_score: RevenueCompositeScore
  test_results: RevenueTestResult[]
  data_quality: RevenueDataQuality
  column_detection: RevenueColumnDetection
  contract_evidence: ContractEvidenceLevel | null
}

// Re-export standardized color maps (backward compat)
export const RISK_TIER_COLORS = TESTING_RISK_TIER_COLORS
export const RISK_TIER_LABELS = TESTING_RISK_TIER_LABELS
export const SEVERITY_COLORS = TESTING_SEVERITY_COLORS
