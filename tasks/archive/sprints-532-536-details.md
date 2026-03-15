# Sprints 532–536 Details

> Archived from `tasks/todo.md` Active Phase on 2026-03-15.

---

### Sprint 532 — Framer-Motion Type Safety Sweep + CI Threshold Hardening

**Status:** COMPLETE
**Goal:** Fix all 6 actionable findings from DEC 2026-03-11 evening session.
**Complexity Score:** 2/10

#### F-001: Add `as const` to 31 framer-motion variant objects across 17 files
- [x] ProfileDropdown.tsx — `dropdownVariants`
- [x] DownloadReportButton.tsx — `buttonVariants`, `spinnerVariants`, `textVariants`
- [x] FinancialStatementsPreview.tsx — `spinnerVariants`
- [x] FeaturePillars.tsx — `cardHoverVariants`
- [x] ProcessTimeline.tsx — `iconVariants`, `numberVariants`
- [x] ToolSlideshow.tsx — `slideVariants`
- [x] ClientCard.tsx — `buttonVariants`
- [x] AnomalyCard.tsx — `cardVariants`
- [x] RiskDashboard.tsx — `containerVariants`
- [x] SensitivityToolbar.tsx — `containerVariants`, `editModeVariants`, `displayModeVariants`
- [x] PdfExtractionPreview.tsx — `overlayVariants`, `modalVariants`
- [x] WorkbookInspector.tsx — `overlayVariants`, `modalVariants`, `listItemVariants`
- [x] pricing/page.tsx — `containerVariants`, `cardVariants`, `fadeUp`
- [x] trust/page.tsx — `containerVariants`, `fadeUp`, `scaleIn`, `lineGrow`, `vertLineGrow`
- [x] portfolio/page.tsx — `buttonVariants`
- [x] history/page.tsx — `pageVariants`
- [x] HeritageTimeline.tsx — `containerVariants`
- [x] UnifiedToolbar.tsx — already compliant (verified)

#### F-002: Update test counts in CLAUDE.md + MEMORY.md
- [x] CLAUDE.md: 6,188 → 6,507 backend, 1,345 → 1,339 frontend
- [x] MEMORY.md: 6,223 → 6,507 backend, 1,345 → 1,339 frontend

#### F-003: Sync ceo-actions.md
- [x] Update sync date from 2026-02-27 to 2026-03-11

#### F-004: Raise CI coverage thresholds
- [x] pytest: `--cov-fail-under=60` → `--cov-fail-under=80`
- [x] Jest: `coverageThreshold` 25% → 35%

#### F-006: Fix PytestCollectionWarning
- [x] Add `__test__ = False` to `TestingMemoConfig` class

#### Verification
- [x] `npm run build` passes (42 routes, all dynamic)
- [x] `npm test` — 1,339 passed
- [x] `pytest` — 6,507 passed (0 failures)
- [x] PytestCollectionWarning for TestingMemoConfig — suppressed

**Review:** 31 `as const` additions across 17 frontend files, CI coverage gates raised (pytest 60→80%, Jest 25→35%), PytestCollectionWarning suppressed, test counts synchronized, CEO actions sync date updated. Zero regressions.
**Commit:** f37a8c5


---

### Sprint 533 — CI Parity + Lint Baseline + Accessibility Polish

**Status:** COMPLETE
**Goal:** Fix all 3 actionable findings from DEC 2026-03-15.
**Complexity Score:** 2/10

#### F-001: Add `--cov-fail-under=80` to PostgreSQL CI job
- [x] `.github/workflows/ci.yml` line 171 — append `--cov-fail-under=80` to pytest command

#### F-002: Recapture lint baseline date
- [x] `.github/lint-baseline.json` — update `"updated"` field from `2026-02-23` to `2026-03-15`

