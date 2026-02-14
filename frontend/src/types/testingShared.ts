/**
 * Shared Testing Types (Sprint 137)
 *
 * Common type definitions and color constants used across all 7 testing tools.
 * Domain-specific types extend these bases.
 */

import type { Severity } from './shared'

// ─── Shared Type Aliases ───────────────────────────────────────────────────────

export type TestingRiskTier = 'low' | 'elevated' | 'moderate' | 'high' | 'critical'
export type TestingTestTier = 'structural' | 'statistical' | 'advanced'
/** Domain alias for the canonical Severity type (Sprint 225). */
export type TestingSeverity = Severity

// ─── Base Interfaces ───────────────────────────────────────────────────────────

/** Shared shape for flagged-entry wrappers (identical across all 7 tools). */
export interface BaseFlaggedEntry<TEntry> {
  entry: TEntry
  test_name: string
  test_key: string
  test_tier: TestingTestTier
  severity: TestingSeverity
  issue: string
  confidence: number
  details: Record<string, unknown> | null
}

/** Shared shape for per-test results (6/7 tools; AR adds skipped fields). */
export interface BaseTestResult<TFlagged> {
  test_name: string
  test_key: string
  test_tier: TestingTestTier
  entries_flagged: number
  total_entries: number
  flag_rate: number
  severity: TestingSeverity
  description: string
  flagged_entries: TFlagged[]
}

/** Shared shape for composite risk scores (core fields only). */
export interface BaseCompositeScore<TFinding = string> {
  score: number
  risk_tier: TestingRiskTier
  tests_run: number
  total_flagged: number
  flags_by_severity: { high: number; medium: number; low: number }
  top_findings: TFinding[]
}

/** Shared shape for data quality metrics (6/7 tools; AR has different row fields). */
export interface BaseDataQuality {
  completeness_score: number
  field_fill_rates: Record<string, number>
  detected_issues: string[]
  total_rows: number
}

// ─── Standardized Color Maps ───────────────────────────────────────────────────

/** Risk tier color mapping — Oat & Obsidian light theme (standardized -700 palette). */
export const TESTING_RISK_TIER_COLORS: Record<TestingRiskTier, { bg: string; border: string; text: string }> = {
  low: { bg: 'bg-sage-50', border: 'border-sage-200', text: 'text-sage-700' },
  elevated: { bg: 'bg-oatmeal-100', border: 'border-oatmeal-300', text: 'text-oatmeal-700' },
  moderate: { bg: 'bg-clay-50', border: 'border-clay-200', text: 'text-clay-700' },
  high: { bg: 'bg-clay-100', border: 'border-clay-300', text: 'text-clay-700' },
  critical: { bg: 'bg-clay-200', border: 'border-clay-400', text: 'text-clay-800' },
}

export const TESTING_RISK_TIER_LABELS: Record<TestingRiskTier, string> = {
  low: 'Low Risk',
  elevated: 'Elevated',
  moderate: 'Moderate',
  high: 'High Risk',
  critical: 'Critical',
}

export const TESTING_SEVERITY_COLORS: Record<TestingSeverity, string> = {
  high: 'text-clay-600',
  medium: 'text-content-primary',
  low: 'text-content-secondary',
}
