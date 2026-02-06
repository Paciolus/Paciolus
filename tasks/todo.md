# Paciolus Development Roadmap

> **Protocol:** Every directive MUST begin with a Plan Update to this file and end with a Lesson Learned in `lessons.md`.

---

## Completed Phases

### Phase I (Days 1-7, Sprints 8-24) — COMPLETE
> Core platform: Zero-Storage TB analysis, streaming, classification, brand, risk dashboard, multi-sheet Excel, PDF/Excel export, JWT auth, activity logging, client management, practice settings, deployment prep

| Sprint | Theme | Primary Agent |
|--------|-------|---------------|
| 8 | Automated Testing | QualityGuardian |
| 9 | Mapping Logic + Brand + Column Detection | BackendCritic + FrontendExecutor |
| 10 | Risk Dashboard | BackendCritic + FintechDesigner |
| 11 | Multi-Sheet Excel | BackendCritic |
| 12 | PDF Export | BackendCritic + FrontendExecutor |
| 13 | Authentication | BackendCritic + FintechDesigner |
| 14 | Activity Logging | BackendCritic + FrontendExecutor |
| 15 | Stability Reset | QualityGuardian |
| 16 | Client Infrastructure | BackendCritic + FrontendExecutor |
| 17 | Portfolio Dashboard | FintechDesigner + FrontendExecutor |
| 18 | Diagnostic Fidelity | IntegratorLead + BackendCritic |
| 19 | Analytics & Ratios | BackendCritic + FintechDesigner |
| 20 | Document Hardening | QualityGuardian + BackendCritic |
| 21 | Practice Settings | BackendCritic + FrontendExecutor |
| 22 | Sensitivity Tuning | FintechDesigner + FrontendExecutor |
| 23 | Marketing Front | FintechDesigner + FrontendExecutor |
| 24 | Production Deployment | BackendCritic + QualityGuardian |

### Phase II (Sprints 25-40) — COMPLETE
> Test suite, 9 ratios (Current/Quick/D2E/Gross/Net/Operating/ROA/ROE), IFRS/GAAP docs, trend analysis + viz, industry ratios (Manufacturing/Retail/Services), rolling windows, batch upload, benchmark RFC

| Sprint | Theme | Primary Agent |
|--------|-------|---------------|
| 25 | Foundation Hardening (47 ratio tests) | QualityGuardian + BackendCritic |
| 26 | Profitability Ratios | BackendCritic |
| 27 | Return Metrics (ROA/ROE) | BackendCritic |
| 28 | Ratio Dashboard Enhancement | FrontendExecutor + FintechDesigner |
| 29 | Classical PDF "Renaissance Ledger" | BackendCritic + FintechDesigner |
| 30 | IFRS/GAAP Documentation | ProjectAuditor + BackendCritic |
| 31 | Classification Intelligence (fuzzy match) | BackendCritic + FrontendExecutor |
| 32 | Weighted Materiality | BackendCritic + QualityGuardian |
| 33 | Trend Analysis Foundation | BackendCritic + FintechDesigner |
| 34 | Trend Visualization (recharts) | FintechDesigner + FrontendExecutor |
| 35 | Industry Ratio Foundation | BackendCritic + FintechDesigner |
| 36 | Industry Ratio Expansion | BackendCritic + FrontendExecutor |
| 37 | Rolling Window Analysis | BackendCritic + FrontendExecutor |
| 38 | Batch Upload Foundation | FrontendExecutor + QualityGuardian |
| 39 | Batch Upload UI | FintechDesigner + FrontendExecutor |
| 40 | Benchmark Framework RFC | BackendCritic + ProjectAuditor |

### Phase III (Sprints 41-47) — COMPLETE
> Anomaly detection (suspense, concentration, rounding, balance sheet), benchmark engine + API + UI + integration

| Sprint | Theme | Primary Agent |
|--------|-------|---------------|
| 41 | Suspense Account Detector + Performance Quick Wins | BackendCritic + FrontendExecutor |
| 42 | Concentration Risk + Rounding Anomaly | BackendCritic + FintechDesigner |
| 43 | Balance Sheet Validator | BackendCritic |
| 44 | Benchmark Schema Implementation | BackendCritic |
| 45 | Benchmark Comparison Engine (4 API endpoints) | BackendCritic + QualityGuardian |
| 46 | Benchmark Frontend Components | FrontendExecutor + FintechDesigner |
| 47 | Benchmark Integration & Testing | QualityGuardian |

### Phase IV (Sprints 48-55) — COMPLETE
> User profile, security hardening, lead sheets, prior period comparison, adjusting entries, DSO, CSV export, frontend tests

