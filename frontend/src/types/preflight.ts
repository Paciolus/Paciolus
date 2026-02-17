/**
 * Pre-Flight Report Types — Sprint 283
 *
 * Mirrors backend PreFlightReportResponse schema.
 */

export interface PreFlightColumnQuality {
  role: string
  detected_name: string | null
  confidence: number
  status: 'found' | 'low_confidence' | 'missing'
}

export interface PreFlightIssue {
  category: string
  severity: 'high' | 'medium' | 'low'
  message: string
  affected_count: number
  remediation: string
}

export interface PreFlightDuplicate {
  account_code: string
  count: number
}

export interface PreFlightEncodingAnomaly {
  row_index: number
  value: string
  column: string
}

export interface PreFlightMixedSign {
  account: string
  positive_count: number
  negative_count: number
}

export interface PreFlightReport {
  filename: string
  row_count: number
  column_count: number
  readiness_score: number
  readiness_label: 'Ready' | 'Review Recommended' | 'Issues Found'
  columns: PreFlightColumnQuality[]
  issues: PreFlightIssue[]
  duplicates: PreFlightDuplicate[]
  encoding_anomalies: PreFlightEncodingAnomaly[]
  mixed_sign_accounts: PreFlightMixedSign[]
  zero_balance_count: number
  null_counts: Record<string, number>
}
