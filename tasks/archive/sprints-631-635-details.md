# Sprints 631–635 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-16.

---

### Sprint 631: Balance Sheet Assertion Completeness Checker
**Status:** COMPLETE
**Source:** Accounting Auditor — preflight capability gap
**File:** `backend/preflight_engine.py` extension
**Problem:** Classification validator checks individual accounts but does not assert population-level completeness — no engine verifies the uploaded TB has at least one account in each GAAP category (Assets/Liabilities/Equity/Revenue/Expenses) before downstream tools run.
**Changes:**
- [x] After classification, check all 5 categories have ≥1 mapped account
- [x] Emit preflight warning: "No [category] accounts detected — financial statement output will be incomplete"
- [x] Secondary check: Revenue > 0 but COGS = 0 → flag classification gap
- [x] Surface in preflight gate UI (via new `category_completeness` block on the preflight response; response schema wired for frontend consumption)

**Review:**
- Ran classifier inline in preflight (after column detection). `CategoryCompleteness` dataclass on `PreFlightReport`; `category_completeness` JSON block on the to_dict output and the Pydantic response schema.
- `category_completeness` added to `_CHECK_WEIGHTS` (10% weight); issues surface at high severity for missing categories, medium for the Revenue > 0 / COGS = 0 classification gap.
- COGS gap is skipped when no expense activity exists, so service-business TBs (no COGS) don't get false-positive warnings.
- Existing clean-file test updated to include all 5 GAAP categories; 5 new tests added covering complete TB, missing equity, COGS gap, service business no-op, and to_dict shape.
- All 27 preflight tests pass.
- Commit: bb0f794

---

### Sprint 632: Account Sequence Gap Detector
**Status:** COMPLETE
**Source:** Accounting Auditor — TB-only fraud signal not currently surfaced
**File:** new engine under `backend/audit/rules/`
**Problem:** Gaps in numeric account number sequences can reveal suppressed accounts. No existing tool surfaces this.
**Changes:**
- [x] Parse numeric component from account numbers, sort, detect gaps
- [x] Configurable tolerance (default: gap > cluster_step; cluster_step default 10)
- [x] Exclude category boundary gaps (1xxx→2xxx)
- [x] Integrate into Classification Validator output (new CV-4b check)
- [x] Test against fabricated TB with suppressed account ranges

**Review:**
- New `backend/audit/rules/gaps.py` with `detect_account_number_gaps()` and `AccountGap` dataclass.
- Cluster test: fires only when neighbours step by ≤ `cluster_step` (default 10) on both sides of the gap — excludes sparse numbering and isolated singletons.
- Category boundary detector (1xxx→2xxx) suppresses false positives at chart block boundaries.
- CV-4b `check_suspicious_sequence_gaps` integrated into `run_classification_validation`; complementary to CV-4's raw threshold check.
- 12 new tests cover sequential series, suppressed ranges (high/medium severity), boundary skip, isolated neighbours, cluster tuning, and validator integration. All 64 gap + validator tests pass.
- Commit: b2db2ec

---

