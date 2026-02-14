/**
 * AR Aging Types (Sprint 109)
 *
 * TypeScript interfaces matching the backend ARAgingResult.to_dict() shape.
 * ISA 500/540: Audit Evidence + Auditing Accounting Estimates.
 * Dual-input: TB (required) + optional AR sub-ledger.
 */

import type {
  TestingRiskTier,
  TestingTestTier,
  TestingSeverity,
  BaseFlaggedEntry,
  BaseTestResult,
  BaseCompositeScore,
} from './testingShared'
import {
  TESTING_RISK_TIER_COLORS,
  TESTING_RISK_TIER_LABELS,
  TESTING_SEVERITY_COLORS,
} from './testingShared'

// Re-export shared types as domain aliases (backward compatibility)
export type ARRiskTier = TestingRiskTier
export type ARTestTier = TestingTestTier
export type ARSeverity = TestingSeverity

export type AREntryData = {
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

export interface FlaggedAREntry extends BaseFlaggedEntry<AREntryData> {}

export interface ARTestResult extends BaseTestResult<FlaggedAREntry> {
  skipped: boolean
  skip_reason: string | null
}

export interface ARCompositeScore extends BaseCompositeScore {
  tests_skipped: number
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

// Re-export standardized color maps (backward compat)
export const RISK_TIER_COLORS = TESTING_RISK_TIER_COLORS
export const RISK_TIER_LABELS = TESTING_RISK_TIER_LABELS
export const SEVERITY_COLORS = TESTING_SEVERITY_COLORS
