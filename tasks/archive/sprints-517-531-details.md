# Sprints 517–531 Details

> Archived from `tasks/todo.md` Active Phase on 2026-03-11.

---

### Sprint 531 — DEC 2026-03-11 Remediation (15 Findings)

**Status:** COMPLETE
**Goal:** Fix all 15 findings from Digital Excellence Council audit 2026-03-11.

#### Accounting Methodology (F-001 through F-006)
- [x] F-001: Added `CONTRA_LIABILITY_KEYWORDS` + LIABILITY branch in `is_contra_account()` — bond discounts, debt issuance costs now recognized
- [x] F-002: Removed AOCI entries from `CONTRA_EQUITY_KEYWORDS` — AOCI is not consistently contra-equity
- [x] F-003: Removed bare "non-operating"/"nonoperating" from `_CSV_TYPE_MAP` — prevents misclassifying non-operating income as expense
- [x] F-004: Added `("management fee", 0.90, True)` to `RELATED_PARTY_KEYWORDS`
- [x] F-005: Removed "sundry" (weight 0.60 = threshold) from `SUSPENSE_KEYWORDS` — false positives on Commonwealth accounts
- [x] F-006: Removed "float" (weight 0.55 < threshold 0.60) from `SUSPENSE_KEYWORDS` — dead code

#### CI Coverage Enforcement (F-008, F-009)
- [x] F-008: Added `--cov-fail-under=60` to pytest CI step
- [x] F-009: Added `--coverage` flag to Jest CI step

#### Consistency & Patterns (F-007, F-010, F-013)
- [x] F-007: Added `credentials: 'include'` to `uploadTransport.ts` fetch call
- [x] F-010: Added `as const` to `mobileItemVariants` and `mobileContainerVariants` in MarketingNav
- [x] F-013: Added "direct cost" (singular) to `_COGS_SUBTYPES` in ratio_engine

#### Observability (F-012)
- [x] F-012: Removed hot-path `[DEPLOY-VERIFY-530]` logger.info from `is_contra_account()` — fires on every call

#### Documentation / Info (F-011, F-014, F-015)
- [x] F-011: framer-motion `as const` pattern — addressed by F-010 fix
- [x] F-014: Informational — no code change needed
- [x] F-015: Informational — no code change needed

#### Verification
- [x] `pytest` — 6,507 passed (0 failures)
- [x] `npm run build` passes
- [x] `npm test` — 1,339 passed (0 failures)

**Review:** 13 code fixes across 7 files. Key changes: contra-liability recognition (F-001), AOCI removal from contra-equity (F-002), bare non-operating CSV type removal (F-003), management fee related-party keyword (F-004), suspense keyword cleanup (F-005/F-006), upload transport credentials (F-007), CI coverage gates (F-008/F-009), framer-motion as const (F-010), deploy-verify log removal (F-012), COGS subtype singular form (F-013). Test updates: removed 2 AOCI contra-equity parametrize entries, added 3 contra-liability tests, removed 2 bare non-operating CSV type test entries.


---

### Sprint 527 — DEC 2026-03-10 P2 Remediation (6 findings)

**Status:** COMPLETE
**Goal:** Remediate 6 P2 findings from the Digital Excellence Council audit dated 2026-03-10.

#### F-001: Detection Keywords Hardcoded in StreamingAuditor
- [x] Added `RELATED_PARTY_KEYWORDS`, `INTERCOMPANY_KEYWORDS`, `EQUITY_RETAINED_EARNINGS_KEYWORDS`, `EQUITY_DIVIDEND_KEYWORDS`, `EQUITY_TREASURY_KEYWORDS` to `classification_rules.py` using `(keyword, weight, is_phrase)` 3-tuple format
- [x] Imported and used in `audit_engine.py` — removed class-level `_RELATED_PARTY_KEYWORDS` and `_INTERCOMPANY_KEYWORDS`
- [x] Updated `detect_equity_signals()` to use imported keyword lists instead of inline string checks
- [x] 44 anomaly tests pass

