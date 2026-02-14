/**
 * Bank Reconciliation Types (Sprint 78)
 *
 * Mirrors backend BankRecResult.to_dict() shape exactly.
 */

// =============================================================================
// ENUMS & CONSTANTS
// =============================================================================

export type MatchType = 'matched' | 'bank_only' | 'ledger_only'

export const MATCH_TYPE_LABELS: Record<MatchType, string> = {
  matched: 'Matched',
  bank_only: 'Bank Only',
  ledger_only: 'Ledger Only',
}

export const MATCH_TYPE_COLORS: Record<MatchType, string> = {
  matched: 'bg-sage-50 text-sage-700 border-sage-200',
  bank_only: 'bg-clay-50 text-clay-700 border-clay-200',
  ledger_only: 'bg-oatmeal-100 text-oatmeal-700 border-oatmeal-300',
}

export const MATCH_TYPE_BORDER_COLORS: Record<MatchType, string> = {
  matched: 'border-l-sage-500',
  bank_only: 'border-l-clay-500',
  ledger_only: 'border-l-oatmeal-500',
}

// =============================================================================
// TRANSACTION DATA
// =============================================================================

export interface BankTransactionData {
  date: string | null
  description: string
  amount: number
  reference: string | null
  row_number: number
}

export interface LedgerTransactionData {
  date: string | null
  description: string
  amount: number
  reference: string | null
  row_number: number
}

// =============================================================================
// MATCH DATA
// =============================================================================

/** Discriminated union by match_type — Sprint 226
 *  - 'matched': both transactions present
 *  - 'bank_only': bank transaction only (outstanding item)
 *  - 'ledger_only': ledger transaction only (in-transit item)
 */
export type ReconciliationMatchData =
  | { match_type: 'matched'; bank_txn: BankTransactionData; ledger_txn: LedgerTransactionData; match_confidence: number }
  | { match_type: 'bank_only'; bank_txn: BankTransactionData; ledger_txn?: never; match_confidence: number }
  | { match_type: 'ledger_only'; bank_txn?: never; ledger_txn: LedgerTransactionData; match_confidence: number }

// =============================================================================
// SUMMARY
// =============================================================================

export interface ReconciliationSummaryData {
  matched_count: number
  matched_amount: number
  bank_only_count: number
  bank_only_amount: number
  ledger_only_count: number
  ledger_only_amount: number
  reconciling_difference: number
  total_bank: number
  total_ledger: number
  matches: ReconciliationMatchData[]
}

// =============================================================================
// COLUMN DETECTION
// =============================================================================

export interface BankColumnDetectionData {
  date_column: string | null
  amount_column: string | null
  description_column: string | null
  reference_column: string | null
  balance_column: string | null
  overall_confidence: number
  requires_mapping: boolean
  all_columns: string[]
  detection_notes: string[]
}

// =============================================================================
// TOP-LEVEL RESULT
// =============================================================================

export interface BankRecResult {
  summary: ReconciliationSummaryData
  bank_column_detection: BankColumnDetectionData
  ledger_column_detection: BankColumnDetectionData
}
