/**
 * Intercompany Elimination — Sprint 689c.
 *
 * Shapes mirror backend/routes/intercompany_elimination.py Pydantic
 * contracts and backend/intercompany_elimination_engine.py dataclasses.
 *
 * Decimal fields serialize as strings on the wire (Pydantic accepts
 * numeric strings; engine emits `str(Decimal)` via `.to_dict()`).
 */

export type IntercompanyDirection =
  | 'receivable'
  | 'payable'
  | 'revenue'
  | 'expense'
  | 'investment'
  | 'other'

export type MismatchKind = 'no_reciprocal' | 'amount_mismatch' | 'direction_mismatch'

export interface IntercompanyEntityAccountRequest {
  account: string
  debit: string
  credit: string
  counterparty_entity: string | null
}

export interface IntercompanyEntityTBRequest {
  entity_id: string
  entity_name: string
  accounts: IntercompanyEntityAccountRequest[]
}

export interface IntercompanyEliminationRequest {
  entities: IntercompanyEntityTBRequest[]
  tolerance: string
}

export interface IntercompanyLine {
  entity_id: string
  account: string
  direction: IntercompanyDirection | string
  counterparty_entity: string | null
  net_balance: string
  debit: string
  credit: string
}

export interface EliminationPair {
  entity_a: string
  entity_b: string
  account_a: string
  account_b: string
  direction_a: string
  direction_b: string
  amount_a: string
  amount_b: string
  net_residual: string
  reconciles: boolean
}

export interface IntercompanyMismatch {
  kind: MismatchKind
  entity: string
  counterparty: string | null
  account: string
  direction: string
  amount: string
  message: string
}

export interface EliminationJE {
  description: string
  debit_entity: string
  debit_account: string
  credit_entity: string
  credit_account: string
  amount: string
}

export interface ConsolidationColumn {
  entity_id: string
  entity_name: string
  debit_total: string
  credit_total: string
  intercompany_gross: string
}

export interface ConsolidationWorksheet {
  columns: ConsolidationColumn[]
  total_entity_debits: string
  total_entity_credits: string
  elimination_debits: string
  elimination_credits: string
  consolidated_debits: string
  consolidated_credits: string
}

export interface IntercompanyEliminationSummary {
  entity_count?: number
  intercompany_line_count?: number
  matched_pair_count?: number
  reconciling_pair_count?: number
  mismatch_count?: number
  elimination_je_count?: number
  consolidation_complete?: boolean
  [key: string]: unknown
}

export interface IntercompanyEliminationResponse {
  intercompany_lines: IntercompanyLine[]
  pairs: EliminationPair[]
  mismatches: IntercompanyMismatch[]
  elimination_journal_entries: EliminationJE[]
  worksheet: ConsolidationWorksheet
  summary: IntercompanyEliminationSummary
}