#### F-002: Concentration Benchmark Thresholds Inconsistent
- [x] Added `REVENUE_CONCENTRATION_THRESHOLD` (0.30) and `EXPENSE_CONCENTRATION_THRESHOLD` (0.40) to `classification_rules.py`
- [x] `audit_engine.py` `detect_revenue_concentration()` and `detect_expense_concentration()` use imported thresholds
- [x] `tb_diagnostic_constants.py` `CONCENTRATION_BENCHMARKS` uses f-strings referencing the imported constants
- [x] 134 diagnostic tests pass

#### F-003: `_standard_table_style()` Still Duplicated
- [x] Added `standard_table_style()` to `shared/memo_base.py` using `ledger_table_style()` as base
- [x] Replaced local `_standard_table_style()` in `accrual_completeness_memo.py`, `expense_category_memo.py`, `population_profile_memo.py` with aliases to shared function
- [x] 44 expense category memo tests pass

#### F-004: Wide Type Intersection Cast — Missing `AuditResultResponse`
- [x] Added `AuditResultResponse` interface to `types/diagnostic.ts` extending `AuditResult`
- [x] Replaced inline cast in `useTrialBalanceUpload.ts` line 201 with named type
- [x] Removed unused `ColumnDetectionInfo` import
- [x] `npm run build` passes

#### F-005: No Unit Tests for uploadTransport.ts
- [x] Created `frontend/src/__tests__/uploadTransport.test.ts` with 10 tests
- [x] Tests: successful upload, 401, 403 EMAIL_NOT_VERIFIED, 403 generic, 500, network failure, header injection, null token, null CSRF, 403 JSON parse failure
- [x] 10/10 tests pass

#### F-006: Post-Processor Missing Defensive Checks
- [x] `apply_lead_sheet_grouping()`: added `logger.warning()` to existing early return
- [x] `apply_currency_conversion()`: added defensive `if "accounts" not in result` check with `logger.warning()`
- [x] 134 diagnostic tests pass

#### Verification
- [x] `pytest tests/test_audit_anomalies.py` — 44 passed
- [x] `pytest tests/test_expense_category_memo.py` — 44 passed
- [x] `pytest tests/ -k "post_processor or diagnostic"` — 134 passed
- [x] `npm run build` passes
- [x] `npx jest --testPathPatterns uploadTransport --no-coverage` — 10 passed


---

### Sprint 517 — Memo Generator Test Coverage (DEC F-018)

**Status:** COMPLETE
**Goal:** Add dedicated test files for the 5 memo generators that lack deep coverage.
**Context:** DEC 2026-03-08 finding F-018. 13 other memo generators have dedicated tests; these 5 were enriched in Sprints 489–500 but tests were not expanded. `engagement_dashboard_memo.py` has zero test coverage.

- [x] `tests/test_ap_testing_memo.py` — 24 tests (risk tiers, 13 test descriptions, drill-down tables, DPO metric, guardrails)
- [x] `tests/test_je_testing_memo.py` — 27 tests (risk tiers, 9 test descriptions, Benford's Law, high-severity detail, guardrails)
- [x] `tests/test_payroll_testing_memo.py` — 34 tests (risk tiers, 11 test descriptions, GL reconciliation, headcount roll-forward, Benford, department summary, guardrails)
- [x] `tests/test_preflight_memo.py` — 29 tests (score breakdown, TB balance check, column detection, data quality, FASB/GASB framework, guardrails)
- [x] `tests/test_engagement_dashboard_memo.py` — 23 tests (risk tiers, report summary, cross-report risk threads, priority actions, edge cases, guardrails)
- [x] `pytest` passes — 137 tests across 5 files
- [x] Pattern: follows `test_bank_rec_memo.py` / `test_sampling_memo.py` structure


---

### Sprint 518 — OpenAPI Schema Drift Detection (DEC F-020)

**Status:** COMPLETE
**Goal:** Add a CI job that detects schema drift between backend OpenAPI spec and committed snapshot.
**Context:** DEC 2026-03-08 finding F-020 (P3, systemic). 34 commits changed backend schemas and frontend types independently with no automated sync verification.

- [x] Create `scripts/generate_openapi_snapshot.py` — extracts OpenAPI spec from FastAPI app
- [x] Create `scripts/check_openapi_drift.py` — compares live spec against committed snapshot
- [x] Generate initial snapshot (`scripts/openapi-snapshot.json` — 309 schemas, 159 paths)
- [x] Add `openapi-drift-check` CI job to `.github/workflows/ci.yml`
- [x] Drift detection tested locally — detects added/removed/changed fields, type changes, required/optional changes
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)

