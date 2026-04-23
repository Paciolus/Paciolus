/**
 * Form 1099 Preparation — Sprint 689e.
 *
 * Shapes mirror backend/routes/form_1099.py Pydantic contracts and
 * backend/form_1099_engine.py dataclasses.
 */

export type VendorEntity =
  | 'individual'
  | 'partnership'
  | 'llc'
  | 'corporation'
  | 's_corporation'
  | 'government'
  | 'tax_exempt'
  | 'unknown'

export type PaymentMethod1099 =
  | 'check'
  | 'ach'
  | 'wire'
  | 'cash'
  | 'credit_card'
  | 'paypal'
  | 'unknown'

export type PaymentCategory1099 =
  | 'nonemployee_comp'
  | 'rents'
  | 'royalties'
  | 'medical'
  | 'legal'
  | 'interest'
  | 'other'

export interface VendorRequest {
  vendor_id: string
  vendor_name: string
  tin?: string | null
  entity_type: VendorEntity
  address_line_1?: string | null
  city?: string | null
  state?: string | null
  postal_code?: string | null
}

export interface PaymentRequest {
  vendor_id: string
  amount: string
  payment_category: PaymentCategory1099
  payment_method: PaymentMethod1099
  payment_date?: string | null
  invoice_number?: string | null
}

export interface Form1099Request {
  tax_year: number
  vendors: VendorRequest[]
  payments: PaymentRequest[]
}

export interface VendorBoxAmount {
  category: string
  form_type: string
  box: number
  amount: string
}

export interface Form1099Candidate {
  vendor_id: string
  vendor_name: string
  form_type: string
  total_reportable: string
  box_amounts: VendorBoxAmount[]
  payment_count: number
  excluded_amount: string
  flagged_for_review: boolean
  review_reasons: string[]
}

export interface VendorDataQuality {
  vendor_id: string
  vendor_name: string
  missing_tin: boolean
  invalid_tin_format: boolean
  missing_address: boolean
  unknown_entity_type: boolean
  has_issue: boolean
  notes: string[]
}

export interface W9CollectionRow {
  vendor_id: string
  vendor_name: string
  reason: string
}

export interface Form1099Response {
  tax_year: number
  candidates: Form1099Candidate[]
  data_quality: VendorDataQuality[]
  w9_collection_list: W9CollectionRow[]
  summary: Record<string, unknown>
}
