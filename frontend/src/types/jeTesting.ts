/**
 * Journal Entry Testing Types (Sprint 66)
 *
 * TypeScript interfaces matching the backend JETestingResult.to_dict() shape.
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
export type JERiskTier = TestingRiskTier
export type JETestTier = TestingTestTier
export type JESeverity = TestingSeverity

export type JournalEntryData = {
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

export interface FlaggedJournalEntry extends BaseFlaggedEntry<JournalEntryData> {}

export interface JETestResult extends BaseTestResult<FlaggedJournalEntry> {}

export interface JECompositeScore extends BaseCompositeScore {
  total_entries: number
  flag_rate: number
}

export interface GLDataQuality extends BaseDataQuality {}

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

export interface SamplingStratum {
  name: string
  criteria: string
  population_size: number
  sample_size: number
  sampled_rows: number[]
}

export interface SamplingResult {
  total_population: number
  total_sampled: number
  strata: SamplingStratum[]
  sampled_entries: JournalEntryData[]
  sampling_seed: string
  parameters: {
    stratify_by: string[]
    sample_rate: number
    fixed_per_stratum: number | null
  }
}

export interface SamplingPreview {
  strata: Array<{ name: string; criteria: string; population_size: number }>
  total_population: number
  stratify_by: string[]
}

export type SamplingCriterion = 'account' | 'amount_range' | 'period' | 'user'

export const SAMPLING_CRITERIA_LABELS: Record<SamplingCriterion, string> = {
  account: 'Account',
  amount_range: 'Amount Range',
  period: 'Period',
  user: 'User',
}

export interface JETestingResult {
  composite_score: JECompositeScore
  test_results: JETestResult[]
  data_quality: GLDataQuality
  multi_currency_warning: MultiCurrencyWarning | null
  column_detection: GLColumnDetection
  benford_result: BenfordResult | null
  sampling_result?: SamplingResult | null
}

// Re-export standardized color maps (backward compat)
export const RISK_TIER_COLORS = TESTING_RISK_TIER_COLORS
export const RISK_TIER_LABELS = TESTING_RISK_TIER_LABELS
export const SEVERITY_COLORS = TESTING_SEVERITY_COLORS