| Sprint | Theme | Primary Agent |
|--------|-------|---------------|
| 48 | User Profile Settings + Page Separation | FrontendExecutor + BackendCritic |
| 49 | Security Hardening (CSRF, headers, lockout) | BackendCritic + QualityGuardian |
| 50 | Lead Sheet Mapping (A-Z, 100+ keywords) | BackendCritic + FrontendExecutor |
| 51 | Prior Period Comparison | BackendCritic + FintechDesigner |
| 52 | Adjusting Entry Module | BackendCritic + FrontendExecutor |
| 53 | DSO Ratio + Workpaper Fields | BackendCritic + FintechDesigner |
| 54 | CSV Export Enhancement | BackendCritic + FrontendExecutor |
| 55 | Frontend Test Foundation (Jest/RTL, 26 tests) | QualityGuardian + FrontendExecutor |

### Phase V (Sprints 56-60) — COMPLETE
> UX polish, email verification (backend + frontend), endpoint protection, homepage demo mode

| Sprint | Theme | Primary Agent |
|--------|-------|---------------|
| 56 | UX Polish — EditClientModal, Navigation, Account ID | FrontendExecutor |
| 57 | Email Verification Backend (SendGrid, 36 tests) | BackendCritic |
| 58 | Email Verification Frontend | FrontendExecutor |
| 59 | Protect Audit Endpoints | BackendCritic + FrontendExecutor |
| 60 | Homepage Demo Mode | FrontendExecutor + FintechDesigner |

**Test Coverage at Phase V End:** 625 backend tests + 26 frontend tests

---

## Post-Sprint Checklist

**MANDATORY:** Complete these steps after EVERY sprint before declaring it done.

### Verification
- [ ] Run `npm run build` in frontend directory (must pass)
- [ ] Run `pytest` in backend directory (if tests modified)
- [ ] Verify Zero-Storage compliance for new data handling

### Documentation
- [ ] Update sprint status to COMPLETE in todo.md
- [ ] Add Review section with Files Created/Modified
- [ ] Add lessons to lessons.md if corrections occurred

### Git Commit
- [ ] Stage relevant files: `git add <specific-files>`
- [ ] Commit with sprint reference: `git commit -m "Sprint X: Brief Description"`
- [ ] Verify commit: `git log -1`

### Commit Conventions
- **Format:** `Sprint X: Brief Description`
- **Atomic:** One commit per sprint minimum; additional commits for major features OK
- **Avoid:** `git add -A` (may include sensitive files); use specific file paths

---

## Phase VI: Multi-Period Analysis & Journal Entry Testing

> **Source:** Agent Council Discussion (2026-02-05) + Accounting Expert Auditor Consultation
> **Resequenced:** Agent Council + Auditor Review (2026-02-06) — rebrand deferred, tools-first priority
> **Scope:** 10 sprints (61-70) covering two new tools + platform rebrand + housekeeping
> **Estimated New Code:** ~14,000 lines (6,500 backend + 7,500 frontend)
> **Estimated New Tests:** 130+ backend tests, 30+ frontend tests

### CEO Directive: Platform Suite, Not a Single Tool
> **STRICT REQUIREMENT 1:** Paciolus is an audit intelligence platform with a suite of tools.
> The homepage must market the company and the full suite — not just one tool.
> Trial Balance Diagnostics is the headliner, but not the entire pitch.

> **STRICT REQUIREMENT 2:** These are three distinct products, not extensions of one tool.
> Each must feel like its own tool to the customer, even if engines share patterns internally.

| Tool | Route | Marketing Name | Icon/Identity |
|------|-------|---------------|---------------|
| 1. Trial Balance Diagnostics | `/tools/trial-balance` (move from `/`) | Trial Balance Diagnostics | Balance scale / checkmark |
| 2. Multi-Period Comparison | `/tools/multi-period` | Multi-Period Comparison | Dual-document / timeline |
| 3. Journal Entry Testing | `/tools/journal-entry-testing` | Journal Entry Testing | Magnifying glass / shield |

**Homepage redesign (FintechDesigner + FrontendExecutor):**
- `/` becomes the platform marketing page — sells Paciolus the company and suite
- Hero section: platform-level pitch ("Professional Audit Intelligence Suite"), not "upload your trial balance"
- Tool Showcase section: three tool cards with distinct icons, descriptions, and CTAs linking to each tool
- DemoZone: either tabbed multi-tool demo or TB Diagnostics headliner with teaser previews for the other two
- ProcessTimeline: evolve to platform-level (or replace with per-tool flow within each tool page)
- FeaturePillars: revisit — should sell platform-level value props (Zero-Storage, Professional-Grade, etc.)
- Authenticated users: platform dashboard or tool selector instead of jumping straight into TB upload
- Navigation: platform-level nav with tool selector dropdown or top-level links to each tool

**Design constraints (FintechDesigner):**
- Separate top-level navigation entries (not tabs within existing diagnostic)
- Each tool has its own independent upload flow, results view, and export
- Each tool needs its own homepage demo/marketing section
- Same Oat & Obsidian palette but distinguishing visual element per tool (icon, header treatment)
- No shared state across tools — separate hooks, contexts, upload flows
- User should always know which tool they're in via persistent visual cues

