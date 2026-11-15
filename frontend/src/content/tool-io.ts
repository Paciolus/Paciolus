/**
 * What each tool takes and what it gives — Sprint 866 (reports/website-review-2026-11-14.md S-04).
 *
 * Every row was established from the code on 2026-11-15, not from marketing
 * copy; the evidence comment on each row names where. When a tool's upload
 * columns, tests or exports change, change its row here.
 *
 * "One file" tools accept any of the upload formats the platform supports;
 * tools marked "parsed in your browser" accept CSV/TSV/TXT only.
 */

export interface ToolIO {
  /** Matches `id` in content/tool-ledger.ts. */
  id: string
  input: string
  does: string
  outputs: string
}

export const TOOL_IO: ToolIO[] = [
  // backend/column_detector.py:214-224; backend/audit/__init__.py:7-14; backend/pdf/orchestrator.py:110-135
  { id: 'trial_balance', input: 'One trial balance file with Debit and Credit columns (the account is taken from the first column if not named).', does: 'Checks the trial balance balances, classifies accounts, runs anomaly rules and assigns risk tiers.', outputs: 'Diagnostic PDF memo; financial statements (PDF and Excel); lead sheets; CSV extracts.' },
  // backend/routes/multi_period.py:88-93; backend/multi_period_comparison.py:4-9
  { id: 'multi_period', input: 'Prior and current trial balances, plus an optional budget, in the same format as Trial Balance Diagnostics.', does: 'Compares two or three trial balances account by account: movements, new and closed accounts, sign changes, significant variances.', outputs: 'PDF memo; CSV of movements, lead-sheet summary and summary statistics.' },
  // backend/bank_reconciliation.py:219-231
  { id: 'bank_reconciliation', input: 'A bank statement and a ledger file, each with Date and Amount columns.', does: 'Matches bank transactions to ledger entries, including split matches, and lists outstanding deposits and checks.', outputs: 'PDF memo; CSV of matched items, split matches, outstanding deposits and checks, and a summary.' },
  // backend/three_way_match_engine.py:317-392
  { id: 'three_way_match', input: 'Purchase-order, invoice and receipt files (PO number, vendor and amounts; quantity received on receipts).', does: 'Matches the three documents by PO number, with a fuzzy fallback, and computes variances.', outputs: 'PDF memo; CSV of match results with a summary.' },
  // backend/services/audit/je_testing/analysis.py:327-341; backend/tools_registry.py:94
  { id: 'journal_entry_testing', input: 'One general-ledger file with Account, a date, and Debit/Credit or Amount columns.', does: 'Runs 19 tests on the file; some need a minimum number of entries.', outputs: 'PDF memo (including a Benford’s Law section where the data supports it); CSV of flagged entries.' },
  // backend/services/audit/ap_testing/analysis.py:316-347; backend/tools_registry.py:104
  { id: 'ap_testing', input: 'One payments file with Payment Date, Vendor Name and Amount columns.', does: 'Runs 14 tests over the payments.', outputs: 'PDF memo (including duplicate-payment detail); CSV of flagged payments.' },
  // backend/services/audit/revenue_testing/analysis.py:287-312; backend/tools_registry.py:114
  { id: 'revenue_testing', input: 'One revenue ledger file with Date and Amount columns; contract fields are optional.', does: 'Runs 18 tests, four of which use the optional contract fields.', outputs: 'PDF memo; CSV of flagged entries.' },
  // backend/services/audit/ar_aging/analysis.py:648-670; backend/tools_registry.py:124
  { id: 'ar_aging', input: 'A trial balance, plus an optional AR sub-ledger with an Amount column.', does: 'Runs 12 tests.', outputs: 'PDF memo (including an aging schedule); CSV of flagged items.' },
  // backend/services/audit/payroll_testing/analysis.py:272-288; backend/tools_registry.py:134
  { id: 'payroll_testing', input: 'One payroll file with Employee Name, Pay Date and Gross Pay columns.', does: 'Runs 13 tests.', outputs: 'PDF memo (including a headcount roll-forward); CSV of flagged employees.' },
  // backend/services/audit/fixed_asset_testing/analysis.py:247-259; backend/tools_registry.py:144
  { id: 'fixed_asset_testing', input: 'One asset register with a Cost column and an Asset ID or Description.', does: 'Runs 11 tests.', outputs: 'PDF memo (including a roll-forward); CSV of flagged assets.' },
  // backend/services/audit/inventory_testing/analysis.py:238-254; backend/tools_registry.py:154
  { id: 'inventory_testing', input: 'One inventory file with Quantity, Unit Cost or Extended Value, and an Item ID or Description.', does: 'Runs 10 tests.', outputs: 'PDF memo; CSV of flagged items.' },
  // backend/sampling_engine.py:5-13,246; backend/routes/export_testing.py:425
  { id: 'statistical_sampling', input: 'A population file with an Amount column; for evaluation, recorded and audited amounts.', does: 'Computes a monetary-unit or random sample size and selection, and evaluates errors with a Stringer upper bound.', outputs: 'Design and evaluation PDF memos; CSV of selected items with a blank Audited Amount column.' },
  // frontend/src/components/sod/parseCsv.ts:88-94,125-130; backend/sod_engine.py:4-6; backend/routes/sod.py:192
  { id: 'sod_checker', input: 'A users file and a roles file (CSV, parsed in your browser).', does: 'Checks each user’s effective permissions against a conflict-rule library and ranks users by risk.', outputs: 'CSV of user risk and conflicts. No PDF memo.' },
  // frontend/src/components/intercompany/parseCsv.ts:111-118; backend/intercompany_elimination_engine.py:4-10
  { id: 'intercompany_elimination', input: 'One file of entity balances, at least two entities (CSV, parsed in your browser).', does: 'Builds a consolidation worksheet with elimination entries and lists mismatched intercompany pairs.', outputs: 'CSV of the worksheet, elimination entries and mismatches. No PDF memo.' },
  // frontend/src/components/w2Reconciliation/parseCsv.ts:97-98; backend/w2_reconciliation_engine.py:4-10
  { id: 'w2_reconciliation', input: 'Payroll year-to-date, with optional draft W-2s and Form 941s (CSV, parsed in your browser).', does: 'Reconciles payroll to the draft W-2s and quarterly 941s and checks wage bases and plan limits.', outputs: 'CSV of discrepancies and W-3 totals. No PDF memo.' },
  // frontend/src/components/form1099/parseCsv.ts:117-127; backend/form_1099_engine.py:4-8
  { id: 'form_1099', input: 'A vendor file and a payments file (CSV, parsed in your browser).', does: 'Totals payments by vendor for the tax year, applies the 1099 thresholds and flags missing TINs or addresses.', outputs: 'CSV of 1099 candidates and vendors below threshold. No PDF memo.' },
  // backend/routes/book_to_tax.py:48-68; backend/book_to_tax_engine.py:4-7
  { id: 'book_to_tax', input: 'Form entry, no file: book income, tax rates and the list of adjustments.', does: 'Classifies adjustments as permanent or temporary and produces Schedule M-1/M-3 and a deferred-tax roll-forward.', outputs: 'CSV of the schedules and the roll-forward. No PDF memo.' },
  // backend/routes/cash_flow_projector.py:42-64; backend/cash_flow_projector_engine.py:4-7
  { id: 'cash_flow_projector', input: 'Form entry, no file: opening cash, AR and AP aging, and recurring flows.', does: 'Projects cash over 30, 60 and 90 days in base, stress and best scenarios.', outputs: 'CSV of the projection by scenario and day. No PDF memo.' },
]
