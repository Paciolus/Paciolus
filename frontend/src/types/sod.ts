/**
 * Segregation of Duties — Sprint 689b.
 *
 * Shapes mirror backend/routes/sod.py Pydantic schemas and
 * backend/sod_engine.py dataclasses.
 */

export type SODSeverity = 'high' | 'medium' | 'low'
export type SODRiskTier = 'high' | 'moderate' | 'low'

export interface SODUserAssignment {
  user_id: string
  user_name: string
  role_codes: string[]
}

export interface SODRolePermission {
  role_code: string
  permissions: string[]
}

export interface SODCustomRule {
  code: string
  title: string
  severity: SODSeverity
  permissions_required: string[]
  permissions_alternate: string[]
  mitigation: string
  rationale: string
}

export interface SODAnalysisRequest {
  user_assignments: SODUserAssignment[]
  role_permissions: SODRolePermission[]
  extra_rules?: SODCustomRule[]
}

export interface SODConflict {
  user_id: string
  user_name: string
  rule_code: string
  rule_title: string
  severity: SODSeverity
  triggering_permissions: string[]
  triggering_roles: string[]
  mitigation: string
  rationale: string
}

export interface SODUserSummary {
  user_id: string
  user_name: string
  conflict_count: number
  high_severity_count: number
  medium_severity_count: number
  low_severity_count: number
  risk_score: number
  risk_tier: SODRiskTier
}

export interface SODAnalysisResponse {
  conflicts: SODConflict[]
  user_summaries: SODUserSummary[]
  rules_evaluated: number
  users_evaluated: number
  users_with_conflicts: number
  high_risk_users: number
}

export interface SODRule {
  code: string
  title: string
  severity: SODSeverity
  permissions_required: string[]
  permissions_alternate: string[]
  mitigation: string
  rationale: string
}

export interface SODRulesResponse {
  rules: SODRule[]
}