### Agent Council Consensus
- **BackendCritic:** Multi-Period first (reuses lead sheet + prior period patterns), JE Testing second (new pipeline)
- **FrontendExecutor:** Agrees on ordering. BenfordChart (8/10) and FlaggedEntryTable (8/10) are hardest components
- **Accounting Expert Auditor:** Movement classification (NEW/CLOSED/SIGN_CHANGE) essential for multi-period; Benford's Law + 17 test battery for JE testing
- **All agents:** Contra-Account Validator deferred indefinitely; Account Dormancy is free byproduct of multi-period

### Identified Tensions
| Tension | Agent A | Agent B | Resolution |
|---------|---------|---------|------------|
| Sprint count | BackendCritic: 9 total | FrontendExecutor: 7.5 FE alone | Parallelize backend/frontend within each sprint |
| EditClientModal | BackendCritic: housekeeping sprint | FrontendExecutor: already coded | Sprint 61 standalone commit (no overhead) |
| JE complexity | Both: highest risk (7-8/10) | — | Split into 4 focused sprints with clear milestones |

---

### Sprint 61: Housekeeping + Multi-Period Foundation — COMPLETE
> **Complexity:** 3/10 | **Agent Lead:** BackendCritic
> **Focus:** Commit EditClientModal, build multi-period comparison engine

#### Housekeeping
- [x] Commit EditClientModal from Sprint 56 (already coded, uncommitted) — committed as `6ebbed8`
- [x] Stage `frontend/src/components/portfolio/EditClientModal.tsx` + modified files
- [x] Atomic commit: "Sprint 56: EditClientModal for portfolio clients"

#### Multi-Period Backend Foundation
- [x] Create `backend/multi_period_comparison.py` — core comparison engine
  - AccountMovement dataclass: account_name, prior_balance, current_balance, movement_type, change_amount, change_percent
  - MovementType enum: NEW_ACCOUNT, CLOSED_ACCOUNT, SIGN_CHANGE, INCREASE, DECREASE, UNCHANGED
  - MovementSummary dataclass: total_accounts, movements_by_type, significant_movements
  - compare_trial_balances() function: account-level matching by normalized name
  - calculate_movement() function: classify each account's change
  - SignificanceTier: MATERIAL (>materiality threshold), SIGNIFICANT (>10% or >$10K), MINOR (<10% and <$10K)
- [x] Account name normalization for fuzzy matching (strip whitespace, case-insensitive, handle common abbreviations)
- [x] Lead sheet organization: group movements by lead sheet category
- [x] Create `backend/tests/test_multi_period_comparison.py`
  - Test movement type classification (all 6 types)
  - Test account matching (exact, fuzzy, unmatched)
  - Test significance tier assignment
  - Test edge cases (empty TB, single account, all new accounts)
  - 63 tests (target was 25+)
- [x] `pytest` passes

---

### Sprint 62: Route Scaffolding + Multi-Period API/Frontend — COMPLETE
> **Complexity:** 6/10 | **Agent Lead:** FrontendExecutor + BackendCritic
> **Focus:** Tool route structure, multi-period API endpoint, dual-file upload UI, movement table
> **Change:** Rebrand deferred to Sprint 66 per auditor/council recommendation — tools-first priority

#### Route Scaffolding (from original Sprint 62)
- [x] Create tool route structure (no visual rebrand yet)
  - `/tools/trial-balance` — TB Diagnostics (moved from `/`)
  - `/tools/multi-period` — Multi-Period Comparison
  - `/tools/journal-entry-testing` — Journal Entry Testing (placeholder until Sprint 66)
- [x] Platform navigation: Tools dropdown in ProfileDropdown with links to each tool route
- [x] Redirect `/` → `/tools/trial-balance` temporarily (full homepage rebrand in Sprint 66)
- [x] Tool page nav bars with cross-tool links (ToolNav component)

#### Backend API (from original Sprint 63)
- [x] POST `/audit/compare-periods` endpoint (require_verified_user)
  - Accepts two account lists (current + prior) in request body
  - Returns MovementSummary with categorized account movements
  - Zero-Storage: both files processed in-memory, results ephemeral
- [x] Movement summary statistics: net change by category, largest movements, new/closed account lists
- [x] Lead sheet grouping for movement results
- [x] 27 API integration tests (5 test classes)

#### Frontend — Standalone Tool Route `/tools/multi-period`
- [x] Create `/tools/multi-period` page as standalone tool experience
  - Own hero header with dual-document motif
  - Own upload flow — completely independent from TB Diagnostics
  - Persistent "Multi-Period Comparison" identity in ToolNav
- [x] FileDropZone component: side-by-side dropzones for "Prior Period" and "Current Period"
  - Period labels (e.g., "FY2024", "FY2025") with text inputs
  - Oat & Obsidian dropzone styling with file info display
- [x] Page orchestrates dual audit + comparison flow
  - State: priorFile, currentFile, priorResult, currentResult, comparison
  - Flow: upload both → audit both via /audit/trial-balance → compare → display results

