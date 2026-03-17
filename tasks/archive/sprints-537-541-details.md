# Sprints 537–541 Details

> Archived from `tasks/todo.md` Active Phase on 2026-03-17.

---

### Sprint 539 — Comprehensive Remediation (Security, Correctness, Architecture)

**Status:** COMPLETE
**Goal:** Fix critical security, billing correctness, auth concurrency, webhook idempotency, and architectural quality issues identified by 3 independent audits.

#### Section 1 — Authorization & Billing Correctness
- [x] 1.1: Refactor `check_seat_limit()` to accept org context, not caller identity
- [x] 1.2: `handle_subscription_deleted()` downgrades ALL org members to FREE
- [x] 1.3: Implement `is_authorized_for_client()` helper for org-aware access
- [x] 1.4: Backfill `org.subscription_id` on checkout for org-first lifecycle

#### Section 2 — Authentication
- [x] 2.1: Replace read-then-write in `rotate_refresh_token()` with CAS guard

#### Section 3 — Webhook Idempotency
- [x] 3.1: Atomic deduplication — insert dedup marker before business logic
- [x] 3.2: Stale event ordering guard — reject out-of-order subscription events

#### Section 4 — Data Integrity
- [x] 4.1: DPA timestamp normalization — `.astimezone(UTC)` for offset-aware inputs

#### Section 5 — Architectural Refactoring
- [x] 5.1: Split `apiClient.ts` into transport/authMiddleware/cachePlugin/downloadAdapter
- [x] 5.8: Split `engagements.py` into CRUD/analytics/exports + tool_taxonomy config
- [x] 5.10: Audit back-compat shims in `export.py` — added removal plan (Sprint 545)

#### Section 6 — Test Coverage
- [x] 15 new tests: seat enforcement, cancellation entitlement, refresh race, webhook dedup, event ordering, DPA timestamps, org-first lifecycle, shared access

#### Verification
- [x] `pytest` passes (6,522 tests — 15 new)
- [x] `npm run build` passes
- [x] `npm test` passes (1,339 tests)

#### Review
- 6 critical/high security bugs fixed across auth, billing, webhooks
- Org member collaborative access implemented across 4 managers
- apiClient.ts split from 1,141-line monolith into 5 composable modules
- engagements.py decomposed into 3 focused route files + centralized tool taxonomy
- Zero regressions in existing 6,507 + 1,339 test suites


---

### Sprint 538 — DEC 2026-03-16 Remediation

**Status:** COMPLETE
**Goal:** Fix 2 P2 + 7 P3 findings from Digital Excellence Council audit.

#### P2 Fixes
- [x] F-001: Reorder `classify_round_number_tier()` — informational check before 10%-TB escalation
- [x] F-002: Cap informational risk score contribution at 5 points

#### P3 Fixes
- [x] F-003: Narrow bare `"cash"` keyword in TIER2_INFORMATIONAL (5 specific variants)
- [x] F-004: Add 'informational' to severity filter dropdowns (FlaggedEntriesTable, FollowUpItemsTable)
- [x] F-005: Contra-equity detection in multi-period credit-normal sign flip
- [x] F-006: Replace "potential adjusting entry" language with neutral wording (4 occurrences)
- [x] F-007: Add related-party loan variants to ROUND_NUMBER_TIER1_CARVEOUTS (5 entries)
- [x] F-009: Benford MAD digit filter `>` → `>=`
- [x] F-014: Add `__test__ = False` to TestTier enum

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,339 tests)
- [x] `pytest` passes (6,507 tests)
- [x] QA: Cash at >10% TB total returns "informational" (not "material")
- [x] QA: 20 informational findings produce max 5 risk score points

#### Review
- 9 findings fixed across 8 files (2 P2, 7 P3)
- F-001: Moved informational keyword check to Step 5e, before 10%-TB escalation (Step 5f)
- F-002: `min(informational_count, 5)` with "(capped)" label when cap applies
- F-003: Replaced bare "cash" with 5 specific variants: cash and cash equivalents, operating cash, petty cash, cash on hand, cash in bank
- F-005: Added `is_contra_account()` check in `_is_credit_normal` property — contra-equity excluded from sign flip
- F-006: Removed "potential adjusting entry" from 4 procedure texts; replaced with "further investigation/evaluation"
- F-007: Added 5 related-party loan keywords to carve-outs (shareholder/officer/employee/director/related party)
- Lessons captured in `tasks/lessons.md`
- Commit: c47cd28


---

### Sprint 540 — Report QA Bug Fixes (Meridian FY2025)

**Status:** COMPLETE
**Goal:** Fix 12 confirmed bugs across 8 report generators identified during QA review of Meridian Capital Group FY2025 sample output.

#### Priority 1 — Critical: Proof Summary Metrics
- [x] 1a: Bank rec proof summary shows 0%/0% — add `data_quality` and `column_detection` keys to bank rec result dict
- [x] 1b: Data Completeness/Column Confidence hardcoded 94%/92% — parameterize `_make_testing_result()`, pass distinct per-tool values

#### Priority 2 — High: Calculation and Reference Errors
- [x] 2a: Benford digit 9 deviation off by 10x — fix sample data from -0.0004 to -0.00406; add regression test
- [x] 2b: Bank rec AR aging cross-ref mismatch — share reference via `_SHARED_REFS` between gen_ar_aging and gen_bank_rec
- [x] 2c: ASC 240-10 incorrect in JE testing — replace with ASC 850-10 (Related Party Disclosures) in YAML