**Review:** Snapshot-based approach (Option A) chosen over key-schema checks — more comprehensive and simpler to maintain. The drift check script imports the FastAPI app, generates the live OpenAPI spec, and compares it field-by-field against a committed JSON snapshot. Reports added/removed/changed paths, schemas, fields, type changes, and required/optional transitions. CI job runs independently (no DB needed) with ~15s execution time. Developers run `generate_openapi_snapshot.py` when intentionally changing schemas.


---

### Sprint 527 — DEC 2026-03-10 Remediation (6 P2 Findings)

**Status:** COMPLETE
**Goal:** Fix all 6 P2 findings from Digital Excellence Council audit 2026-03-10.
**Context:** DEC identified 15 findings (6 P2, 7 P3, 2 info). This sprint addresses the P2s.

#### F-001: Centralize Detection Keywords in classification_rules.py
- [x] Added 5 keyword lists to `classification_rules.py`: `RELATED_PARTY_KEYWORDS` (11), `INTERCOMPANY_KEYWORDS` (6), `EQUITY_RETAINED_EARNINGS_KEYWORDS` (2), `EQUITY_DIVIDEND_KEYWORDS` (1), `EQUITY_TREASURY_KEYWORDS` (1)
- [x] Removed hardcoded class attributes from `StreamingAuditor`
- [x] Updated 3 detection methods to import from `classification_rules`

#### F-002: Concentration Benchmark Threshold Consistency
- [x] Added `REVENUE_CONCENTRATION_THRESHOLD` and `EXPENSE_CONCENTRATION_THRESHOLD` to `classification_rules.py`
- [x] Replaced hardcoded 0.30/0.40 in `audit_engine.py` with imported constants
- [x] Updated `CONCENTRATION_BENCHMARKS` in `tb_diagnostic_constants.py` to use f-strings

#### F-003: Extract `_standard_table_style()` to shared/memo_base.py
- [x] Added `standard_table_style()` to `shared/memo_base.py` built on `ledger_table_style()`
- [x] Replaced local definitions in `accrual_completeness_memo.py`, `expense_category_memo.py`, `population_profile_memo.py`

#### F-004: Create `AuditResultResponse` Type
- [x] Added `AuditResultResponse` interface to `frontend/src/types/diagnostic.ts`
- [x] Replaced inline type intersection cast in `useTrialBalanceUpload.ts`

#### F-005: Add uploadTransport.ts Unit Tests
- [x] Created `frontend/src/__tests__/uploadTransport.test.ts` — 10 tests
- [x] Covers: success, 401, 403, EMAIL_NOT_VERIFIED, 500, network failure, header injection

#### F-006: Post-Processor Defensive Checks
- [x] Added `logger.warning()` + early-return guards to both post-processor functions
- [x] `apply_currency_conversion()` now checks for `"accounts"` key before any work

#### Verification
- [x] `pytest` — 249 affected tests pass (anomalies 44 + memos 44 + diagnostics 134 + sanitizer 27)
- [x] `npm run build` passes
- [x] `npm test` passes (1,339 tests, 112 suites)
- [x] `uploadTransport` tests pass (10 tests)