#### Frontend — Results Display
- [x] AccountMovementTable component with sorting and filtering
  - Sortable columns: Account, Prior Balance, Current Balance, Change, Change %, Type, Significance
  - Color-coded movement badges (sage=increase, clay=decrease, oatmeal=unchanged)
  - Significance indicators (material/significant/minor)
  - Filter by movement type and significance tier
- [x] MovementSummaryCards: visual summary (NEW, CLOSED, SIGN_CHANGE, INCREASE, DECREASE, UNCHANGED)
- [x] CategoryMovementSection: group by lead sheet with expand/collapse
- [x] Account dormancy detection: dormant flag with visual indicator
- [x] useMultiPeriodComparison hook + types exported from hooks/index.ts
- [x] `npm run build` passes
- [x] `pytest` passes (715 total: 688 + 27 API tests)

---

### Sprint 63: Multi-Period Polish + Three-Way Comparison — COMPLETE
> **Complexity:** 4/10 | **Agent Lead:** BackendCritic + FrontendExecutor
> **Focus:** Three-way TB comparison, CSV export, UX polish
> **New sprint:** Added per auditor recommendation for three-way comparison capability

#### Three-Way TB Comparison
- [x] `compare_three_periods()` in `multi_period_comparison.py` — wraps two-way, enriches with budget variance
  - Support: Prior Year vs Current Year vs Budget/Forecast
  - Third period optional — gracefully degrade to two-way when absent
  - BudgetVariance dataclass: budget_balance, variance_amount, variance_percent, variance_significance
  - ThreeWayMovementSummary: extends two-way with budget_label, budget totals, over/under/on budget counts
  - ThreeWayLeadSheetSummary: budget_total, budget_variance, budget_variance_percent per lead sheet
- [x] POST `/audit/compare-three-way` endpoint (require_verified_user)
- [x] Frontend three-way UI: `+ Add Budget/Forecast` toggle, third FileDropZone, budget label input
  - Conditional budget columns in AccountMovementTable and CategoryMovementSection
  - BudgetSummaryCards: over/under/on budget counts
  - Grid layout adjusts 2-col → 3-col when budget enabled

#### Export
- [x] CSV export: `export_movements_csv()` in `multi_period_comparison.py`
  - Handles both two-way and three-way (budget columns conditional)
  - Includes lead sheet summary section and summary statistics
  - UTF-8 BOM encoding for Excel compatibility
- [x] POST `/export/csv/movements` endpoint (require_verified_user)
- [x] Frontend Export CSV button with blob download and filename extraction
- [x] Zero-Storage: exports generated in-memory, streamed to user

#### Tests & Verification
- [x] 37 new tests in `test_three_way_comparison.py` (10 test classes)
  - TestThreeWayComparison (7), TestBudgetVariance (7), TestUnmatchedBudget (4)
  - TestThreeWayLeadSheets (3), TestCsvExportTwoWay (5), TestCsvExportThreeWay (2)
  - TestSerialization (4), TestThreeWayApiEndpoint (2), TestCsvExportApiEndpoint (3)
- [x] `pytest` passes (753 total: 716 + 37 new)
- [x] `npm run build` passes (20 routes)

#### Review
**Files Created:**
- `backend/tests/test_three_way_comparison.py` (37 tests)

**Files Modified:**
- `backend/multi_period_comparison.py` (added compare_three_periods, export_movements_csv, 3 dataclasses)
- `backend/main.py` (added 2 Pydantic models, 2 new endpoints)
- `frontend/src/hooks/useMultiPeriodComparison.ts` (three-way types, exportCsv, isExporting)
- `frontend/src/hooks/index.ts` (added BudgetVariance export)
- `frontend/src/app/tools/multi-period/page.tsx` (budget toggle, 3-col grid, CSV export button)

---

### Sprint 64: JE Testing — Backend Foundation + Config + Dual-Date — COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic
> **Focus:** GL parsing engine, data model, Tier 1 tests (structural), config dataclass, dual-date support
> **Council additions:** JETestingConfig dataclass, entry_date/posting_date columns, multi-currency detect-and-warn, GL data quality scoring

#### Data Model
- [x] Create `backend/je_testing_engine.py` — core JE testing framework (~750 lines)
  - JournalEntry dataclass: entry_id, entry_date, posting_date, account, description, debit, credit, posted_by, source, reference, currency
  - FlaggedEntry dataclass: entry + test metadata + severity + issue + confidence + details
  - TestResult dataclass: test_name, test_key, test_tier, entries_flagged, total_entries, flag_rate, severity, description, flagged_entries
  - CompositeScore dataclass: score (0-100), risk_tier, tests_run, total_entries, total_flagged, flag_rate, flags_by_severity, top_findings
  - JETestingConfig dataclass: configurable thresholds (balance_tolerance, round_amount_threshold, unusual_amount_stddev, etc.)
  - JETestingResult: composite_score, test_results, data_quality, multi_currency_warning, column_detection
- [x] GL file parser: detect_gl_columns() + parse_gl_entries()
  - 13 GL column types with weighted regex patterns
  - Required columns: date, account, debit/credit (or single amount)
  - Optional columns: description, reference, posted_by, source, currency, entry_id
  - Dual-date support: entry_date vs posting_date auto-detection
  - Manual column mapping override support
