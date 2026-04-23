/**
 * W-2 / W-3 Reconciliation — Sprint 689d.
 *
 * Shapes mirror backend/routes/w2_reconciliation.py Pydantic contracts
 * and backend/w2_reconciliation_engine.py dataclasses. All monetary
 * fields are Decimal-strings on the wire.
 */

export type DiscrepancySeverity = 'high' | 'medium' | 'low'
export type HsaCoverage = 'none' | 'self_only' | 'family'
export type RetirementPlanType = '401k' | 'simple_ira'

export interface W2EmployeePayrollRequest {
  employee_id: string
  employee_name: string
  age?: number | null
  federal_wages: string
  federal_withholding: string
  ss_wages: string
  ss_tax_withheld: string
  medicare_wages: string
  medicare_tax_withheld: string
  hsa_contributions: string
  hsa_coverage: HsaCoverage
  retirement_401k: string
  retirement_simple_ira: string
  retirement_plan_type?: RetirementPlanType | null
}

export interface W2DraftRequest {
  employee_id: string
  box_1_federal_wages: string
  box_2_federal_withholding: string
  box_3_ss_wages: string
  box_4_ss_tax_withheld: string
  box_5_medicare_wages: string
  box_6_medicare_tax_withheld: string
  box_12_code_w_hsa: string
  box_12_code_d_401k: string
  box_12_code_s_simple: string
}

export interface Form941QuarterRequest {
  quarter: number
  total_federal_wages: string
  total_federal_withholding: string
  total_ss_wages: string
  total_medicare_wages: string
}

export interface W2ReconciliationRequest {
  tax_year: number
  employees: W2EmployeePayrollRequest[]
  w2_drafts: W2DraftRequest[]
  form_941_quarters: Form941QuarterRequest[]
  tolerance: string
}

export interface W2Discrepancy {
  employee_id: string
  employee_name: string
  kind: string
  severity: DiscrepancySeverity
  expected: string
  actual: string
  difference: string
  message: string
}

export interface Form941Mismatch {
  quarter: number | null
  kind: string
  severity: DiscrepancySeverity
  expected: string
  actual: string
  difference: string
  message: string
}

export interface W3Totals {
  total_federal_wages: string
  total_federal_withholding: string
  total_ss_wages: string
  total_ss_tax_withheld: string
  total_medicare_wages: string
  total_medicare_tax_withheld: string
  employee_count: number
}

export interface W2ReconciliationResponse {
  tax_year: number
  employee_discrepancies: W2Discrepancy[]
  form_941_mismatches: Form941Mismatch[]
  w3_totals: W3Totals
  summary: Record<string, unknown>
}