#### Priority 3 — Medium: Data Consistency
- [x] 3a: Financial statements cover page missing client/period — pass `entity_name` as `client_name` in `FSReportMetadata`
- [x] 3b: Payroll headcount non-agreement — add variance footnote in roll-forward + reconciliation note in department summary
- [x] 3c: AR aging missing test descriptions — add 5 alternate test_key aliases to `AR_AGING_TEST_DESCRIPTIONS`

#### Priority 4 — Low: Presentation and UX
- [x] 4a: Revenue cut-off negative amounts — apply `abs()` in `_build_cutoff_table`
- [x] 4b: Inventory risk score vs test pass rate — add interpretive note via `_build_risk_score_note` post-results callback
- [x] 4c: IFRS citations on US GAAP engagement — replace IAS 16 → ASC 360-10, IAS 2 → ASC 330-10 in methodology intros
- [x] 4d: Financial statement notes placeholder — replace inline italic with bordered callout box

#### Verification
- [x] `pytest` (401 affected tests pass)
- [x] `npm run build` passes
- [x] Benford regression test (28 tests pass)
- [x] All 21 sample reports regenerated successfully

#### Review
- 8 files modified: `generate_sample_reports.py`, `fasb_scope_methodology.yml`, `pdf_generator.py`, `payroll_testing_memo_generator.py`, `ar_aging_memo_generator.py`, `revenue_testing_memo_generator.py`, `inventory_testing_memo_generator.py`, `fixed_asset_testing_memo_generator.py`
- 1 test file modified: `test_benford.py` (+1 regression test)


---

### Sprint 537 — Informational Note Tier

**Status:** COMPLETE
**Goal:** Add third severity level (Informational Note) for low-signal findings that require no procedure.

#### Backend
- [x] Add `ROUND_NUMBER_TIER2_INFORMATIONAL` list to `classification_rules.py`
- [x] Update `classify_round_number_tier()` to return `"informational"` for matching accounts
- [x] Handle `tier == "informational"` in `detect_rounding_anomalies()` (severity, text template)
- [x] Add `informational_count` to `_build_risk_summary()` and risk_summary dict
- [x] Update `compute_tb_risk_score()` for informational (+1 each, grouped summary line)
- [x] Update PDF generator: four-column risk table, third section for informational notes
- [x] Change classification_validator number_gap severity to `"informational"`
- [x] Add DEPLOY-VERIFY-537 log line
- [x] Fix stale test assertion in `test_contra_and_detection_fixes.py` (contra-asset → minor, not suppressed)

#### Frontend
- [x] Add `'informational'` to Severity type in `types/shared.ts`
- [x] Add `informational_count` to RiskSummary in `types/mapping.ts`
- [x] Update `DisplayMode` to include `'all'` in SensitivityToolbar
- [x] Three-section split in RiskDashboard (High / Medium / Notes)
- [x] Informational card variant in AnomalyCard (grey border, collapsed, no procedure)
- [x] Pass displayMode to RiskDashboard for filtering
- [x] Add informational severity color to ClassificationQualitySection
- [x] Add `informational` to all `Record<Severity, ...>` across 7 files

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,339 tests)
- [x] `pytest` passes (6,507 tests)
- [x] Cascade QA: 3 informational (Cash, AR Trade, AP Trade), Accrued Bonuses stays Minor
- [x] Meridian QA: 1 informational (Rent — Office), 2520 suppressed, CV-4 gaps informational

#### Review
- Fixed false positive: "rent" substring matched "current" in "2520 — Current Portion — Long Term Debt". Added "current portion" and "long term debt" to TIER1_SUPPRESS.
- Fixed stale test: `test_allowance_round_suppressed` was already failing pre-537 (Sprint 536 changed contra-asset from suppress to minor).
- Lessons captured in `tasks/lessons.md`.
- Commit: c394549


---

### Sprint 541 — Report QA Round 2: Fiscal Year End on Testing Memos

**Status:** COMPLETE
**Goal:** Fix fiscal_year_end rendering as "—" on all testing memo cover pages, and confirm proof summary metrics are dynamically computed.

#### Fix 1 — Fiscal Year End on Testing Memo Cover Pages
- [x] Add `fiscal_year_end: Optional[str] = None` to `WorkpaperMetadata` schema
- [x] Add `fiscal_year_end` to `common_kwargs` in `_memo_export_handler`
- [x] Add `fiscal_year_end` param to `generate_testing_memo()` and pass to `ReportMetadata`
- [x] Update 7 standard testing generators (JE, AP, Payroll, Revenue, AR Aging, Fixed Asset, Inventory)
- [x] Update 2 custom generators (Bank Rec, Three-Way Match) — signature + `ReportMetadata` wiring
- [x] Update 8 remaining generators (Multi-Period, Currency, Sampling ×2, Preflight, PopProfile, Expense, Accrual, Flux) to prevent `**common_kwargs` crash

#### Fix 2 — Proof Summary Metrics (Dynamic Computation)
- [x] Confirmed: `completeness_score` computed dynamically per-file by `shared/data_quality.py`
- [x] Confirmed: `overall_confidence` computed dynamically per-file by `column_detector.py`
- [x] Confirmed: `build_proof_summary_section()` extracts from result dict — no hardcoded values
- [x] No code change needed — metrics are already dynamic

#### Verification
- [x] All 18 generator function signatures verified via `inspect.signature()`
- [x] `pytest -k memo` passes (867 tests, 0 failures)
- [x] Proof summary tests pass (8/8)

#### Review
- 18 files modified across export schema, route handler, shared template, and all memo generators
- Root cause: `generate_testing_memo()` never received `fiscal_year_end` — only financial statements builder did
- Proof metrics (Fix 2) were already correct — dynamic computation via `data_quality.py` and `column_detector.py`


---