- [x] RiskTier enum: LOW (0-9), ELEVATED (10-24), MODERATE (25-49), HIGH (50-74), CRITICAL (75+)
- [x] TestTier enum: STRUCTURAL, STATISTICAL, ADVANCED
- [x] Severity enum: HIGH, MEDIUM, LOW

#### GL Data Quality Scoring
- [x] GLDataQuality dataclass: completeness_score, field_fill_rates, detected_issues, total_rows
  - Tracks fill rates per column (date, account, amount, description, reference, posted_by, etc.)
  - Flags low fill rates and zero-amount entries
  - Weighted scoring: date (30%), account (30%), amount (25%), optional fields (15%)

#### Multi-Currency Detection
- [x] detect_multi_currency() identifies multiple currencies via currency column
- [x] MultiCurrencyWarning with currencies_found, primary_currency, entry_counts_by_currency
- [x] Warning message only — no conversion attempted

#### Tier 1 Tests — Structural (5 tests)
- [x] **T1: Unbalanced Entries** — Groups by entry_id/reference, flags debit≠credit, severity by difference
- [x] **T2: Missing Fields** — Flags blank account, date, or zero amount
- [x] **T3: Duplicate Entries** — Exact match on date + account + amount + description (case-insensitive)
- [x] **T4: Round Dollar Amounts** — $100K/$50K/$10K patterns, sorted by amount, configurable max flags
- [x] **T5: Unusual Amounts** — Per-account z-score analysis, configurable stddev threshold
- [x] run_test_battery() orchestrates all 5 tests
- [x] calculate_composite_score() with weighted severity scoring + multi-flag multiplier

#### Tests & Verification
- [x] 91 tests in `test_je_testing.py` (14 test classes)
  - TestGLColumnDetection (13), TestGLParsing (7), TestSafeHelpers (10)
  - TestDataQuality (4), TestMultiCurrency (5)
  - TestUnbalancedEntries (7), TestMissingFields (6), TestDuplicateEntries (5)
  - TestRoundAmounts (9), TestUnusualAmounts (7)
  - TestCompositeScoring (7), TestBattery (2), TestRunJETesting (5), TestSerialization (4)
- [x] `pytest` passes (844 total: 753 + 91 new)
- [x] `npm run build` passes (20 routes)

#### Review
**Files Created:**
- `backend/je_testing_engine.py` (JE testing engine — ~750 lines)
- `backend/tests/test_je_testing.py` (91 tests across 14 classes)

**No files modified** — Sprint 64 is a standalone backend module with no frontend or API changes.

---

### Sprint 65: JE Testing — Statistical Tests + Benford Pre-Checks — COMPLETE ✅
> **Complexity:** 7/10 | **Agent Lead:** BackendCritic + QualityGuardian
> **Focus:** Benford's Law with pre-validation, date-based tests, composite scoring, calibration fixtures
> **Council additions:** Benford minimum thresholds (500 entries, 2 orders of magnitude), synthetic GL test fixtures, context weighting

#### Benford Pre-Check Validation (Council + Auditor recommendation)
- [x] Minimum entry count: 500 journal entries required for Benford analysis
  - Below threshold: skip Benford test, return "Insufficient data" result (not a failure)
- [x] Minimum magnitude range: entries must span 2+ orders of magnitude ($10→$1,000+)
- [x] Exclude amounts <$1 from Benford analysis (sub-dollar entries distort distribution)
- [x] Return pre-check results alongside Benford results for transparency

#### Tier 1 Tests — Statistical (3 tests)
- [x] **T6: Benford's Law** — First-digit distribution analysis
  - Chi-squared statistic calculation (8 degrees of freedom)
  - MAD (Mean Absolute Deviation) thresholds: conforming (<0.006), acceptable (0.006-0.012), marginally acceptable (0.012-0.015), nonconforming (>0.015)
  - Return expected vs actual distribution, deviation by digit
  - Flag individual entries whose first digits fall in most-deviated buckets
- [x] **T7: Weekend/Holiday Postings** — Flag entries posted on Saturday/Sunday
  - Configurable via JETestingConfig: some businesses post on weekends legitimately
  - Return count and percentage of weekend entries
- [x] **T8: Month-End Clustering** — Flag unusual concentration of entries in last 3 days of month
  - Compare last-3-day volume to monthly average
  - Significance threshold: >2x average daily volume (configurable)

#### Context Weighting (Council addition)
- [x] Weight weekend/holiday postings by amount (large weekend entries more suspicious than small ones)
- [x] Weight round-dollar amounts by context — deferred account-type weighting to Tier 2 (Sprint 68)

#### Composite Scoring Engine
- [x] Score calculation: weighted sum of test results
  - Each test contributes based on flag_rate x severity_weight
  - 1.25x multiplier for entries triggering 3+ different test types
  - Normalize to 0-100 scale
