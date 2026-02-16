/**
 * Statistical Sampling Types (Sprint 270)
 * Phase XXXVI: Tool 12
 *
 * ISA 530 / PCAOB AS 2315: Two-phase workflow types.
 * Phase 1 (Design): population upload → sample selection
 * Phase 2 (Evaluate): completed sample → projected misstatement → Pass/Fail
 */

// ═══════════════════════════════════════════════════════════════
// Enums & Constants
// ═══════════════════════════════════════════════════════════════

export type SamplingMethod = 'mus' | 'random'

export type SamplingConclusion = 'pass' | 'fail'

export const SAMPLING_METHOD_LABELS: Record<SamplingMethod, string> = {
  mus: 'Monetary Unit Sampling (MUS)',
  random: 'Simple Random Sampling',
} as const

export const SAMPLING_CONCLUSION_COLORS: Record<SamplingConclusion, string> = {
  pass: 'text-sage-500',
  fail: 'text-clay-500',
} as const

export const SAMPLING_CONCLUSION_BG: Record<SamplingConclusion, string> = {
  pass: 'bg-sage-500/10 border-sage-500/30',
  fail: 'bg-clay-500/10 border-clay-500/30',
} as const

export const CONFIDENCE_LEVELS = [
  { value: 0.80, label: '80%' },
  { value: 0.85, label: '85%' },
  { value: 0.90, label: '90%' },
  { value: 0.95, label: '95% (Recommended)' },
  { value: 0.99, label: '99%' },
] as const

// ═══════════════════════════════════════════════════════════════
// Design Phase (Phase 1)
// ═══════════════════════════════════════════════════════════════

export interface SamplingDesignConfig {
  method: SamplingMethod
  confidence_level: number
  tolerable_misstatement: number
  expected_misstatement: number
  stratification_threshold: number | null
  sample_size_override: number | null
}

export interface SelectedSampleItem {
  row_index: number
  item_id: string
  description: string
  recorded_amount: number
  stratum: 'high_value' | 'remainder'
  selection_method: 'high_value_100pct' | 'mus_interval' | 'random'
  interval_position: number | null
}

export interface StratumSummary {
  stratum: string
  threshold: string
  count: number
  total_value: number
  sample_size: number
}

export interface SamplingDesignResult {
  method: SamplingMethod
  confidence_level: number
  confidence_factor: number
  tolerable_misstatement: number
  expected_misstatement: number
  population_size: number
  population_value: number
  sampling_interval: number | null
  calculated_sample_size: number
  actual_sample_size: number
  high_value_count: number
  high_value_total: number
  remainder_count: number
  remainder_sample_size: number
  selected_items: SelectedSampleItem[]
  random_start: number | null
  strata_summary: StratumSummary[]
}

// ═══════════════════════════════════════════════════════════════
// Evaluation Phase (Phase 2)
// ═══════════════════════════════════════════════════════════════

export interface SamplingEvaluationConfig {
  method: SamplingMethod
  confidence_level: number
  tolerable_misstatement: number
  expected_misstatement: number
  population_value: number
  sample_size: number
  sampling_interval: number | null
}

export interface SamplingError {
  row_index: number
  item_id: string
  recorded_amount: number
  audited_amount: number
  misstatement: number
  tainting: number
}

export interface SamplingEvaluationResult {
  method: SamplingMethod
  confidence_level: number
  tolerable_misstatement: number
  expected_misstatement: number
  population_value: number
  sample_size: number
  sample_value: number
  errors_found: number
  total_misstatement: number
  projected_misstatement: number
  basic_precision: number
  incremental_allowance: number
  upper_error_limit: number
  conclusion: SamplingConclusion
  conclusion_detail: string
  errors: SamplingError[]
  taintings_ranked: number[]
}
