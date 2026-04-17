# Sprints 636–640 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-16.

---

### Sprint 636: W-2/W-3 Reconciliation Tool
**Status:** COMPLETE
**Source:** Future-State Consultant — missing catalog feature #14
**File:** new engine + route
**Problem:** Not present. Payroll testing tests data integrity, not W-2 reconciliation. W-2 errors create amended filings + penalties.
**Changes:**
- [x] New `backend/w2_reconciliation_engine.py` — reconcile payroll system → draft W-2 → quarterly 941s
- [x] Validate SS wage base, HSA, retirement plan limits (including age-50 catch-up and 60–63 Secure 2.0 super-catch-up)
- [x] Employee-level discrepancy report
- [x] Route + CSV (PDF deferred)

**Review:**
- Engine enforces 2026 reference limits (SS wage base $176,100, 401(k) $23,500 + age-based catch-ups, HSA $4,300/$8,550, SIMPLE IRA $16,500, additional Medicare threshold $200k at 0.9%). All thresholds are caller-overridable via `W2ReconciliationConfig`.
- Checks: box 1/2/3/4/5/6 reconciliation to payroll; SS wage base cap; HSA over-limit per coverage level; 401(k)/SIMPLE IRA elective limit with age-aware catch-up; additional Medicare threshold-crossed informational; Form 941 4-quarter sum vs payroll YTD.
- W-3 totals = sum of every W-2 draft, returned as its own block.
- Missing W-2 draft falls back to a self-consistent payroll-derived draft so limit checks still fire.
- Route: `POST /audit/w2-reconciliation`, `POST /audit/w2-reconciliation/export.csv`.
- 19 new tests cover happy path, SS wage base cap + mismatch, Medicare standard vs additional, HSA self-only/family/none, 401(k) + catch-up + super-catch-up + SIMPLE IRA limits, 941 matching and divergence, W-3 totals, input validation, missing-draft self-consistency fallback, and serialisation. Backend imports 234 routes.
- Commit: 087393e

---

### Sprint 637: Multi-Entity Intercompany Elimination
**Status:** COMPLETE
**Source:** Future-State Consultant — partial catalog feature #11
**File:** new engine (`backend/intercompany_elimination_engine.py`) + route; single-TB detection in `audit/rules/relationships.py` left intact
**Problem:** Existing single-TB intercompany imbalance detection exists. Missing: multi-entity TB input, elimination JE generation, consolidation worksheet.
**Changes:**
- [x] Accept multiple TB uploads in one session (≥2, ≤50 entities)
- [x] Extract intercompany balances per entity, match reciprocal pairs
- [x] Calculate elimination JEs
- [x] Flag timing/currency/error imbalances (amount mismatch, direction mismatch, no-reciprocal)
- [x] Consolidation worksheet output (pre-elim, elim, post-elim)

**Review:**
- New `backend/intercompany_elimination_engine.py` — standalone from `relationships.py` so the single-TB rule keeps its existing contract.
- Direction parser recognises "Due from", "Due to", "Intercompany revenue/expense", "Investment in subsidiary", management-fee variants, and the generic "intercompany" token.
- Counterparty parser: uses explicit `counterparty_entity` if provided, else extracts from "Due from X" / "Intercompany — X" patterns; falls back to a NO_RECIPROCAL mismatch when the parsed name doesn't match any entity in the consolidation.
- Reciprocal direction map: receivable↔payable, revenue↔expense; UNKNOWN matches any; direction mismatch surfaces as its own mismatch kind.
- Tolerance-based reconciliation: residual ≤ $1.00 default tolerance reconciles the pair; above tolerance fires AMOUNT_MISMATCH.
- Elimination JEs generated only for reconciling pairs (practitioner must fix mismatches first).
- Consolidation worksheet: per-entity columns, pre-elimination totals, elimination sum, post-elimination consolidated.
- Route: `POST /audit/intercompany-elimination`, `POST /audit/intercompany-elimination/export.csv`.
- 13 new engine tests cover happy path, direction parsing, no-reciprocal, amount mismatch, tolerance absorbing small residuals, worksheet shape, 3-entity consolidation, input validation (single-entity, duplicate IDs), counterparty parsing from account names, serialisation. Backend imports 236 routes.
- Commit: 013d593

---

### Sprint 638: Statement Of Changes In Equity
**Status:** COMPLETE
**Source:** Future-State Consultant — partial catalog feature #7
**File:** `backend/financial_statement_builder.py:275`
**Problem:** TB → Financial Statements mapper builds BS, IS, Cash Flow. Statement of Changes in Equity is missing from spec output.
**Changes:**
- [x] Extend `financial_statement_builder.py` to generate equity rollforward from TB equity accounts
- [x] Explicit unmapped-accounts report alongside the mapping trace
- [ ] Include in PDF financial statement package — PDF section deferred to downstream section-framework follow-up (same deferral rationale as Sprints 633–637)