- [x] Top findings generator: rank flagged entries by composite risk
- [x] Summary statistics: total entries, total flagged, flag rate, risk tier

#### Scoring Calibration Fixtures (Council addition — QualityGuardian priority)
- [x] Create synthetic GL test fixtures with known risk profiles
  - "Clean" GL: LOW risk tier
  - "Moderate risk" GL: LOW-ELEVATED tier (comparative ordering validated)
  - "High risk" GL: MODERATE-CRITICAL tier with known fraud indicators
- [x] Validate scoring engine produces expected tiers for each fixture
- [x] 47 new tests for statistical tests + scoring engine + calibration (138 total JE tests)
- [x] `pytest` passes (891 passed, 1 known flaky perf test)

#### Review
- **Tests:** 138 JE testing tests (91 Sprint 64 + 47 Sprint 65), 891 total backend
- **Frontend:** Clean build, 20 routes
- **Key additions:** BenfordResult dataclass, _get_first_digit/_parse_date helpers, T6-T8 statistical tests
- **Learnings:** Non-Benford test data must span 2+ orders of magnitude to pass prechecks; scoring calibration tiers are relative (comparative assertions more robust than absolute tier assertions)

---

### Sprint 66: JE Testing — Frontend MVP + Platform Rebrand — COMPLETE ✅
> **Complexity:** 7/10 | **Agent Lead:** FrontendExecutor + FintechDesigner
> **Focus:** JE Testing upload UI + results display + Benford chart + platform homepage rebrand
> **Change:** Platform Rebrand moved here from Sprint 62 per auditor/council recommendation

#### API Endpoint
- [x] POST `/audit/journal-entries` — accepts GL file, runs Tier 1 battery, returns results
  - Zero-Storage: file processed in-memory, results ephemeral
  - Returns: composite_score, risk_tier, test_results[], flagged_entries[], benford_distribution, data_quality

#### Frontend — Standalone Tool Route `/tools/journal-entry-testing`
> **CEO Directive:** This is a separate tool, not a feature of TB Diagnostics.
- [x] Create `/tools/journal-entry-testing` page as standalone tool experience
  - Own hero header with tool-specific icon (shield motif)
  - Own upload flow — completely independent from TB Diagnostics and Multi-Period
  - Persistent "Journal Entry Testing" identity in nav and breadcrumb
- [x] GLFileUpload: single dropzone for GL extract (reuse dropzone pattern)
  - Accepted formats: CSV, XLSX
  - File size limit: 50MB (consistent with existing limits)
- [x] JEScoreCard: large composite score display with animated SVG ring, risk tier badge
- [x] TestResultGrid: grid of test result cards showing flag counts and severity, expandable detail
- [x] GLDataQualityBadge: completeness score with animated progress bar, field fill rates
- [x] BenfordChart: recharts bar chart comparing expected vs actual first-digit distribution
  - Deviation highlighting (clay-* bars for nonconforming digits)
  - Conformity badge (conforming/acceptable/marginally/nonconforming)
  - Pre-check status display for insufficient data
  - MAD and chi-squared stats

#### Platform Homepage Rebrand (deferred from Sprint 62)
- [x] Transform `/` from redirect into platform marketing page
  - New Hero Section: "The Complete Audit Intelligence Suite"
  - Sub-headline: Zero-Storage + professional-grade + three tools
  - Primary CTA: "Explore Our Tools" + "Get Started Free"
- [x] Tool Showcase Section: three tool cards with distinct icons, badges, descriptions
  - Trial Balance Diagnostics → `/tools/trial-balance` (Headliner badge)
  - Multi-Period Comparison → `/tools/multi-period` (Tool 2 badge)
  - Journal Entry Testing → `/tools/journal-entry-testing` (Tool 3 badge)
- [x] Reused FeaturePillars, ProcessTimeline, DemoZone components
- [x] Footer with Pacioli motto
- [x] `npm run build` passes (20 routes)

#### Review
- **Backend:** POST `/audit/journal-entries` endpoint with rate limiting and verified user auth
- **Frontend:** 4 new components (JEScoreCard, TestResultGrid, GLDataQualityBadge, BenfordChart), 1 hook (useJETesting), 1 type file (jeTesting.ts)
- **Pages:** Full JE Testing tool page + Platform homepage (replaced redirect)
- **Tests:** 891 backend passed (no new backend tests — endpoint tests planned Sprint 67)
- **Build:** Clean, 20 routes

---

### Sprint 67: JE Testing — Results Table + Export + Testing Memo — COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor + BackendCritic
> **Focus:** Flagged entry table, filtering, export, auto-generated testing memo
> **Council addition:** JE Testing Memo per PCAOB AS 1215 / ISA 530 documentation requirements

#### Frontend — Results Detail
- [x] FlaggedEntryTable (8/10 complexity): sortable, filterable table of flagged entries
  - Columns: Test, Account, Date, Amount, Severity, Issue
  - Filter by test type, severity, search text
  - Expandable row detail (click to expand)
  - Pagination (25 items per page)