### Sprint 633: Cash Flow Projector (30/60/90-Day)
**Status:** COMPLETE
**Source:** Future-State Consultant — missing catalog feature #16 (Strategic Bet, Priority 7/4)
**File:** new engine; reuses AR/AP aging parsers
**Problem:** Existing `financial_statement_builder.py` cash flow statement is historical indirect-method only. No forward-looking AR/AP-based projector. Operational finance teams need this.
**Changes:**
- [x] New `backend/cash_flow_projector_engine.py`
- [x] Inputs: AR aging, AP aging (both already parsed by existing engines), recurring cash flows, opening balance
- [x] Base/stress/best-case scenarios
- [x] Daily 30/60/90-day forecast (horizon summaries at 30, 60, 90)
- [x] Collection probability analysis, suggested AR priorities, AP deferral candidates
- [x] Route + CSV (PDF + Excel deferred to a follow-up sprint — mirrors Sprint 625's CSV-only ship)

**Review:**
- Engine produces 90 daily points per scenario, horizon summaries at 30/60/90 days, collection priorities ranked by at-risk amount, AP deferral candidates (empty under stress; populated under best).
- Scenarios: `base` / `stress` / `best` — each with independent collection-rate and AP-payment assumptions.
- Min-safe-cash threshold check flags breach per scenario.
- Route: `POST /audit/cash-flow-projector` returns JSON; `POST /audit/cash-flow-projector/export.csv` returns per-day per-scenario CSV.
- 13 new engine tests cover shape, horizon cumulative ordering, scenario ranking, opening-balance sensitivity, priority ranking, deferral candidates, min-safe-cash breach, input validation, assumption constants, and serialisation. All pass.
- PDF section and XLSX export deferred — they need the downstream section framework (same deferral reason as Sprint 625, tracked under Sprint 672-style follow-up).
- Commit: 7f3cff5

---

### Sprint 634: 1099 Preparation Helper
**Status:** COMPLETE
**Source:** Future-State Consultant — missing catalog feature #12
**File:** new engine + route
**Problem:** Not in any route or engine file. 1099 prep is annual pain point with intense Oct–Jan demand.
**Changes:**
- [x] New `backend/form_1099_engine.py` — aggregate AP payments by vendor, apply 1099 reporting rules, validate vendor data (TIN, address)
- [x] Output: 1099 candidate listing with amounts by box, data quality report, W-9 collection list
- [x] Route + CSV export (PDF deferred to a follow-up sprint alongside the downstream section framework)
- [ ] Seasonal marketing hook (release before October) — not in scope for engine sprint

**Review:**
- `form_1099_engine.py` implements NEC/MISC/INT filing thresholds ($600/$600/$10), corporation exemption (except medical/legal), processor-reported exclusion (credit card / PayPal), per-vendor aggregation, data-quality report, W-9 collection list.
- 13 standard adjustments pre-populated in the catalog with codes, descriptions, direction defaults.
- Route: `POST /audit/form-1099` returns full result; `POST /audit/form-1099/export.csv` for filing-ready CSV.
- 18 new tests cover thresholds, corporation exemption, medical/legal carve-out, processor exclusion, aggregation across categories, data-quality flags, W-9 list, summary aggregation, input validation, and serialisation. All pass.
- Backend imports 231 routes.
- Commit: da24cdb

---

### Sprint 635: Book-to-Tax Adjustment Calculator
**Status:** COMPLETE
**Source:** Future-State Consultant — missing catalog feature #13
**File:** new engine + route
**Problem:** Not present. M-1/M-3, UNICAP, meals/entertainment — none implemented.
**Changes:**
- [x] New `backend/book_to_tax_engine.py` — permanent differences (meals 50%, fines, life insurance, tax-exempt interest, political, DRD), temporary differences (depreciation, bad debt, prepaids, accrued vacation, UNICAP, stock comp, warranty reserve)
- [x] M-1/M-3 formatted output based on entity size (entity_size gated on $10M total assets per IRS Schedule M-3 threshold)
- [x] Deferred tax asset/liability rollforward
- [x] Route + CSV (PDF deferred to the downstream section framework follow-up)

**Review:**
- Engine accepts pretax book income + adjustment list, produces Schedule M-1, Schedule M-3 (income vs expense columns, permanent vs temporary split), deferred tax rollforward, and a tax provision with effective rate.
- 13 standard adjustment codes pre-populated in `STANDARD_ADJUSTMENTS`; frontend can pull via `GET /audit/book-to-tax/standard-adjustments`.
- DTA/DTL rollforward: positive net temporary → DTA; negative consumes DTA first, spills to DTL.
- Route: `POST /audit/book-to-tax` (full JSON), `POST /audit/book-to-tax/export.csv` (M-1 + rollforward + provision).
- 18 new engine tests cover M-1 reconciliation, M-3 column split, entity-size threshold, DTA build, DTA→DTL spillover, rollforward onto existing balances, provision math, effective rate, state tax overlay, input validation, catalog exposure, and serialisation. All pass; backend imports 232 routes.

Also archives sprints 631–635 to clear the archival gate (threshold reached after this commit).

---