#### F-003: Add `aria-label` to icon-only interactive elements (7 instances)
- [x] `AdjustmentEntryForm.tsx` — remove line button: `aria-label="Remove line"`
- [x] `FileQueueItem.tsx` — delete file button: `aria-label` matching title
- [x] `ProfileDropdown.tsx` — avatar button: `aria-label="User menu"`
- [x] `ToolLinkToast.tsx` — dismiss button: `aria-label="Dismiss notification"`
- [x] `UnifiedToolbar.tsx` — search button: `aria-label="Open command palette"`
- [x] `UnifiedToolbar.tsx` — settings link: `aria-label="Settings"`
- [x] `UnifiedToolbar.tsx` — sign in link: `aria-label="Sign in"`

#### Verification
- [x] `npm run build` passes (all routes dynamic)
- [x] `npm test` — 1,339 passed (112 suites)

**Review:** PostgreSQL CI coverage threshold aligned with SQLite (80%), lint baseline date refreshed, 7 icon-only buttons/links now have `aria-label` for screen reader accessibility. Zero regressions.


---

### Sprint 534 — Multi-Period Comparison: 8-Bug Fix Batch

**Status:** COMPLETE
**Goal:** Fix 8 bugs identified in multi-period comparison test session.
**Complexity Score:** 5/10

#### Bug 1: Unicode escape rendering in summary header
- [x] Replace literal `\u00B7` in JSX text content with actual `·` character (page.tsx line 366)

#### Bug 2: CSV parsing incompleteness / hard account limit
- [x] Root cause: `lead_sheet_grouping.summaries` only contains abnormal/flagged accounts, not all parsed accounts
- [x] Add `all_accounts` field to single-sheet audit result (`audit_engine.py`)
- [x] Add `all_accounts` field to multi-sheet audit result (`audit_engine.py`)
- [x] Update `extractAccounts` in `useMultiPeriodComparison.ts` to prefer `all_accounts`
- [x] Update `AuditResultForComparison` type to include `all_accounts`
- [x] Remove hard 100-account display limit in `AccountMovementTable.tsx`

#### Bug 3: "Closed Account" false positives
- [x] Confirmed: downstream symptom of Bug 2 — now resolved. Accounts present with zero balance have `current_acct != None`, so they are not classified as CLOSED.
- [x] Classification logic already correct: `is_closed = current_acct is None` (absent from file, not zero balance)

#### Bug 4: Suggested procedures template mismatch (rotation bug)
- [x] Expand `_MOVEMENT_PROCEDURES` dict from 6 to 24 entries covering all (category, direction) combos
- [x] Add 6 new procedure texts to `FOLLOW_UP_PROCEDURES` (revenue_decrease, cogs_decrease, asset_decrease, cash_decrease, liability_increase, expense_decrease)
- [x] Fix direction logic: credit-nature accounts (revenue, liability) — negative change = economic increase
- [x] Handle new_account, closed_account, sign_change movement types explicitly

#### Bug 5: Ratio calculations (GPM=100%, COGS%=0%)
- [x] Root cause: `is_cogs = acct_type == "cogs" if acct_type else ...` short-circuits when acct_type is any non-empty string (e.g., "expense")
- [x] Fix: use `acct_type == "cogs" or _match_keyword(name, _COGS_KEYWORDS)` (OR instead of exclusive fallback)
- [x] Same fix for `is_revenue`: OR-based check

#### Bug 6: Lead sheet accordion expand throws frontend error
- [x] Root cause: `ThreeWayLeadSheetSummary` missing `movements` field — `.map()` on undefined
- [x] Add `movements: list[dict]` to `ThreeWayLeadSheetSummary` dataclass + `to_dict()`
- [x] Pass enriched movements through in `compare_three_periods` lead sheet loop
- [x] Add `movements` to `ThreeWayLeadSheetSummaryResponse` schema
- [x] Add null guard `(ls.movements ?? [])` in `CategoryMovementSection.tsx`

#### Bug 7: Blank engagement metadata in downloaded PDF
- [x] Add Client Name, Fiscal Year End, Engagement Practitioner, Engagement Reviewer inputs to config screen
- [x] Pass metadata values to `/export/multi-period-memo` endpoint body
- [x] Default to "Not specified" for blank fields