- [x] FilterBar: search input + severity dropdown + test type dropdown (integrated into FlaggedEntryTable)

#### JE Testing Memo (Council addition — unanimous agreement)
- [x] Auto-generated PDF memo documenting the JE testing engagement
  - Header: client name, period tested, date of testing, preparer
  - Scope: total entries tested, date range, GL source description (leader dots)
  - Methodology: list of tests applied with brief description of each (table)
  - Results summary: composite score, risk tier, flag counts by test (leader dots + table)
  - Findings: top flagged entries with risk explanation
  - Conclusion: overall assessment with professional language (risk-tier-aware)
  - Reference numbers: JET-YYYY-MMDD-NNN format
- [x] Reuse existing PDF generator pattern (Renaissance Ledger aesthetic)
- [x] "Download Testing Memo" button alongside export options on results page

#### Export
- [x] PDF memo export via POST `/export/je-testing-memo` (workpaper format with sign-off fields)
- [x] CSV export for flagged entries via POST `/export/csv/je-testing` (UTF-8 BOM)
- [x] Zero-Storage: exports generated in-memory, streamed to user
- [x] `npm run build` passes (20 routes)
- [x] FlaggedEntryTable integrated into JE Testing page below TestResultGrid
- [x] Export buttons (Download Testing Memo + Export Flagged CSV) in action bar

#### Review
- **Backend:** `je_testing_memo_generator.py` (~350 lines) with Renaissance Ledger aesthetic, 2 new export endpoints
- **Frontend:** FlaggedEntryTable component with sort/filter/pagination, export buttons integrated into page
- **Tests:** 890 backend passed (2 pre-existing flaky: temp file + perf), 138 JE tests, clean frontend build
- **Build:** Clean, 20 routes

---

### Sprint 68: JE Testing — Tier 2 Tests + Threshold Config UI — COMPLETE
> **Complexity:** 6/10 | **Agent Lead:** BackendCritic + FrontendExecutor
> **Focus:** User/time-based anomaly tests, configurable threshold UI
> **Council addition:** Threshold Config UI integrated into Practice Settings page (not a new page)

#### Tier 2 Tests (5 tests)
- [x] **T9: Single-User High-Volume** — Flag users posting >X% of total entries (opt-in: requires posted_by)
- [x] **T10: After-Hours Postings** — Flag entries posted outside business hours (opt-in: requires timestamp data)
- [x] **T11: Sequential Numbering Gaps** — Flag gaps in entry reference numbers (opt-in: requires entry_id)
- [x] **T12: Backdated Entries** — Flag entries where posting_date significantly differs from entry_date (opt-in: dual dates)
- [x] **T13: Suspicious Keywords** — Flag descriptions containing audit-sensitive keywords (25 keywords, confidence-weighted)

#### Threshold Config UI (Council addition — deferred from Sprint 64 data model)
- [x] JE Testing section in Practice Settings page (`/settings/practice`)
- [x] Tiered presets: Conservative / Standard / Permissive / Custom (4-button selector)
- [x] Key threshold overrides: Round Amount, Unusual Stddev, User Volume %, Backdate Days, Keyword Confidence
- [x] Enable/disable toggles for 5 optional tests (T7, T10-T13)
- [x] Saved as `je_testing_config` field in PracticeSettings (Pydantic + TypeScript)
- [x] Zero-Storage: config is practice settings (stored), not financial data

#### Integration
- [x] Add Tier 2 tests to JETestBattery (opt-in based on available columns)
- [x] Tier 2 tests auto-contribute to composite scoring via existing SEVERITY_WEIGHTS
- [x] TestResultGrid already handles STATISTICAL tier display (no changes needed)
- [x] 69 new tests (207 total JE tests)
- [x] `pytest` passes (961 total)
- [x] `npm run build` passes (20 routes)

#### Review
- **Backend:** 5 new test functions + 2 helpers (_extract_hour, _extract_number) + SUSPICIOUS_KEYWORDS list + 15 new config fields
- **Frontend:** JE Testing section in Practice Settings with preset selector, threshold overrides, test toggles
- **Types:** JETestingConfig interface, presets, defaults in settings.ts; je_testing_config in PracticeSettings
- **Tests:** 69 new Tier 2 tests covering all 5 tests + helpers + edge cases
- **Build:** Clean, 20 routes

---

### Sprint 69: JE Testing — Tier 3 + Sampling + Fraud Indicators — COMPLETE
> **Complexity:** 7/10 | **Agent Lead:** BackendCritic + QualityGuardian
> **Focus:** Advanced statistical tests, stratified sampling, deeper fraud indicators
> **CEO decision:** Full stratified sampling included (not deferred to Phase VII)

#### Tier 3 Tests (5 tests)
- [x] **T14: Reciprocal Entries** — Flag matching debit/credit pairs posted close together (potential round-tripping)
- [x] **T15: Just-Below-Threshold** — Flag entries just below common approval thresholds ($5K, $10K, $25K, $50K) + split detection
- [x] **T16: Account Frequency Anomaly** — Flag accounts receiving entries at unusual frequency vs historical (z-score)
- [x] **T17: Description Length Anomaly** — Flag entries with unusually short or blank descriptions vs account norms
- [x] **T18: Unusual Account Combinations** — Flag rarely-seen debit/credit account pairings

