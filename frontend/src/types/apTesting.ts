/**
 * AP Payment Testing Types (Sprint 75)
 *
 * TypeScript interfaces matching the backend APTestingResult.to_dict() shape.
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
export type APRiskTier = TestingRiskTier
export type APTestTier = TestingTestTier
export type APSeverity = TestingSeverity

export type APPaymentData = {
  invoice_number: string | null
  invoice_date: string | null
  payment_date: string | null
  vendor_name: string
  vendor_id: string | null
  amount: number
  check_number: string | null
  description: string | null
  gl_account: string | null
  payment_method: string | null
  row_number: number
}

export interface FlaggedAPPayment extends BaseFlaggedEntry<APPaymentData> {}

export interface APTestResult extends BaseTestResult<FlaggedAPPayment> {}

export interface APCompositeScore extends BaseCompositeScore {
  total_entries: number
  flag_rate: number
}

export interface APDataQuality extends BaseDataQuality {}

export interface APColumnDetection {
  vendor_name_column: string | null
  amount_column: string | null
  payment_date_column: string | null
  invoice_number_column: string | null
  invoice_date_column: string | null
  vendor_id_column: string | null
  check_number_column: string | null
  description_column: string | null
  gl_account_column: string | null
  payment_method_column: string | null
  has_dual_dates: boolean
  has_check_numbers: boolean
  overall_confidence: number
  requires_mapping: boolean
  all_columns: string[]
  detection_notes: string[]
}

export interface APTestingResult {
  composite_score: APCompositeScore
  test_results: APTestResult[]
  data_quality: APDataQuality
  column_detection: APColumnDetection
}

// Re-export standardized color maps (backward compat — consumers import from here)
export const RISK_TIER_COLORS = TESTING_RISK_TIER_COLORS
export const RISK_TIER_LABELS = TESTING_RISK_TIER_LABELS
export const SEVERITY_COLORS = TESTING_SEVERITY_COLORS
