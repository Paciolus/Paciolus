/**
 * Composite Risk Scoring Types (Sprint 688)
 *
 * Mirrors backend `routes/composite_risk.py` schemas. ISA 315 (Revised 2019):
 * auditor-provided inherent/control/fraud risk assessments per account/assertion,
 * combined via the 4x4 RMM matrix, optionally enriched with automated diagnostic
 * data (TB anomaly score, tool scores, going concern indicators).
 */

/**
 * Composite (RMM-matrix) risk level used by the ISA 315 risk-scoring tool.
 * Distinct from `ThresholdRiskLevel` (`utils/themeUtils.ts` — 4-value with
 * `'none'`, used by per-row diagnostic visualizations) and from `RiskLevel`
 * (`types/diagnostic.ts` enum — streaming-auditor finding tier).
 */
export type CompositeRiskLevel = 'low' | 'moderate' | 'elevated' | 'high'

export type Assertion =
  | 'existence'
  | 'completeness'
  | 'valuation'
  | 'rights'
  | 'presentation'

export const RISK_LEVELS: CompositeRiskLevel[] = ['low', 'moderate', 'elevated', 'high']
export const ASSERTIONS: Assertion[] = [
  'existence',
  'completeness',
  'valuation',
  'rights',
  'presentation',
]

export const RISK_LEVEL_LABELS: Record<CompositeRiskLevel, string> = {
  low: 'Low',
  moderate: 'Moderate',
  elevated: 'Elevated',
  high: 'High',
}

export const ASSERTION_LABELS: Record<Assertion, string> = {
  existence: 'Existence',
  completeness: 'Completeness',
  valuation: 'Valuation',
  rights: 'Rights & Obligations',
  presentation: 'Presentation',
}

export const RISK_BADGE_STYLES: Record<CompositeRiskLevel, string> = {
  low: 'bg-sage-50 text-sage-700 border-sage-200',
  moderate: 'bg-oatmeal-100 text-obsidian-700 border-oatmeal-300',
  elevated: 'bg-clay-50 text-clay-700 border-clay-200',
  high: 'bg-clay-100 text-clay-800 border-clay-300',
}

export interface AccountRiskAssessmentInput {
  account_name: string
  assertion: Assertion
  inherent_risk: CompositeRiskLevel
  control_risk: CompositeRiskLevel
  fraud_risk_factor: boolean
  auditor_notes: string
}

export interface CompositeRiskProfileRequest {
  account_assessments: AccountRiskAssessmentInput[]
  tb_diagnostic_score?: number | null
  tb_diagnostic_tier?: string | null
  testing_scores?: Record<string, number> | null
  going_concern_indicators_triggered: number
}

export interface AccountRiskAssessmentResponse {
  account_name: string
  assertion: Assertion
  inherent_risk: CompositeRiskLevel
  control_risk: CompositeRiskLevel
  combined_risk: CompositeRiskLevel
  fraud_risk_factor: boolean
  auditor_notes?: string | null
}

export interface CompositeRiskProfileResponse {
  account_assessments: AccountRiskAssessmentResponse[]
  tb_diagnostic_score?: number | null
  tb_diagnostic_tier?: string | null
  testing_scores: Record<string, number>
  going_concern_indicators_triggered: number
  high_risk_accounts: number
  fraud_risk_accounts: number
  total_assessments: number
  risk_distribution: Record<CompositeRiskLevel, number>
  overall_risk_tier?: CompositeRiskLevel | null
  disclaimer: string
}
