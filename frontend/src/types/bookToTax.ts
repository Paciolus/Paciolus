/**
 * Book-to-Tax — Sprint 689f.
 *
 * Shapes mirror backend/routes/book_to_tax.py Pydantic contracts.
 * All monetary values are Decimal strings on the wire.
 */

export type AdjustmentDirection = 'add' | 'subtract'
export type DifferenceType = 'permanent' | 'temporary'

export interface AdjustmentRequest {
  label: string
  amount: string
  difference_type: DifferenceType
  direction: AdjustmentDirection
  code?: string | null
}

export interface RollforwardRequest {
  beginning_dta: string
  beginning_dtl: string
}

export interface BookToTaxRequest {
  tax_year: number
  book_pretax_income: string
  total_assets: string
  federal_tax_rate: string
  state_tax_rate: string
  adjustments: AdjustmentRequest[]
  rollforward: RollforwardRequest
}

export interface AdjustmentLine {
  label: string
  code: string | null
  difference_type: string
  direction: string
  amount: string
  signed_amount: string
}

export interface ScheduleM1 {
  net_income_per_books: string
  federal_income_tax_per_books: string
  permanent_additions: AdjustmentLine[]
  temporary_additions: AdjustmentLine[]
  permanent_subtractions: AdjustmentLine[]
  temporary_subtractions: AdjustmentLine[]
  taxable_income: string
}

export interface ScheduleM3Section {
  label: string
  code: string | null
  permanent: string
  temporary: string
  total: string
}

export interface ScheduleM3 {
  income_per_books: string
  income_items: ScheduleM3Section[]
  expense_items: ScheduleM3Section[]
  taxable_income: string
}

export interface DeferredTaxRollforward {
  beginning_dta: string
  beginning_dtl: string
  current_year_temporary_adjustments: string
  tax_rate: string
  current_year_movement: string
  ending_dta: string
  ending_dtl: string
}

export interface TaxProvision {
  taxable_income: string
  current_federal_tax: string
  current_state_tax: string
  deferred_tax_expense: string
  total_tax_expense: string
  effective_rate: string
}

export interface BookToTaxResponse {
  tax_year: number
  entity_size: 'small' | 'large' | string
  schedule_m1: ScheduleM1
  schedule_m3: ScheduleM3
  deferred_tax: DeferredTaxRollforward
  tax_provision: TaxProvision
}

export interface StandardAdjustment {
  code: string
  description: string
  difference_type: DifferenceType
  typical_direction: AdjustmentDirection
}

export interface StandardAdjustmentsResponse {
  standard_adjustments: StandardAdjustment[]
}