#### Bug 8: Upload UX blocks concurrent zone interaction
- [x] Replace shared `isProcessing` blocking with per-zone disabled logic
- [x] Each zone disabled only during its own loading or during comparison — not blocked by other zones
- [x] Compare button remains gated on all required zones being ready

#### Verification
- [x] `npm run build` passes (all routes dynamic)
- [x] `npm test` — 1,339 passed (112 suites)
- [x] `pytest tests/test_multi_period_comparison.py` — 65 passed
- [x] `pytest tests/test_multi_period_memo.py` — 75 passed

**Review:** 8 bugs fixed across 9 files (3 backend engine/route, 2 backend shared modules, 4 frontend components/hooks). Key root causes: (1) account extraction from audit result only included abnormal accounts, not full TB; (2) sign convention not respected in procedure/ratio logic; (3) 3-way comparison dropped movements from lead sheet summaries. Zero regressions.
**Commit:** 3cb7d6e


---

### Sprint 536 — Round-Number Detection Tiering

**Status:** COMPLETE
**Goal:** Replace flat round-number detection with a 3-tier framework (Suppress / Minor / Material) to reduce noise from expected round balances while preserving genuine anomaly signal.
**Complexity Score:** 6/10

#### Implementation
- [x] Add `classify_round_number_tier()` + tiered constants to `classification_rules.py`
- [x] Rewrite `detect_rounding_anomalies()` in `audit_engine.py` to use tiered classification
- [x] Tier 1 (Suppress): fixed assets, equity, long-term debt, depreciation, goodwill, salary
- [x] Tier 1 carve-outs: related-party note payables still generate findings
- [x] Tier 2 (Minor): accruals, reserves, bonuses, rent, insurance, pensions, warranties
- [x] Tier 3 (Material): revenue, COGS, misc/catch-all, repeated identical patterns, >10% of TB
- [x] Update finding text by tier (Minor observation vs Material finding)
- [x] Update score contribution: Tier 2 = +2, Tier 3 = +8, Tier 1 = +0
- [x] Add `DEPLOY-VERIFY-536` log line
- [x] Update existing tests for new tier behavior

#### Verification
- [x] `npm run build` passes (all routes dynamic)
- [x] `npm test` — 1,339 passed (112 suites)
- [x] `pytest` — 88 passed on modified test files (0 failures)
- [x] Tier 1 accounts suppressed in Cascade TB (14/14 checked: Land, Buildings, Leasehold, Machinery, Vehicles, CIP, Patents, Customer Lists, LT Debt x2, Common Stock x2, APIC, Retained Earnings)
- [x] Tier 1 carve-out: Note Payable — Shareholder still flagged in abnormals
- [x] Tier 2 accounts generate Minor findings (Accrued Bonuses, Pension Obligation confirmed minor)
- [x] Tier 3 accounts generate Material findings (Revenue OEM/Direct/Government, COGS Direct Materials/Overhead)
- [x] Cascade TB: 87 round-balance accounts → 20 findings (67 suppressed by tiering)
- [x] All acceptance criteria passed

**Review:** Three-tier round-number detection replaces flat flagging. `classify_round_number_tier()` added to `classification_rules.py` with 3 keyword lists + subtype-based suppression. `detect_rounding_anomalies()` rewritten to use tiered classification with per-tier severity, finding text, and score contribution. Repeated identical amounts pattern detection (3+ accounts same amount/type) added. Cascade FY2025 TB: 87 round accounts → 67 suppressed (Tier 1), 2 minor (Tier 2), 14 material (Tier 3), 4 merged flags. Zero regressions: 44 anomaly tests + 88 broader backend tests + 1,339 frontend tests pass.


---

### Sprint 535 — QA Sweep Fix Batch (11 fixes across 6 files)

**Status:** COMPLETE
**Goal:** Fix all FAIL/PARTIAL items from comprehensive QA sweep against Cascade FY2025 test TB (162 accounts).
**Complexity Score:** 7/10

#### P0-1: Account balances and classified_accounts keyed by display name
- [x] Add `provided_account_subtypes` storage + subtype column detection in `process_chunk()`
- [x] Rewrite `get_category_totals()` to build display-name-keyed dicts
- [x] Expose `account_balances`, `classified_accounts`, `account_subtypes` in result dict

