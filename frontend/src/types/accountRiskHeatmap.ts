/**
 * Account Risk Heatmap Types (Sprint 688)
 *
 * Mirrors backend `routes/account_risk_heatmap.py`. Aggregates per-account
 * audit signals across diagnostic engines into a triage-density view.
 */

export type PriorityTier = 'high' | 'moderate' | 'low'
export type Severity = 'high' | 'medium' | 'low'

export const PRIORITY_TIER_STYLES: Record<PriorityTier, string> = {
  high: 'bg-clay-100 text-clay-800 border-clay-300',
  moderate: 'bg-oatmeal-200 text-obsidian-700 border-oatmeal-400',
  low: 'bg-sage-50 text-sage-700 border-sage-200',
}

export const PRIORITY_TIER_LABELS: Record<PriorityTier, string> = {
  high: 'High',
  moderate: 'Moderate',
  low: 'Low',
}

export interface RawSignalInput {
  account_number?: string
  account_name: string
  source: string
  severity?: Severity | string
  issue: string
  materiality?: string
  confidence?: number
}

export interface HeatmapRequest {
  signals?: RawSignalInput[]
  audit_anomalies?: Record<string, unknown>[]
  classification_issues?: Record<string, unknown>[]
  cutoff_flags?: Record<string, unknown>[]
  accrual_findings?: Record<string, unknown>[]
  composite_risk_profile?: Record<string, unknown> | null
}

export interface HeatmapRow {
  account_number: string
  account_name: string
  signal_count: number
  weighted_score: number
  sources: string[]
  severities: Record<string, number>
  issues: string[]
  total_materiality: string
  priority_tier: PriorityTier
  rank: number
}

export interface HeatmapResponse {
  rows: HeatmapRow[]
  total_accounts_with_signals: number
  high_priority_count: number
  moderate_priority_count: number
  low_priority_count: number
  total_signals: number
  sources_active: string[]
}