**Review:** All 6 P2 findings fixed. F-001 moved 21 keyword entries from 3 hardcoded locations to canonical `classification_rules.py` in standard 3-tuple format. F-002 unified 2 threshold sources. F-003 eliminated ~70 lines of duplication from 3 diagnostic memos. F-004 replaced an unsafe inline type cast with a named `AuditResultResponse` type. F-005 added 10 unit tests for the shared upload transport layer. F-006 added defensive guards preventing `KeyError` in post-processors.


---

### Sprint 528 — Expand CSV Account Type Synonym Map

**Status:** COMPLETE
**Goal:** Expand `_CSV_TYPE_MAP` to recognize compound/qualified account type values (e.g., "Current Asset", "Cost of Goods Sold", "Non-Operating Expense") and add suffix fallback for unlisted variants.

- [x] Expand `_CSV_TYPE_MAP` from 10 entries to 56 entries (compound values for all 5 categories)
- [x] Add `_CSV_TYPE_SUFFIXES` list for suffix-based fallback matching
- [x] Add `_resolve_csv_type()` helper returning `(category, confidence)` — direct=1.0, suffix=0.90
- [x] Update `_resolve_category()` to use `_resolve_csv_type()`
- [x] Update `get_abnormal_balances()` confidence logic to use `_resolve_csv_type()` instead of bare `has_csv_type` check
- [x] Tests pass — 44 anomaly tests + 77 CSV type resolution tests (121 total)
- [x] Created `tests/test_csv_type_resolution.py` — 77 tests (48 direct, 13 suffix, 7 miss, 6 e2e category, 2 e2e confidence, 1 whitespace)
- [x] `npm run build` passes

**Review:** Expanded `_CSV_TYPE_MAP` from 10 bare-word entries to 56 compound-aware entries covering all 5 categories. Added `_CSV_TYPE_SUFFIXES` for suffix-based fallback at 0.90 confidence. Extracted `_resolve_csv_type()` helper to centralize CSV-to-category resolution with tiered confidence. Fixed a latent bug in `get_abnormal_balances()` where `has_csv_type` was True (key existed in `provided_account_types`) but the value didn't match the map — causing confidence=1.0 to be assigned even though the heuristic was used.


---

### Sprint 529 — CSV Account Type Data Flow Fix

**Status:** COMPLETE
**Goal:** Fix the data path disconnect where CSV-provided account types were detected at intake but never reached downstream classification consumers.

#### Root Cause Analysis
Two bugs on separate data paths:

1. **Primary (line 1738-1741):** `audit_trial_balance_streaming()` built `account_classifications` by calling `auditor.classifier.classify()` directly — bypassing `_resolve_category()` and all CSV-provided types. This heuristic-only dict was then passed to every downstream consumer: classification validator, population profile, expense category, accrual completeness, lease diagnostic, cutoff risk. This is why every account displayed as Unknown despite the CSV having valid types.

2. **Secondary (lines 406-438):** The user-provided column mapping path in `_discover_columns()` returned early without setting `self.account_type_col` or `self.account_name_col`. With user mappings, `process_chunk()` never extracted CSV type values because the column reference was None.

#### Fixes Applied
- [x] **Bug 1:** Replace manual `classifier.classify()` loop with `auditor.get_classified_accounts()` which routes through `_resolve_category()` — CSV types now flow to all 6 downstream consumers
- [x] **Bug 2:** User-mapping path now calls `detect_columns()` for supplementary column detection (account_type, account_name) before returning
- [x] **Step 4:** Added `csv_type_trace` log line in `_resolve_csv_type()` — logs first 5 raw values per analysis for deploy verification

#### Verification
- [x] `pytest` — 6,440 passed (full suite, 0 failures)
- [x] `npm run build` passes
- [x] Existing 77 CSV type resolution tests still pass
- [x] All 566 downstream consumer tests pass (diagnostic + classification + lead_sheet + population + expense_category + accrual)

---