#### Stratified Sampling (CEO approved — full implementation)
- [x] Sampling engine: stratified random sampling from full GL population
  - Stratify by: account category, amount range, posting period, user
  - CSPRNG via `secrets` module (PCAOB AS 2315 compliance)
  - Configurable sample size: percentage or fixed count per stratum
- [x] Sampling parameters UI: 3-step flow (SamplingPanel component)
  - Step 1: Select stratification criteria (checkboxes)
  - Step 2: Preview stratum counts and set sample sizes
  - Step 3: Execute sampling and display selected entries
- [x] Sample results: strata table with population/sampled/rate
- [x] Audit trail: sampling seed + parameters recorded for reproducibility

#### Deeper Fraud Indicators (Council addition — expanded scope)
- [x] T14 enhanced: cross-account round-tripping detection
- [x] T15 enhanced: split transaction detection (same user, same day, total exceeds threshold)
- [x] T18 implemented: rare debit/credit account pairing detection

#### Polish
- [x] T14-T18 registered in run_test_battery (18 tests total)
- [x] Frontend TestResultGrid updated with Advanced tier (T9-T18)
- [x] SamplingPanel component (3-step: configure → preview → results)
- [x] 2 new API endpoints: POST /audit/journal-entries/sample + /sample/preview
- [x] Sampling types added to jeTesting.ts
- [x] Comprehensive test suite for Tier 3 + sampling
- [x] `pytest` passes
- [x] `npm run build` passes

**Delivery Summary:**
- **Backend:** 5 Tier 3 test functions + sampling engine (preview + execute) with CSPRNG + 16 new config fields
- **API:** 2 new sampling endpoints (sample + preview) with rate limiting and Zero-Storage compliance
- **Frontend:** SamplingPanel (3-step flow), TestResultGrid advanced tier, updated types with sampling interfaces
- **Tests:** Comprehensive Tier 3 + sampling tests

---

### Sprint 70: Diagnostic Zone Protection + Phase VI Wrap — PLANNED
> **Complexity:** 2/10 | **Agent Lead:** QualityGuardian
> **Focus:** Re-enable diagnostic zone protection, final verification

- [ ] Re-enable diagnostic zone protection for authenticated users
- [ ] Verify all three tool routes respect auth gating (verified users only)
- [ ] Verify navigation shows three distinct top-level tool entries
- [ ] Homepage marketing: each tool has its own demo/showcase section
- [ ] Update CLAUDE.md with Phase VI completion status
- [ ] Update project version to 0.60.0
- [ ] Full regression: `pytest` (all ~735 tests) + `npm run build` + frontend tests
- [ ] Phase VI retrospective in lessons.md

---

### Phase VI Summary Table
> **Resequenced 2026-02-06:** Auditor + Agent Council review. Rebrand deferred to Sprint 66, tools-first priority.

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 61 | Housekeeping + Multi-Period Foundation | 3/10 | BackendCritic | COMPLETE |
| 62 | Route Scaffolding + Multi-Period API/Frontend | 6/10 | FrontendExecutor + BackendCritic | COMPLETE |
| 63 | Multi-Period Polish + Three-Way Comparison | 4/10 | BackendCritic + FrontendExecutor | COMPLETE |
| 64 | JE Testing — Backend Foundation + Config + Dual-Date | 5/10 | BackendCritic | COMPLETE |
| 65 | JE Testing — Statistical Tests + Benford Pre-Checks | 7/10 | BackendCritic + QualityGuardian | COMPLETE |
| 66 | JE Testing — Frontend MVP + Platform Rebrand | 7/10 | FrontendExecutor + FintechDesigner | COMPLETE |
| 67 | JE Testing — Results Table + Export + Testing Memo | 5/10 | FrontendExecutor + BackendCritic | COMPLETE |
| 68 | JE Testing — Tier 2 Tests + Threshold Config UI | 6/10 | BackendCritic + FrontendExecutor | COMPLETE |
| 69 | JE Testing — Tier 3 + Sampling + Fraud Indicators | 7/10 | BackendCritic + QualityGuardian | COMPLETE |
| 70 | Diagnostic Zone Protection + Wrap | 2/10 | QualityGuardian | PLANNED |

### Deferred Items
- **Contra-Account Validator** — Requires industry-specific accounting rules (all agents: defer indefinitely)
- **Print Styles** — Accounting expert: "Print is legacy" (all agents: not worth the sprint)
- **Batch Upload Processing** — Foundation built (Sprint 38-39), processing pipeline deferred until user demand
- **Multi-Currency Conversion** — Detection added in Sprint 64; full conversion support deferred to Phase VII
- **Full Population Sampling UI** — Stratified sampling of flagged entries in Sprint 69; broader population sampling tools deferred to Phase VII