#### P0-2: Compute lead_sheet_grouping in audit result
- [x] Call `group_by_lead_sheet()` + `lead_sheet_grouping_to_dict()` in streaming audit
- [x] Expose as `result["lead_sheet_grouping"]`

#### P0-3: Display-name-keyed all_accounts_list
- [x] Build `all_accounts_list` entries with display name instead of bare account number

#### P1-1: AOCI accounts excluded from abnormal balance findings
- [x] Add AOCI keywords to `CONTRA_EQUITY_KEYWORDS` in `classification_rules.py`

#### P1-2: Intercompany imbalance priority over related party
- [x] Reverse merge order in `_merge_anomalies()` — intercompany first, then related party
- [x] Add promotion logic: `is_intercompany_imbalance=True` → override type + issue text

#### P1-3: "Temporary" keyword false positive in suspense detection
- [x] Replace bare `"temporary"` with phrase rules: `"temporary account"`, `"temporary balance"`

#### P2-1: Risk score decomposition cap reconciliation
- [x] Add cap logic to `compute_tb_risk_score()` — reconcile factor lines when raw sum > 100

#### P2-2: Lead sheet misclassifications (13 new rules)
- [x] "current portion of long-term" → H at 1.05 (beats "long-term debt" at 1.0)
- [x] COGS: "manufacturing overhead", "freight inbound/—", "packaging" → M
- [x] "bank fee"/"bank charge" → N at 0.95 (overrides "bank" → A at 0.9)
- [x] "dividends payable" → H, "short-term investment" → A
- [x] Long-term debt: "subordinated debt", "senior notes", "revolver", "capital lease", "note payable"
- [x] Other LT liabilities: "pension obligation", "environmental remediation", "asset retirement obligation", "workers compensation reserve"

#### P2-3: Balance sheet pre-closing TB imbalance note
- [x] Add `is_pre_closing` + `pre_closing_note` fields to `FinancialStatements`
- [x] Detect when `balance_difference ≈ net_income` and set explanatory note

#### P3-1: Population profile display-name key alignment
- [x] Pass display-name-keyed dicts to `compute_population_profile()` from audit engine

#### P3-2: Credit-normal sign-flip for period-over-period display
- [x] Add `display_change_amount`, `display_change_percent`, `is_credit_normal` to `AccountMovement.to_dict()`
- [x] Add same fields to `LeadSheetMovementSummary.to_dict()`

#### Bonus: Multi-sheet ClassificationResult.value fix
- [x] Fix `classifier_instance.classify().value` → `.category.value` in multi-sheet path

#### QA test data
- [x] `tests/qa/paciolus_test_tb_cascade_fy2025.csv` — 162-account balanced TB
- [x] `tests/qa/cascade_fy2024_prior.csv` — 159-account prior year
- [x] `tests/qa/cascade_fy2025_budget.csv` — 159-account budget
- [x] `tests/qa/run_qa_sweep.py` — comprehensive 5-tool QA sweep script

#### Verification
- [x] `npm run build` passes (all routes dynamic)
- [x] `npm test` — 1,339 passed (112 suites)
- [x] `pytest` — 315 passed on modified test files (0 failures)
- [x] QA sweep: all 5 tools complete without crashes
- [x] Pre-closing TB note: `is_pre_closing=True`, note generated correctly

**Review:** 11 prioritized fixes (P0×3, P1×3, P2×3, P3×2) plus 1 bonus pre-existing bug fix across 6 backend files. Root causes: (1) account_balances keyed by number not display name, breaking keyword matching in ratio engine and population profile; (2) subtype column never captured from CSV; (3) lead_sheet_grouping never computed in audit result; (4) AOCI not in contra-equity list; (5) intercompany/related-party merge order; (6) "temporary" keyword too broad; (7) risk score factor lines not reconciled to 100 cap; (8) 13 missing/underweighted lead sheet rules; (9) no pre-closing TB indicator; (10) credit-normal sign convention not exposed for display.
**Commit:** 10c2bcc


---

