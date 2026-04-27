/**
 * Sprint 728b — Analytical Expectations (ISA 520) types.
 *
 * Frontend mirror of backend/schemas/analytical_expectation_schemas.py.
 */

export type ExpectationTargetType = 'account' | 'balance' | 'ratio' | 'flux_line';

export type ExpectationCorroborationTag =
  | 'industry_data'
  | 'prior_period'
  | 'budget'
  | 'regression_model'
  | 'other';

export type ExpectationResultStatus =
  | 'not_evaluated'
  | 'within_threshold'
  | 'exceeds_threshold';

export interface AnalyticalExpectation {
  id: number;
  engagement_id: number;
  procedure_target_type: ExpectationTargetType;
  procedure_target_label: string;
  expected_value: number | null;
  expected_range_low: number | null;
  expected_range_high: number | null;
  precision_threshold_amount: number | null;
  precision_threshold_percent: number | null;
  corroboration_basis_text: string;
  corroboration_tags: string[];
  cpa_notes: string | null;
  result_actual_value: number | null;
  result_variance_amount: number | null;
  result_status: ExpectationResultStatus;
  created_by: number;
  created_at: string;
  updated_by: number | null;
  updated_at: string;
}

export interface AnalyticalExpectationCreateInput {
  procedure_target_type: ExpectationTargetType;
  procedure_target_label: string;
  expected_value?: number | null;
  expected_range_low?: number | null;
  expected_range_high?: number | null;
  precision_threshold_amount?: number | null;
  precision_threshold_percent?: number | null;
  corroboration_basis_text: string;
  corroboration_tags: string[];
  cpa_notes?: string | null;
}

export interface AnalyticalExpectationUpdateInput {
  procedure_target_label?: string;
  expected_value?: number | null;
  expected_range_low?: number | null;
  expected_range_high?: number | null;
  precision_threshold_amount?: number | null;
  precision_threshold_percent?: number | null;
  corroboration_basis_text?: string;
  corroboration_tags?: string[];
  cpa_notes?: string | null;
  result_actual_value?: number | null;
  clear_result?: boolean;
}

export interface AnalyticalExpectationListResponse {
  items: AnalyticalExpectation[];
  total_count: number;
  page: number;
  page_size: number;
}

export const EXPECTATION_TARGET_LABELS: Record<ExpectationTargetType, string> = {
  account: 'Account',
  balance: 'Balance',
  ratio: 'Ratio',
  flux_line: 'Flux Line',
};

export const EXPECTATION_TAG_LABELS: Record<ExpectationCorroborationTag, string> = {
  industry_data: 'Industry Data',
  prior_period: 'Prior Period',
  budget: 'Budget',
  regression_model: 'Regression Model',
  other: 'Other',
};

export const EXPECTATION_STATUS_LABELS: Record<ExpectationResultStatus, string> = {
  not_evaluated: 'Not Evaluated',
  within_threshold: 'Within Threshold',
  exceeds_threshold: 'Exceeds Threshold',
};

export const EXPECTATION_STATUS_COLORS: Record<ExpectationResultStatus, string> = {
  not_evaluated: 'bg-oatmeal-100 text-content-secondary border-theme',
  within_threshold: 'bg-sage-50 text-sage-700 border-sage-200',
  exceeds_threshold: 'bg-clay-50 text-clay-700 border-clay-200',
};
