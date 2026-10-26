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

/**
 * Sprint 846 (W4): an omitted figure is "not supplied" and is not compared —
 * a 941 file without a column must not send zeros for it.
 */
export interface Form941QuarterRequest {
  quarter: number
  total_federal_wages?: string
  total_federal_withholding?: string
  total_ss_wages?: string
  total_medicare_wages?: string
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
  /** Sprint 846 (W4): what the four-quarter 941 sum was compared with. */
  compared_with?: 'payroll_ytd' | 'w3'
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

/**
 * Sprint 826 (W1/W2): a catch-up check that could not run — its statutory
 * figure was not supplied for the tax year, or the data has no age for the
 * employees it would apply to. The message names the authority (e.g.
 * IRC §223(b)(3), IRC §414(v)) whose figure was missing.
 *
 * Sprint 846 (W4/W9): also the Form 941 annual tie-out, when a quarter is
 * missing or duplicated, or a 941 figure was not supplied for every quarter.
 */
export interface W2CheckNotRun {
  check: string
  reason:
    | 'limit_not_supplied'
    | 'age_not_supplied'
    | 'form_941_quarters_incomplete'
    | 'form_941_field_not_supplied'
  employee_ids: string[]
  message: string
}

export interface W2ReconciliationResponse {
  tax_year: number
  employee_discrepancies: W2Discrepancy[]
  form_941_mismatches: Form941Mismatch[]
  /** Sprint 846 (W8): null when no draft W-2s were supplied — there is no W-3. */
  w3_totals: W3Totals | null
  summary: Record<string, unknown>
  statutory_basis?: number | null
  statutory_basis_source?: string | null
  statutory_basis_note?: string
  checks_not_run?: W2CheckNotRun[]
}
