/**
 * Three-Way Match Validator Types (Sprint 93)
 *
 * Mirrors backend ThreeWayMatchResult.to_dict() shape exactly.
 */

import type { Severity } from './shared'

// =============================================================================
// ENUMS & CONSTANTS
// =============================================================================

export type TWMMatchType = 'exact_po' | 'fuzzy' | 'partial'
/** Diagnostic risk level for TWM (3-tier, distinct from TestingRiskTier's 5-tier scale). */
export type TWMRiskLevel = 'low' | 'medium' | 'high'

export const MATCH_TYPE_LABELS: Record<TWMMatchType, string> = {
  exact_po: 'Exact PO#',
  fuzzy: 'Fuzzy Match',
  partial: 'Partial Match',
}

export const MATCH_TYPE_COLORS: Record<TWMMatchType, string> = {
  exact_po: 'bg-sage-50 text-sage-700 border-sage-200',
  fuzzy: 'bg-oatmeal-100 text-oatmeal-700 border-oatmeal-300',
  partial: 'bg-clay-50 text-clay-700 border-clay-200',
}

export const VARIANCE_SEVERITY_COLORS: Record<Severity, string> = {
  high: 'bg-clay-50 text-clay-700 border-clay-200',
  medium: 'bg-oatmeal-100 text-oatmeal-700 border-oatmeal-300',
  low: 'bg-sage-50 text-sage-700 border-sage-200',
}

export const RISK_COLORS: Record<TWMRiskLevel, string> = {
  low: 'text-sage-600',
  medium: 'text-oatmeal-700',
  high: 'text-clay-600',
}

export const RISK_BG_COLORS: Record<TWMRiskLevel, string> = {
  low: 'bg-sage-50 border-sage-200',
  medium: 'bg-oatmeal-100 border-oatmeal-300',
  high: 'bg-clay-50 border-clay-200',
}

// =============================================================================
// DOCUMENT DATA
// =============================================================================

export interface POData {
  po_number: string | null
  vendor: string
  description: string
  quantity: number
  unit_price: number
  total_amount: number
  order_date: string | null
  expected_delivery: string | null
  approver: string | null
  department: string | null
  row_number: number
}

export interface InvoiceData {
  invoice_number: string | null
  po_reference: string | null
  vendor: string
  description: string
  quantity: number
  unit_price: number
  total_amount: number
  invoice_date: string | null
  due_date: string | null
  row_number: number
}

export interface ReceiptData {
  receipt_number: string | null
  po_reference: string | null
  invoice_reference: string | null
  vendor: string
  description: string
  quantity_received: number
  receipt_date: string | null
  received_by: string | null
  condition: string | null
  row_number: number
}

// =============================================================================
// MATCH DATA
// =============================================================================

export interface MatchVarianceData {
  field: string
  po_value: number | null
  invoice_value: number | null
  receipt_value: number | null
  variance_amount: number
  variance_pct: number
  severity: Severity
}

export interface ThreeWayMatchData {
  po: POData | null
  invoice: InvoiceData | null
  receipt: ReceiptData | null
  match_type: TWMMatchType
  match_confidence: number
  variances: MatchVarianceData[]
}

export interface UnmatchedDocumentData {
  document: Record<string, unknown>
  document_type: string
  reason: string
}

// =============================================================================
// SUMMARY
// =============================================================================

export interface ThreeWayMatchSummaryData {
  total_pos: number
  total_invoices: number
  total_receipts: number
  full_match_count: number
  partial_match_count: number
  full_match_rate: number
  partial_match_rate: number
  total_po_amount: number
  total_invoice_amount: number
  total_receipt_amount: number
  net_variance: number
  material_variances_count: number
  risk_assessment: TWMRiskLevel
}

// =============================================================================
// DATA QUALITY
// =============================================================================

export interface ThreeWayMatchDataQuality {
  po_count: number
  invoice_count: number
  receipt_count: number
  po_vendor_fill_rate: number
  po_amount_fill_rate: number
  po_number_fill_rate: number
  invoice_vendor_fill_rate: number
  invoice_amount_fill_rate: number
  invoice_number_fill_rate: number
  invoice_po_ref_fill_rate: number
  receipt_vendor_fill_rate: number
  receipt_qty_fill_rate: number
  receipt_po_ref_fill_rate: number
  overall_quality_score: number
  detected_issues: string[]
}

// =============================================================================
// COLUMN DETECTION
// =============================================================================

export interface ColumnDetectionData {
  overall_confidence: number
  requires_mapping: boolean
  all_columns: string[]
  detection_notes: string[]
  [key: string]: unknown
}

// =============================================================================
// TOP-LEVEL RESULT
// =============================================================================

export interface ThreeWayMatchResult {
  full_matches: ThreeWayMatchData[]
  partial_matches: ThreeWayMatchData[]
  unmatched_pos: UnmatchedDocumentData[]
  unmatched_invoices: UnmatchedDocumentData[]
  unmatched_receipts: UnmatchedDocumentData[]
  summary: ThreeWayMatchSummaryData
  variances: MatchVarianceData[]
  data_quality: ThreeWayMatchDataQuality
  column_detection: {
    po: ColumnDetectionData
    invoice: ColumnDetectionData
    receipt: ColumnDetectionData
  }
  config: Record<string, unknown>
}