**Review:**
- New `EquityComponent`, `StatementOfChangesInEquity`, and `EquityActivity` dataclasses.
- `_build_soce()` classifies every equity account on lead sheet K into one of common_stock / additional_paid_in_capital / retained_earnings / treasury_stock / aoci via keyword match (27 rules, deterministic first-wins). Unknown accounts default to retained_earnings AND surface on `unmapped_accounts` so the practitioner can confirm or reclassify.
- Rollforward: beginning from prior-period K accounts (matched by case-insensitive name), net income flows into retained earnings, explicit `EquityActivity` inputs set contributions / distributions / dividends, residual drops into `other_movement` so the rollforward balances. AOCI movement captured on its own column.
- Components emitted in canonical SOCE order: common → APIC → retained → treasury → AOCI.
- 11 new tests; 57 existing FSB / cash-flow / balance-sheet tests unchanged. Full suite: 68 passed.
- Commit: c3f613c

---

### Sprint 639: Bank Reconciliation One-to-Many + Suggested JEs
**Status:** COMPLETE
**Source:** Future-State Consultant — partial catalog feature #2
**File:** `backend/bank_reconciliation.py:399-518, 1201`
**Problem:** V1 exact + tolerance matching only. No one-to-many matching (one bank txn → multiple GL entries). No suggested JE templates for common reconciling items (fees, interest, bank charges).
**Changes:**
- [x] Add split-matching pass after greedy pass
- [x] Emit `suggested_journal_entries` field on `BankRecResult` for BANK_ONLY items classified as fees/interest
- [x] Tests for split-match scenarios

**Review:**
- New `MatchType.SPLIT` variant and `ledger_txns: list` field on `ReconciliationMatch` for one-to-many matches.
- `_split_match_pass()` runs after the greedy exact-match pass. For each remaining BANK_ONLY item, it searches combinations of 2–4 date-windowed LEDGER_ONLY candidates whose sum reconciles within amount tolerance. When found, the BANK_ONLY promotes to SPLIT and the sibling LEDGER_ONLY entries are consumed.
- `SuggestedJE` + `SuggestedJEKind` enum: BANK_FEE / INTEREST_INCOME / INTEREST_EXPENSE / NSF_CHARGE / WIRE_FEE / SERVICE_CHARGE / OVERDRAFT / OTHER.
- `generate_suggested_journal_entries()` scans only BANK_ONLY items (LEDGER_ONLY are already booked). Keyword classifier with word-boundary guard for short tokens (fixes "nsf" false-matching "tra*nsf*er").
- `BankRecResult.suggested_journal_entries` populated by `run_bank_reconciliation()`; serialised on `to_dict()` when non-empty.
- 12 new tests cover 2/3-way splits, tolerance enforcement, date-window respect, greedy-preferred-over-split, NSF / interest / wire / service classification, unmatched vendor payment not classified, matched items not suggested, serialisation.
- Regression: 128 existing bank rec tests unchanged. Full bank rec suite: 140 passed.
- Commit: 1675364

---

### Sprint 640: Budget vs Actual Favorable/Unfavorable Classification
**Status:** COMPLETE
**Source:** Future-State Consultant — partial catalog feature #8
**File:** `backend/multi_period_comparison.py:707-934`
**Problem:** Computes variance amount/percent but never classifies favorable/unfavorable. Opposite signs mean different things for revenue vs expense — expense underage is favorable, revenue underage is unfavorable. Currently ambiguous.
**Changes:**
- [x] Add `variance_direction: Literal["favorable" | "unfavorable" | "on_budget" | "neutral"]` derived from account category + sign
- [x] Add `commentary_prompt` field for `SignificanceTier.MATERIAL` movements (this codebase's top tier; the sprint brief's "CRITICAL" name doesn't exist here)
- [x] Extend response schema and engine output; PDF follow-up deferred with the rest of the section-framework work

**Review:**
- `_classify_variance_direction()` consolidates the sign interpretation: for Revenue, COGS, Operating Expenses, and Other Income / Expense categories, favorable = raw variance < 0 (revenue exceeded budget OR spend below budget); unfavorable when > 0; `on_budget` within $0.01. Balance-sheet categories (Assets, Liabilities, Equity) return `neutral` — favorability is engagement-dependent.
- `_commentary_prompt()` emits a practitioner prompt that names the account + category + direction and asks the user to document the driver (timing, estimate change, one-time item, run-rate shift) and supporting evidence.
- `BudgetVariance` gains `variance_direction` (default `neutral`) and optional `commentary_prompt`. Commentary prompt only set when the variance tier is MATERIAL.
- `BudgetVarianceResponse` Pydantic schema updated with both fields so API consumers see the new columns.
- 14 new tests cover revenue/expense/COGS direction logic, balance-sheet neutral, on-budget tolerance, unknown category, commentary-prompt shape, serialisation behaviour (only present when set). 178 existing multi-period tests unchanged; full suite: 192 passed.

---
