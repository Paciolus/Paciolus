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

### Sprint 70: Diagnostic Zone Protection + Phase VI Wrap — COMPLETE
> **Complexity:** 2/10 | **Agent Lead:** QualityGuardian
> **Focus:** Re-enable diagnostic zone protection, final verification

- [x] Re-enable diagnostic zone protection for authenticated users
  - TB Diagnostics: added `isVerified` check, unverified users see "Verify Your Email" CTA
  - Multi-Period: added `isVerified` check + `VerificationBanner`, unverified users see "Verify Your Email" CTA
  - JE Testing: already had verification gate (Sprint 66)
- [x] Verify all three tool routes respect auth gating (verified users only)
  - 3-state rendering: guest → Sign In CTA, authenticated unverified → VerificationBanner + blocked, verified → full access
  - Backend endpoints already protected with `require_verified_user` (Sprint 59)
- [x] Verify navigation shows three distinct top-level tool entries
  - Homepage nav: TB Diagnostics | Multi-Period | JE Testing | Sign In/Profile
  - Each tool page nav: cross-tool links with active tool highlighted
- [x] Homepage marketing: each tool has its own demo/showcase section
  - Three tool cards with unique icons, badges, descriptions, CTAs
  - FeaturePillars, ProcessTimeline, DemoZone components
- [x] Update CLAUDE.md with Phase VI completion status
- [x] Update project version to 0.60.0
- [x] Full regression: `pytest` (1022 passed, 1 skipped) + `npm run build` (20 routes)
- [x] Phase VI retrospective in lessons.md

#### Review
**Files Modified:**
- `frontend/src/app/tools/trial-balance/page.tsx` (added isVerified check, gated diagnostic zone)
- `frontend/src/app/tools/multi-period/page.tsx` (added isVerified check, VerificationBanner, gated upload section)
- `frontend/package.json` (version 0.1.0 → 0.60.0)
- `CLAUDE.md` (Phase VI complete, updated capabilities, removed diagnostic zone tension)
- `tasks/todo.md` (Sprint 70 complete, review section)
- `tasks/lessons.md` (Phase VI retrospective)

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
| 70 | Diagnostic Zone Protection + Wrap | 2/10 | QualityGuardian | COMPLETE |

### Deferred Items
> **Reviewed:** Phase VI close-out council review (2026-02-06). Deleted 4 items: Contra-Account Validator (no roadmap), Print Styles (replaced by PDF export), Batch Upload Processing (shipped Sprint 38-39), Full Population Sampling UI (shipped Sprint 69).

- **Multi-Currency Conversion** — Detection shipped Sprint 64 (`detect_multi_currency()`, `MultiCurrencyWarning`); conversion logic (exchange rate table, FX variance analysis) deferred beyond Phase VII

---

## Phase VII: Financial Statements + Duplicate Payments + Bank Reconciliation

> **Source:** Future State Consultant Feature Catalog + Agent Council Review (2026-02-06)
> **Scope:** 10 sprints (71-80) covering one Tool 1 enhancement + two new tools
> **Selection criteria:** Value × Leverage — prioritized features that reuse existing engines
> **Estimated New Code:** ~8,000 lines (4,500 backend + 3,500 frontend)
> **Estimated New Tests:** 200+ backend tests

### CEO Directive: Leverage Existing Infrastructure
> **STRICT REQUIREMENT:** New features MUST reuse existing engines where possible.
> - Financial Statements reuses lead sheet mapping (A-Z) + category totals + ratio engine
> - Duplicate Payment Detector clones JE Testing pattern (column detection → parse → test battery → score → export)
> - Bank Reconciliation adapts Multi-Period dual-file upload + account matching

### Agent Council Consensus
- **BackendCritic:** Financial Statements first (85% built), AP Testing second (70% reuse), Bank Rec third (50% reuse)
- **FrontendExecutor:** All three follow established component patterns (Section/Card, upload → results → export)
- **QualityGuardian:** Scoring calibration uses comparative assertions (lesson from Sprint 65); Zero-Storage compliance audited per feature
- **FintechDesigner:** Tool 4 + Tool 5 get distinct visual identities within Oat & Obsidian palette

### Phase VII Summary Table

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 71 | Financial Statements — Backend Builder + Export | 4/10 | BackendCritic | COMPLETE |
| 72 | Financial Statements — Frontend Integration + Polish | 3/10 | FrontendExecutor | COMPLETE |
| 73 | AP Testing — Backend Foundation + Tier 1 Tests | 5/10 | BackendCritic | COMPLETE |
| 74 | AP Testing — Tier 2-3 Tests + Scoring + API | 6/10 | BackendCritic + QualityGuardian | COMPLETE |
| 75 | AP Testing — Frontend MVP (Upload + Results + Export) | 6/10 | FrontendExecutor | COMPLETE |
| 76 | AP Testing — Polish (Recovery Card, Vendor Chart, Config) | 4/10 | FrontendExecutor + FintechDesigner | COMPLETE |
| 77 | Bank Rec — Backend Engine + API (V1 Exact Match) | 5/10 | BackendCritic | COMPLETE |
| 78 | Bank Rec — Frontend Page (Dual Upload + Match Table) | 5/10 | FrontendExecutor | COMPLETE |
| 79 | Bank Rec — Export + Polish (Bridge + Categories) | 4/10 | FrontendExecutor + BackendCritic | COMPLETE |
| 80 | Navigation + Homepage + Regression + Phase VII Wrap | 2/10 | QualityGuardian + FintechDesigner | COMPLETE |

---

### Pre-Sprint 71: API Router Decomposition — COMPLETE
> **Complexity:** 3/10 | **Agent Lead:** IntegratorLead (refactoring)
> **Focus:** Decompose monolithic main.py (4,690 lines) into 15 APIRouter modules
> **Zero behavioral changes:** No API URL changes, no frontend impact

#### Completed
- [x] Created `backend/shared/` package: `rate_limits.py`, `helpers.py`, `schemas.py`
- [x] Created `backend/routes/` package: 15 router files + `__init__.py`
  - `health.py` (2 endpoints), `auth_routes.py` (7), `users.py` (2), `activity.py` (4)
  - `clients.py` (7), `settings.py` (6), `diagnostics.py` (3), `audit.py` (3)
  - `export.py` (8), `benchmarks.py` (4), `trends.py` (3), `prior_period.py` (3)
  - `multi_period.py` (3), `adjustments.py` (10), `je_testing.py` (3)
- [x] Reduced `main.py` from 4,690 → 63 lines (app + middleware + router registration)
- [x] Re-exported `require_verified_user` for 3 test files' `from main import` compatibility
- [x] All 1,023 backend tests pass, 0 failures
- [x] Frontend build passes (20 routes, 0 errors)

---

### Sprint 71: Financial Statements — Backend Builder + Export — COMPLETE
> **Complexity:** 4/10 | **Agent Lead:** BackendCritic
> **Focus:** Transform lead sheet grouping + category totals into formatted financial statements
> **Leverage:** 85% reuse — lead_sheet_mapping.py (A-Z categories), pdf_generator.py, excel_generator.py

#### Backend — Financial Statement Builder
- [x] Create `backend/financial_statement_builder.py` (~210 lines)
  - `FinancialStatementBuilder(lead_sheet_grouping)` — accepts serialized dict
  - `build()` → `FinancialStatements` dataclass
  - `_get_lead_sheet_balance(letter)` — 0.0 if missing
  - `_build_balance_sheet()` → list[StatementLineItem] (A-K with sign conventions)
  - `_build_income_statement()` → list[StatementLineItem] (L-O with sign conventions)
  - `StatementLineItem` dataclass: label, amount, indent_level, is_subtotal, is_total, lead_sheet_ref
  - `FinancialStatements` dataclass: balance_sheet, income_statement, totals, is_balanced, to_dict()
  - Sign conventions: Assets as-is, Liabilities/Equity/Revenue flip sign, COGS/OpEx as-is, Other flipped

#### Export Extensions
- [x] Add `generate_financial_statements_pdf()` to `pdf_generator.py` (+120 lines)
  - Standalone function (not subclassing PaciolusReportGenerator)
  - Balance Sheet + Income Statement pages with leader dots, subtotals, double-rule totals
  - Balance verification seal: "✓ BALANCED" or "⚠ OUT OF BALANCE ($X.XX)"
  - Workpaper signoff section, Renaissance Ledger aesthetic
- [x] Add `generate_financial_statements_excel()` to `excel_generator.py` (+110 lines)
  - "Balance Sheet" + "Income Statement" worksheets
  - Indented line items, bold subtotals, double-underline totals
  - Column C shows lead sheet references in small gray font
  - Oat & Obsidian theme, workpaper signoff section
- [x] Add `POST /export/financial-statements` endpoint in `routes/export.py` (+60 lines)
  - `FinancialStatementsInput` Pydantic model
  - PDF/Excel via `?format=pdf|excel` query param
  - `require_verified_user` auth, 400 on empty summaries
  - StreamingResponse pattern matches existing endpoints

#### Tests
- [x] Create `backend/tests/test_financial_statements.py` (27 tests)
  - 21 builder tests: BS current/noncurrent assets, liabilities, equity, totals, balanced/unbalanced, IS revenue/COGS/gross profit/opex/operating income/other income/expense/net income, missing lead sheets, empty grouping, serialization, zero-revenue edge case, metadata
  - 3 PDF tests: non-empty bytes, type check, workpaper fields
  - 3 Excel tests: non-empty bytes, Balance Sheet tab, Income Statement tab
- [x] `pytest` passes: 1,050 total (1,023 existing + 27 new)
- [x] `npm run build` passes: 20 routes, 0 errors

#### Review
**Files Created:**
- `backend/financial_statement_builder.py` (~210 lines) — core engine with dataclasses + builder
- `backend/tests/test_financial_statements.py` (~400 lines) — 27 tests with 4 fixtures

**Files Modified:**
- `backend/pdf_generator.py` (+120 lines) — `generate_financial_statements_pdf()` standalone function
- `backend/excel_generator.py` (+110 lines) — `generate_financial_statements_excel()` standalone function
- `backend/routes/export.py` (+60 lines) — `FinancialStatementsInput` model + `/export/financial-statements` endpoint

---

### Sprint 72: Financial Statements — Frontend Integration + Polish — COMPLETE
> **Complexity:** 3/10 | **Agent Lead:** FrontendExecutor
> **Focus:** Add financial statement export to Tool 1 results, inline preview

#### Frontend
- [x] `FinancialStatementsPreview` component with client-side statement builder
  - Collapsible section with Balance Sheet / Income Statement tabs
  - Client-side builder mirrors backend `FinancialStatementBuilder` sign conventions
  - Balance verification badge (BALANCED / OUT OF BALANCE)
  - Key metrics grid: Total Assets, Total Liabilities, Revenue, Net Income
  - PDF/Excel export buttons calling `/export/financial-statements`
  - `font-mono` for amounts, `font-serif` for headers
  - Oat & Obsidian token compliance throughout
- [x] Barrel export: `components/financialStatements/index.ts`
- [x] Integrated into `trial-balance/page.tsx` after LeadSheetSection
  - Conditionally renders when `auditResult.lead_sheet_grouping` exists
- [x] Updated Tool 1 description on homepage to mention financial statement generation
- [x] `npm run build` passes (20 routes, 0 errors)

---

### Sprint 73: AP Testing — Backend Foundation + Tier 1 Tests — COMPLETE ✅
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic
> **Focus:** AP column detection, data model, Tier 1 duplicate detection tests
> **Leverage:** 70% clone of je_testing_engine.py structure

#### Data Model
- [x] Create `backend/ap_testing_engine.py` (~850 lines)
  - Duplicated: `RiskTier`, `Severity`, `TestTier` enums (independent tool — no cross-imports)
  - `APColumnType` enum: 11 values (INVOICE_NUMBER through PAYMENT_METHOD + UNKNOWN)
  - 10 `AP_*_PATTERNS` regex lists for each column type
  - `detect_ap_columns(column_names)` → `APColumnDetectionResult` (greedy assignment)
  - `APPayment` dataclass: single `amount` field (not debit/credit)
  - `parse_ap_payments(rows, detection)` → `list[APPayment]`
  - `FlaggedPayment`, `APTestResult`, `APCompositeScore`, `APTestingResult` dataclasses
  - `APTestingConfig` dataclass with Tier 1-3 thresholds
  - `APDataQuality` assessment (vendor/amount/payment_date weighted)

#### Tier 1 Tests — Structural (5 tests)
- [x] **AP-T1: Exact Duplicate Payments** — key=(vendor, invoice#, amount, date), HIGH severity, 0.95 confidence
- [x] **AP-T2: Missing Critical Fields** — vendor blank→HIGH, amount==0→HIGH, date blank→MEDIUM
- [x] **AP-T3: Check Number Gaps** — sequential gaps, opt-in, severity tiered by gap size
- [x] **AP-T4: Round Dollar Amounts** — $100K/$50K(HIGH), $25K(MEDIUM), $10K(LOW) — AP-specific $25K tier
- [x] **AP-T5: Payment Before Invoice** — severity: >30d HIGH, >7d MEDIUM, ≤7d LOW

#### Tests
- [x] Create `backend/tests/test_ap_testing.py` (93 tests across 14 classes)
  - Column detection (12), parsing (8), helpers (6), data quality (5)
  - Exact duplicates (12), missing fields (8), check gaps (8), round amounts (8), payment before invoice (8)
  - Scoring (6), battery (3), full pipeline (5), serialization (4)
- [x] `pytest` passes — 93 AP tests + 1,143 total backend tests, 0 failures

---

### Sprint 74: AP Testing — Tier 2-3 Tests + Scoring + API — COMPLETE
> **Complexity:** 6/10 | **Agent Lead:** BackendCritic + QualityGuardian
> **Focus:** Statistical and fraud indicator tests, composite scoring, API endpoint

#### Tier 2 Tests — Statistical (5 tests)
- [x] **AP-T6: Fuzzy Duplicate Payments** — same vendor + same amount (±tolerance) + different dates within window
- [x] **AP-T7: Invoice Number Reuse** — same invoice# across 2+ different vendors (always HIGH)
- [x] **AP-T8: Unusual Payment Amounts** — per-vendor z-score outliers (HIGH z>5, MEDIUM z>4, LOW z>3)
- [x] **AP-T9: Weekend Payments** — payments on Saturday/Sunday, amount-weighted severity
- [x] **AP-T10: High-Frequency Vendors** — same vendor ≥5 payments on one day (HIGH ≥10, MEDIUM ≥5)

#### Tier 3 Tests — Fraud Indicators (3 tests)
- [x] **AP-T11: Vendor Name Variations** — SequenceMatcher ratio ≥0.85 but names differ
- [x] **AP-T12: Just-Below-Threshold** — within 5% below $5K/$10K/$25K/$50K/$100K + same-day split detection
- [x] **AP-T13: Suspicious Descriptions** — 16 AP-specific keywords (petty cash, void reissue, override, etc.)

#### Scoring & API
- [x] `run_ap_test_battery()` — orchestrates all 13 tests (was 5)
- [x] `calculate_ap_composite_score()` — weighted severity scoring (generic N-test support, no changes needed)
- [x] `run_ap_testing()` — main entry point (unchanged, battery produces 13 results)
- [x] Scoring calibration: clean_score ≤ moderate_score (comparative assertions)
- [x] `POST /audit/ap-payments` endpoint in `routes/ap_testing.py` (16th router)
  - `require_verified_user`, `RATE_LIMIT_AUDIT`, Zero-Storage compliance
- [x] `AP_SUSPICIOUS_KEYWORDS` constant (16 weighted entries with phrase support)

#### Config Expansion
- [x] `APTestingConfig` — 14 new fields for T6-T13 thresholds and toggles
- [x] `import statistics`, `from difflib import SequenceMatcher`

#### Tests
- [x] 72 new tests (8 per Tier 2-3 test + 5 calibration + 3 API route registration)
- [x] Updated existing battery tests (5→13) and pipeline tests (5→13)
- [x] `pytest tests/test_ap_testing.py -v` — 165 tests, all pass
- [x] `pytest` — 1,215 total backend tests, 0 failures

---

### Sprint 75: AP Testing — Frontend MVP — COMPLETE
> **Complexity:** 6/10 | **Agent Lead:** FrontendExecutor
> **Focus:** Standalone Tool 4 page, upload, score display, flagged payment table

#### Types & Hook
- [x] Create `frontend/src/types/apTesting.ts` (~110 lines) — AP types (APPaymentData, FlaggedAPPayment, APTestResult, APCompositeScore, APDataQuality, APColumnDetection, APTestingResult + theme maps)
- [x] Create `frontend/src/hooks/useAPTesting.ts` (~90 lines) — endpoint `/audit/ap-payments`
- [x] Export from `frontend/src/hooks/index.ts`

#### Tool Page
- [x] Create `frontend/src/app/tools/ap-testing/page.tsx` (~310 lines)
  - Clone from JE Testing page structure
  - Hero: "AP Payment Testing" with 13-test battery description
  - `isVerified` gate + `VerificationBanner` (Sprint 70 pattern)
  - Single-file dropzone: "Upload AP Payment Register"
  - Zero-Storage notice
  - Navigation: TB Diagnostics / Multi-Period / JE Testing (links) + AP Testing (active sage)
  - No export buttons (Sprint 76), no Benford/Sampling panels

#### Components
- [x] Create `frontend/src/components/apTesting/` directory:
  - `APScoreCard.tsx` (~120 lines) — composite score ring + risk tier
  - `APTestResultGrid.tsx` (~160 lines) — test cards by tier (T1-T5 Structural, T6-T10 Statistical, T11-T13 Fraud Indicators)
  - `FlaggedPaymentTable.tsx` (~260 lines) — sortable/filterable table
    - Columns: Test, Vendor, Amount, Date, Severity, Issue
    - Filter by test type, severity, search text (vendor, invoice#, description)
    - Pagination (25 per page)
  - `APDataQualityBadge.tsx` (~90 lines) — completeness score with field fill rates
  - `index.ts` barrel export
- [x] `npm run build` passes — 0 errors, route `/tools/ap-testing` generated

---

### Sprint 76: AP Testing — Polish + Config — COMPLETE
> **Complexity:** 4/10 | **Agent Lead:** FrontendExecutor + FintechDesigner
> **Focus:** Export (PDF memo + CSV), frontend export buttons, threshold config in Practice Settings
> **Deferred:** RecoverySummaryCard, VendorFrequencyChart (require computed data not in current API response)

#### Export
- [x] Create `backend/ap_testing_memo_generator.py` (~280 lines, adapted from je_testing_memo_generator.py)
  - APT- reference prefix, ISA 240 / ISA 500 / PCAOB AS 2401 references
  - 13 AP test descriptions, scope/methodology/results/findings/conclusion sections
- [x] CSV export for flagged payments via `POST /export/csv/ap-testing`
  - Headers: Test, Test Key, Tier, Severity, Vendor, Invoice #, Payment Date, Amount, Check #, Description, Issue, Confidence
  - Summary section: composite score, risk tier, total payments, total flagged, flag rate
- [x] PDF testing memo via `POST /export/ap-testing-memo` (clone JE memo endpoint pattern)
- [x] `APTestingExportInput` Pydantic model in `backend/routes/export.py`
- [x] Frontend export buttons on AP testing results page
  - "Download Testing Memo" (sage accent, disabled while exporting)
  - "Export Flagged CSV" (obsidian, disabled while exporting)

#### Threshold Config
- [x] `ap_testing_config` field added to `backend/practice_settings.py`
- [x] `APTestingConfig` interface + presets in `frontend/src/types/settings.ts`
  - 14 config fields matching backend `APTestingConfig` dataclass
  - Conservative / Standard / Permissive / Custom presets
- [x] AP Testing section in Practice Settings (`/settings/practice`)
  - Preset selector (4 buttons, same pattern as JE)
  - Key thresholds: Round Amount ($), Duplicate Date Window (days), Unusual Amount Sensitivity (σ), Keyword Sensitivity (%)
  - Toggle tests: T3 Check Number Gaps, T5 Payment Before Invoice, T7 Invoice Reuse, T9 Weekend Payments, T10 High-Frequency Vendors, T11 Vendor Variations, T12 Just-Below-Threshold
- [x] `npm run build` passes (21 routes, 0 errors)
- [x] `pytest tests/test_ap_testing.py` passes (165 tests)

#### Deferred to Future Sprint
- [ ] `RecoverySummaryCard.tsx` — requires computed recovery amounts not in current API response
- [ ] `VendorFrequencyChart.tsx` — requires per-vendor duplicate counts not in current API response

#### Review
**Files Created:**
- `backend/ap_testing_memo_generator.py` (~280 lines)

**Files Modified:**
- `backend/routes/export.py` (+APTestingExportInput, +2 endpoints: ap-testing-memo, csv/ap-testing)
- `backend/practice_settings.py` (+ap_testing_config field)
- `frontend/src/types/settings.ts` (+APTestingConfig, +presets, +defaults, +labels)
- `frontend/src/app/settings/practice/page.tsx` (+AP Testing section with presets, thresholds, toggles)
- `frontend/src/app/tools/ap-testing/page.tsx` (+export buttons, +export handlers)

---

### Sprint 77: Bank Rec — Backend Engine + API — COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic
> **Focus:** Transaction matching engine (V1 exact match), reconciliation summary
> **Leverage:** 50% reuse — AP testing column detection pattern, file parsing infra

#### Backend Engine
- [x] Create `backend/bank_reconciliation.py` (~500 lines)
  - `MatchType` enum: MATCHED, BANK_ONLY, LEDGER_ONLY
  - `BankRecConfig` dataclass: amount_tolerance=0.01, date_tolerance_days=0
  - `BankColumnType` enum + weighted regex patterns for column detection
  - `BankColumnDetectionResult` dataclass with greedy assignment
  - `BankTransaction` / `LedgerTransaction` dataclasses with to_dict()
  - `ReconciliationMatch` dataclass: bank_txn, ledger_txn, match_type, match_confidence
  - `ReconciliationSummary` dataclass: matched/bank_only/ledger_only counts + amounts + reconciling difference
  - `_parse_date()` — multi-format parser (9 formats)
  - `_safe_float()` — currency-aware with parenthetical negative support
  - `match_transactions()` — V1 exact matching (greedy, largest-first)
  - `calculate_summary()` — aggregates match results
  - `export_reconciliation_csv()` — 4 sections (matched, bank-only, ledger-only, summary)
  - `reconcile_bank_statement()` — main entry point with manual mapping support

#### API
- [x] `POST /audit/bank-reconciliation` — dual-file upload (bank + ledger), column mappings, require_verified_user
- [x] `POST /export/csv/bank-rec` — CSV export with StreamingResponse
- [x] Router registered in `routes/__init__.py`

#### Tests
- [x] Create `backend/tests/test_bank_reconciliation.py` (55 tests)
  - TestDateParsing (8): multi-format + invalid/empty/None
  - TestSafeFloat (7): plain, string, currency, parentheses, empty, non-numeric, None
  - TestColumnDetection (6): standard, alternate, minimal, low-confidence, to_dict, greedy
  - TestTransactionParsing (4): bank, ledger, empty, to_dict
  - TestExactMatching (11): all/none/partial, tolerance edge/exceeded, duplicates, one-to-one, empty, single, date tolerance
  - TestSummaryCalculation (5): balanced, bank excess, ledger excess, mixed, to_dict
  - TestCsvExport (3): basic, empty, special chars
  - TestMainEntry (4): full pipeline, manual mapping, to_dict, empty files
  - TestAPIRoute (4): route registered, POST method, export route, tag
  - TestMatchColumn (3): exact, partial, no match
- [x] All 55 tests pass

---

### Sprint 78: Bank Rec — Frontend Page — COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor
> **Focus:** Dual-file upload, match results table, CSV export
> **Leverage:** Multi-Period dual-file upload pattern, FlaggedPaymentTable component pattern

#### Types & Hook
- [x] Create `frontend/src/types/bankRec.ts` — interfaces matching BankRecResult.to_dict()
- [x] Create `frontend/src/hooks/useBankReconciliation.ts` — dual-file upload, auth cascade

#### Tool Page
- [x] Create `frontend/src/app/tools/bank-rec/page.tsx`
  - 5-tool navigation (TB, Multi-Period, JE Testing, AP Testing, Bank Rec)
  - Hero: "Bank Statement Reconciliation" with reconciliation badge
  - `isVerified` gate + `VerificationBanner` + Guest CTA
  - Dual FileDropZone: "Bank Statement" (left) + "GL Cash Detail" (right)
  - "Reconcile" button (disabled until both files uploaded)
  - CSV export via POST `/export/csv/bank-rec`
  - Column detection warnings for low-confidence files
  - 3 info cards (idle state): Exact Matching, Auto-Detection, CSV Export

#### Components
- [x] `MatchSummaryCards.tsx` — 3 animated cards + reconciling difference indicator
- [x] `BankRecMatchTable.tsx` — sortable/filterable/paginated match table with color-coded rows
- [x] `index.ts` barrel export
- [x] `npm run build` passes

---

### Sprint 79: Bank Rec — Export + Polish — COMPLETE
> **Complexity:** 4/10 | **Agent Lead:** FrontendExecutor + BackendCritic
> **Focus:** Reconciliation bridge, auto-categorization, match rate surfacing

- [x] Export CSV button — download reconciliation report (shipped Sprint 78)
- [x] ReconciliationBridge component — standard bank rec workpaper format (bank → adjusted bank, GL → adjusted GL)
- [x] Auto-categorization badges: Outstanding Check/Deposit, Deposit in Transit, Unrecorded Check
- [x] Match rate % and total_bank/total_ledger surfaced in MatchSummaryCards
- [x] Row number display in match table description cell
- [x] Zero-Storage notice on page (shipped Sprint 78)
- [x] `npm run build` passes

---

### Sprint 80: Navigation + Homepage + Regression + Phase VII Wrap — COMPLETE
> **Complexity:** 2/10 | **Agent Lead:** QualityGuardian + FintechDesigner
> **Focus:** Platform integration, full regression, Phase VII close-out

- [x] Update homepage tool showcase: 3 → 5 tool cards
  - Tool 4: AP Payment Testing (icon: overlapping documents, badge: "Tool 4")
  - Tool 5: Bank Reconciliation (icon: two-arrow exchange, badge: "Tool 5")
  - Updated hero copy: "Three integrated tools" → "Five integrated tools"
  - Updated showcase heading: "Three Tools. One Platform." → "Five Tools. One Platform."
  - Added 2 nav links (AP Testing, Bank Rec) to homepage navigation
- [x] Update navigation across all tool pages (5 cross-tool links)
  - TB Diagnostics: replaced tagline with 5-link nav + standardized auth section
  - Multi-Period: restructured ToolNav to match standard pattern, standardized active style (border-b)
  - JE Testing: added AP Testing + Bank Rec links
  - AP Testing: added Bank Rec link
  - Bank Rec: already had all 5 links (no changes needed)
  - All pages now use consistent active style: `text-sage-400 border-b border-sage-400/50`
  - All pages now use consistent inactive style: `text-oatmeal-400 hover:text-oatmeal-200 transition-colors`
- [x] Full regression: `npm run build` (22 routes, 0 errors) + `pytest` (1,270 tests)
- [x] Update CLAUDE.md with Phase VII completion status
- [x] Update version to 0.70.0
- [x] Phase VII retrospective in lessons.md

#### Review
**Files Modified:**
- `frontend/src/app/page.tsx` (+2 tool cards, +2 nav links, copy updates)
- `frontend/src/app/tools/trial-balance/page.tsx` (replaced tagline with 5-link nav)
- `frontend/src/app/tools/multi-period/page.tsx` (restructured ToolNav, standardized styles)
- `frontend/src/app/tools/journal-entry-testing/page.tsx` (+2 nav links)
- `frontend/src/app/tools/ap-testing/page.tsx` (+1 nav link)
- `frontend/package.json` (version 0.60.0 → 0.70.0)
- `CLAUDE.md` (Phase VII → COMPLETE, version 0.70.0, updated capabilities)
- `tasks/todo.md` (Sprint 80 → COMPLETE)
- `tasks/lessons.md` (Phase VII retrospective)

---

### Sprint 81: Code Quality — Shared Components + Session TTL — COMPLETE
> **Complexity:** 2/10 | **Agent Lead:** IntegratorLead (refactoring)
> **Focus:** Eliminate duplicated navigation, drag/drop handlers, and fix session memory leak
> **Trigger:** Codebase audit identified 3 immediate-priority issues across 84 Python + 159 TypeScript files

- [x] Session TTL + cleanup for `routes/adjustments.py`
  - Added `_SESSION_TTL_SECONDS = 3600` (1 hour) + `_MAX_SESSIONS = 500` cap
  - `_cleanup_expired_sessions()` runs on every access via `time.monotonic()`
  - LRU eviction: when at capacity, evict oldest session before creating new
  - `clear_all_adjustments()` now also cleans up timestamps
- [x] Extract shared `ToolNav` component (`components/shared/ToolNav.tsx`)
  - `ToolKey` type: `'tb-diagnostics' | 'multi-period' | 'je-testing' | 'ap-testing' | 'bank-rec'`
  - `TOOLS` array with key, label, href — single source of truth for navigation
  - `showBrandText` prop for TB's logo + "Paciolus" text treatment
  - Calls `useAuth()` internally — eliminates prop threading from all pages
  - Barrel-exported from `components/shared/index.ts`
  - Applied to all 5 tool pages, replacing 50-66 lines of inline nav each
- [x] Extract `useFileUpload` hook (`hooks/useFileUpload.ts`)
  - Encapsulates: isDragging, fileInputRef, handleDrop, handleDragOver, handleDragLeave, handleFileSelect, resetFileInput
  - Barrel-exported from `hooks/index.ts`
  - Applied to 3 pages: TB Diagnostics, JE Testing, AP Testing
  - Not applied to Bank Rec / Multi-Period (specialized FileDropZone sub-components with different props)
- [x] `npm run build` passes (22 routes, 0 errors)
- [x] `pytest tests/test_adjusting_entries.py` passes (45 tests)

#### Review
**Files Created:**
- `frontend/src/components/shared/ToolNav.tsx` (~65 lines) — shared navigation component
- `frontend/src/hooks/useFileUpload.ts` (~52 lines) — shared drag/drop hook

**Files Modified:**
- `backend/routes/adjustments.py` (+session TTL, cleanup, LRU eviction)
- `frontend/src/components/shared/index.ts` (+ToolNav export)
- `frontend/src/hooks/index.ts` (+useFileUpload export)
- `frontend/src/app/tools/trial-balance/page.tsx` (ToolNav + useFileUpload, ~90 lines removed)
- `frontend/src/app/tools/multi-period/page.tsx` (ToolNav, ~62-line local ToolNav function removed)
- `frontend/src/app/tools/journal-entry-testing/page.tsx` (ToolNav + useFileUpload, ~70 lines removed)
- `frontend/src/app/tools/ap-testing/page.tsx` (ToolNav + useFileUpload, ~70 lines removed)
- `frontend/src/app/tools/bank-rec/page.tsx` (ToolNav, ~52 lines removed)

---

### Sprint 82: Code Quality — Backend File Helpers + Frontend Export/Auth Utilities — COMPLETE
> **Complexity:** 2/10 | **Agent Lead:** IntegratorLead (refactoring)
> **Focus:** Extract duplicated CSV/Excel parsing, fetch-blob-download, and auth error handling into shared utilities
> **Trigger:** Codebase audit (Sprint 81) identified 3 short-term priority items

#### Backend: Shared Helper Functions
- [x] `parse_uploaded_file(file_bytes, filename)` → `tuple[list[str], list[dict]]` — CSV/Excel parsing
- [x] `parse_json_mapping(raw_json, log_label)` → `Optional[dict[str, str]]` — JSON column mapping
- [x] `safe_download_filename(raw_name, suffix, ext)` → `str` — sanitized timestamped filenames
- [x] Added to `backend/shared/helpers.py` with imports (io, json, pandas, datetime)

#### Backend: Route Updates (5 files)
- [x] `routes/ap_testing.py` — `parse_uploaded_file` + `parse_json_mapping` (removed io, json, pandas imports)
- [x] `routes/je_testing.py` — both helpers across 3 handlers (removed io, pandas imports)
- [x] `routes/bank_reconciliation.py` — both helpers for dual-file parsing + `safe_download_filename` (removed io, json, pandas, datetime imports)
- [x] `routes/audit.py` — `parse_json_mapping` for column_mapping (left overrides/sheets inline — unique logic)
- [x] `routes/export.py` — `safe_download_filename` across 10 sites (removed datetime import)

#### Frontend: `downloadBlob` Utility
- [x] Created `frontend/src/lib/downloadBlob.ts` — fetch → blob → anchor → download pattern
- [x] Updated `app/tools/ap-testing/page.tsx` — 2 export handlers simplified
- [x] Updated `app/tools/journal-entry-testing/page.tsx` — 2 export handlers simplified
- [x] Updated `app/tools/bank-rec/page.tsx` — 1 export handler simplified

#### Frontend: `useAuditUpload` Generic Hook
- [x] Created `frontend/src/hooks/useAuditUpload.ts` — generic status/result/error + auth error handling
- [x] Rewrote `useAPTesting.ts` as thin wrapper (~35 lines, was ~92)
- [x] Rewrote `useJETesting.ts` as thin wrapper (~35 lines, was ~92)
- [x] Rewrote `useBankReconciliation.ts` as thin wrapper (~42 lines, was ~93)
- [x] Added exports to `hooks/index.ts`

#### Verification
- [x] `npm run build` passes (22 routes, 0 errors)
- [x] `pytest` — 1,270 tests pass (targeted: 533 across AP/JE/bank-rec/adjustments)
- [x] No behavioral changes — pure refactoring

#### Review
**Files Created:**
- `frontend/src/lib/downloadBlob.ts` (~30 lines) — blob download utility
- `frontend/src/hooks/useAuditUpload.ts` (~90 lines) — generic audit upload hook

**Files Modified:**
- `backend/shared/helpers.py` (+3 functions, +5 imports)
- `backend/routes/ap_testing.py` (simplified with helpers, removed 3 imports)
- `backend/routes/je_testing.py` (simplified 3 handlers, removed 2 imports)
- `backend/routes/bank_reconciliation.py` (simplified with helpers, removed 5 imports)
- `backend/routes/audit.py` (column_mapping uses parse_json_mapping)
- `backend/routes/export.py` (10 filename sites use safe_download_filename, removed datetime import)
- `frontend/src/app/tools/ap-testing/page.tsx` (2 export handlers use downloadBlob)
- `frontend/src/app/tools/journal-entry-testing/page.tsx` (2 export handlers use downloadBlob)
- `frontend/src/app/tools/bank-rec/page.tsx` (1 export handler uses downloadBlob)
- `frontend/src/hooks/useAPTesting.ts` (thin wrapper using useAuditUpload)
- `frontend/src/hooks/useJETesting.ts` (thin wrapper using useAuditUpload)
- `frontend/src/hooks/useBankReconciliation.ts` (thin wrapper using useAuditUpload)
- `frontend/src/hooks/index.ts` (+useAuditUpload, +useBankReconciliation exports)

---

### Not Currently Pursuing
> **Reviewed:** Agent Council + Future State Consultant feature evaluation (2026-02-06)
> **Criteria:** Features below were deprioritized due to low leverage (no reuse of existing engines), niche markets, regulatory maintenance burden, or off-brand positioning.

| Feature | Consultant # | Reason Not Pursuing |
|---------|:---:|---|
| Loan Amortization Generator | 5 | Commodity calculator; no reuse of diagnostic engines; off-brand ("audit intelligence" not "calculators") |
| Depreciation Calculator | 6 | MACRS table maintenance; better served by existing tools (Excel, QuickBooks) |
| TB to Financial Statements — Cash Flow | 7 (partial) | Indirect method requires change-in-balance analysis beyond current category totals; Phase VIII candidate |
| Expense Classification Validator | 10 | Extends classification engine but creates accounting judgment liability; needs disclaimers and careful scoping; Phase VIII candidate |
| Intercompany Elimination Checker | 11 | Niche market (multi-entity only); N-file upload is new paradigm; Phase VIII candidate if user demand |
| 1099 Preparation Helper | 12 | US-only, seasonal, annual IRS rule changes create maintenance burden |
| Book-to-Tax Adjustment Calculator | 13 | Tax preparer persona (not our core audit user); regulatory complexity |
| W-2/W-3 Reconciliation Tool | 14 | Payroll niche; seasonal; different user persona |
| Three-Way Match Validator | 15 | High complexity (7/10); needs 3 different file parsers; Phase VIII candidate |
| Cash Flow Projector | 16 | Requires AR/AP aging + payment history; complex multi-file inputs |
| Lease Accounting (ASC 842) | 17 | New domain (8/10 complexity); high value but needs dedicated research sprint |
| Revenue Recognition (ASC 606) | 18 | Extreme complexity (9/10); contract-specific logic; avoid |
| Segregation of Duties Checker | 19 | IT audit persona; different user base |
| Ghost Employee Detector | 20 | Strong demo story, JE Testing clone pattern; Phase VIII candidate (council interest) |
| Multi-Currency Conversion | — | Detection shipped Sprint 64; conversion needs exchange rate infrastructure |

### Phase IX Candidates (Shortlist for Future Evaluation)
> Re-evaluate after Phase VIII ships.

1. **Expense Classification Validator** — 62% reuse, needs legal review for accounting judgment liability
2. **Three-Way Match Validator** — Re-evaluate if integration APIs are built
3. **Cash Flow Statement — Direct Method** — Requires AP/payroll detail integration; evaluate after Payroll Testing ships

---

## Phase VIII: Cash Flow Statement + Payroll & Employee Testing

> **Source:** Agent Council deliberation (2026-02-07) — 5 candidates evaluated, 2 selected
> **Scope:** 7 sprints (83-89) covering Cash Flow (Tool 1 enhancement) + Payroll Testing (Tool 6)
> **Strategy:** Highest reuse first (Cash Flow 75%), then proven clone pattern (Payroll 68%)
> **Estimated New Code:** ~4,200 lines (2,700 backend + 1,500 frontend)
> **Estimated New Tests:** ~130 backend + ~10 frontend

### Phase VIII Summary Table

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 83 | Cash Flow Statement — Backend Engine | 4/10 | BackendCritic | COMPLETE |
| 84 | Cash Flow Statement — Frontend + Export | 3/10 | FrontendExecutor | COMPLETE |
| 85 | Payroll Testing — Backend Foundation + Tier 1 | 5/10 | BackendCritic | COMPLETE |
| 86 | Payroll Testing — Tier 2-3 + Scoring + API | 6/10 | BackendCritic + QualityGuardian | COMPLETE |
| 87 | Payroll Testing — Frontend MVP | 5/10 | FrontendExecutor | COMPLETE |
| 88 | Payroll Testing — Export + Config + Polish | 4/10 | FrontendExecutor + FintechDesigner | COMPLETE |
| 89 | Phase VIII Wrap — Navigation + Homepage + Regression | 2/10 | QualityGuardian + FintechDesigner | COMPLETE |

---

### Sprint 83: Cash Flow Statement — Backend Engine — COMPLETE
> **Complexity:** 4/10 | **Agent Lead:** BackendCritic
- [x] Extend `backend/financial_statement_builder.py` with cash flow dataclasses + builder
- [x] Operating Activities (Indirect Method per ASC 230 / IAS 7)
- [x] Investing / Financing Activities
- [x] Reconciliation check + `to_dict()` serialization
- [x] 30 tests in `test_cash_flow_statement.py` — all passing

### Sprint 84: Cash Flow Statement — Frontend + Export — COMPLETE
> **Complexity:** 3/10 | **Agent Lead:** FrontendExecutor
- [x] Cash flow PDF + Excel export in `pdf_generator.py` / `excel_generator.py`
- [x] Cash Flow tab in `FinancialStatementsPreview` component
- [x] Updated export routes

### Sprint 85: Payroll Testing — Backend Foundation + Tier 1 — COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic
- [x] `backend/payroll_testing_engine.py` — column detection, parsing, data model
- [x] PR-T1 to PR-T5 (Structural tests: duplicates, missing fields, round amounts, post-termination, check gaps)
- [x] 92 tests in `test_payroll_testing.py` — all passing

### Sprint 86: Payroll Testing — Tier 2-3 + Scoring + API — COMPLETE
> **Complexity:** 6/10 | **Agent Lead:** BackendCritic + QualityGuardian
- [x] PR-T6 to PR-T8 (Statistical: z-score, pay frequency, Benford's Law)
- [x] PR-T9 to PR-T11 (Fraud: ghost employee, duplicate bank/address, duplicate tax ID)
- [x] `backend/routes/payroll_testing.py` — POST /audit/payroll-testing
- [x] 139 tests — all passing (1,448 total backend)

### Sprint 87: Payroll Testing — Frontend MVP — COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor
- [x] `types/payrollTesting.ts`, `hooks/usePayrollTesting.ts`
- [x] 4 components: PayrollScoreCard, PayrollTestResultGrid, FlaggedEmployeeTable, PayrollDataQualityBadge
- [x] `app/tools/payroll-testing/page.tsx` — full tool page
- [x] ToolNav updated with payroll-testing link (moved from Sprint 89)

### Sprint 88: Payroll Testing — Export + Config + Polish — COMPLETE
> **Complexity:** 4/10 | **Agent Lead:** FrontendExecutor + FintechDesigner
- [x] `backend/payroll_testing_memo_generator.py` — PDF memo (ISA 240/500, PCAOB AS 2401)
- [x] POST /export/payroll-testing-memo + POST /export/csv/payroll-testing
- [x] Frontend export buttons (Download Testing Memo + Export Flagged CSV)
- [x] `payroll_testing_config` in practice_settings.py
- [x] PayrollTestingConfig types + presets in settings.ts
- [x] Payroll Testing section in Practice Settings page
- [x] `npm run build` passes (23 routes), `pytest` passes (139 payroll tests)

### Sprint 89: Phase VIII Wrap — Navigation + Homepage + Regression — COMPLETE
> **Complexity:** 2/10 | **Agent Lead:** QualityGuardian + FintechDesigner
- [x] Added Tool 6 card to homepage toolCards array
- [x] Updated hero copy: "Five" → "Six integrated tools"
- [x] Updated showcase heading: "Five Tools" → "Six Tools"
- [x] Added Payroll Testing to homepage nav links
- [x] Verified all 6 tool pages have consistent ToolNav (6 links each)
- [x] Updated `CLAUDE.md` with Phase VIII completion + version 0.80.0
- [x] `npm run build` passes (23 routes)
- [x] `pytest` passes (1,448 total backend tests)

### Phase VIII Review
> **Shipped:** 7 sprints (83-89) + 2 code quality sprints (81-82)
> **New Backend Code:** ~2,700 lines
> **New Frontend Code:** ~1,500 lines
> **New Tests:** 178 backend (30 cash flow + 139 payroll + 9 misc)
> **Files Created:** ~12 (engine, route, memo generator, types, hook, page, 4 components, barrel)
> **Files Modified:** ~15 (financial_statement_builder, pdf/excel generators, export routes, ToolNav, homepage, practice_settings, hooks/index, settings types)

---

## Phase IX: Code Quality + Three-Way Match + Classification Validator

> **Source:** Agent Council deliberation (2026-02-07) — CEO selected "Professional Depth" option
> **Scope:** 7 sprints (90-96) covering Code Quality + Three-Way Match (Tool 7) + Classification Validator (TB Enhancement)
> **Strategy:** Clean up duplication first (Sprint 90), then build Tool 7 on clean foundation, enhance Tool 1 last
> **Estimated New Code:** ~3,800 lines (2,400 backend + 1,400 frontend)
> **Estimated New Tests:** ~155 backend

### Phase IX Summary Table

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 90 | Code Quality — Shared Testing Utilities | 4/10 | QualityGuardian | COMPLETE |
| 91 | Three-Way Match — Backend Foundation | 5/10 | BackendCritic | COMPLETE |
| 92 | Three-Way Match — Matching Algorithm + API | 7/10 | BackendCritic + QualityGuardian | COMPLETE |
| 93 | Three-Way Match — Frontend MVP | 5/10 | FrontendExecutor | COMPLETE |
| 94 | Three-Way Match — Export + Config + Polish | 4/10 | FrontendExecutor + FintechDesigner | PENDING |
| 95 | Classification Validator — TB Enhancement | 5/10 | BackendCritic + AccountingExpertAuditor | PENDING |
| 96 | Phase IX Wrap — Navigation + Homepage + Regression | 2/10 | QualityGuardian + FintechDesigner | PENDING |

---

### Sprint 90: Code Quality — Shared Testing Utilities — COMPLETE
> **Complexity:** 4/10 | **Agent Lead:** QualityGuardian
> **Focus:** Extract duplicated enums, round-amount logic, memo generators, and frontend export hook
> **Result:** ~588 lines added, ~1,003 lines removed → ~415 lines net reduction

#### Backend — Shared Enums
- [x] Created `backend/shared/testing_enums.py` (~60 lines)
  - `RiskTier`, `TestTier`, `Severity` enums + `SEVERITY_WEIGHTS` dict
- [x] Updated `je_testing_engine.py` — replaced local enums with shared import
- [x] Updated `ap_testing_engine.py` — replaced local enums with shared import
- [x] Updated `payroll_testing_engine.py` — replaced local enums with shared import

#### Backend — Shared Round Amount Detection
- [x] Created `backend/shared/round_amounts.py` (~40 lines)
  - `ROUND_AMOUNT_PATTERNS_3TIER` (JE: $100K/$50K/$10K)
  - `ROUND_AMOUNT_PATTERNS_4TIER` (AP/Payroll: $100K/$50K/$25K/$10K)
- [x] Updated 3 engines to import shared patterns

#### Backend — Shared Memo Base
- [x] Created `backend/shared/memo_base.py` (~80 lines)
  - `RISK_TIER_DISPLAY`, `create_memo_styles()`, `build_memo_header()`, `build_scope_section()`
  - `build_methodology_section()`, `build_results_summary_section()`, `build_workpaper_signoff()`, `build_disclaimer()`
- [x] Rewrote `je_testing_memo_generator.py` to use shared base
- [x] Rewrote `ap_testing_memo_generator.py` to use shared base
- [x] Rewrote `payroll_testing_memo_generator.py` to use shared base

#### Frontend — Shared Export Hook
- [x] Created `frontend/src/hooks/useTestingExport.ts` (~50 lines)
  - `useTestingExport(memoEndpoint, csvEndpoint, fallbackMemoFilename, fallbackCsvFilename)`
  - Returns `{ exporting, handleExportMemo, handleExportCSV }`
- [x] Updated `ap-testing/page.tsx` to use `useTestingExport`
- [x] Updated `payroll-testing/page.tsx` to use `useTestingExport`
- [x] Updated `journal-entry-testing/page.tsx` to use `useTestingExport`
- [x] Exported from `frontend/src/hooks/index.ts`

#### Verification
- [x] `pytest` passes (1,448 existing tests — zero regressions)
- [x] `npm run build` passes (23 routes)

---

### Sprint 91: Three-Way Match — Backend Foundation — COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic
> **Focus:** Data models, column detection for PO/Invoice/Receipt files, parsing, data quality, config
> **Note:** Matching algorithm also included (planned for Sprint 92) since it was part of the same engine module

#### Engine
- [x] Created `backend/three_way_match_engine.py` (~1,500 lines)
  - Enums: `MatchDocumentType`, `MatchType`, `MatchRiskLevel`
  - PO/Invoice/Receipt column type enums with regex patterns
  - Column detection: `detect_po_columns()`, `detect_invoice_columns()`, `detect_receipt_columns()`
  - Data models: `PurchaseOrder`, `Invoice`, `Receipt` dataclasses with `to_dict()`
  - Detection results: `POColumnDetectionResult`, `InvoiceColumnDetectionResult`, `ReceiptColumnDetectionResult`
  - Parsing: `parse_purchase_orders()`, `parse_invoices()`, `parse_receipts()`
  - Data quality: `ThreeWayMatchDataQuality`, `assess_three_way_data_quality()`
  - Config: `ThreeWayMatchConfig` (7 configurable thresholds)
  - Matching: Phase 1 exact PO# + Phase 2 fuzzy (vendor 40% + amount 30% + date 30%)
  - Variance analysis: amount, quantity, price, date with severity tiers
  - Result aggregation: `ThreeWayMatchResult` with summary + risk assessment

#### Tests
- [x] Created `backend/tests/test_three_way_match.py` (62 tests)
  - TestHelpers (9): safe_float, safe_str, parse_date, vendor_similarity
  - TestPOColumnDetection (8): standard, alternate, minimal, empty, low confidence, requires_mapping, to_dict, notes
  - TestInvoiceColumnDetection (8): standard, alternate, without PO ref, empty, low confidence, bill number, to_dict, notes
  - TestReceiptColumnDetection (8): standard, GRN, minimal, empty, low confidence, without inv ref, to_dict, condition
  - TestPOParsing (6): valid, missing fields, empty, currency amounts, to_dict, row numbering
  - TestInvoiceParsing (6): valid, missing PO ref, empty, date fields, to_dict, row numbering
  - TestReceiptParsing (6): valid, invoice ref, empty, condition, to_dict, row numbering
  - TestDataQuality (5): full quality, empty, low PO ref issues, to_dict, partial fill rates
  - TestConfig (3): defaults, custom values, to_dict
  - TestEnums (3): match document type, match type, risk level

#### Verification
- [x] `pytest tests/test_three_way_match.py` — 62 tests pass
- [x] Engine compiles and all functionality verified

---

### Sprint 92: Three-Way Match — Matching Algorithm + API — COMPLETE
> **Complexity:** 7/10 | **Agent Lead:** BackendCritic + QualityGuardian
> **Focus:** API route, matching algorithm tests, router registration
> **Note:** Matching algorithm was included in engine file during Sprint 91; this sprint adds the API + comprehensive tests

#### API Endpoint
- [x] Created `backend/routes/three_way_match.py` (~95 lines)
  - `POST /audit/three-way-match` — 3 file uploads (po_file, invoice_file, receipt_file)
  - Optional per-file column mappings
  - `require_verified_user`, `RATE_LIMIT_AUDIT`, Zero-Storage compliance
  - Uses `parse_uploaded_file()` from `shared/helpers.py`
  - `clear_memory()` cleanup
- [x] Registered router in `backend/routes/__init__.py` (19th router)

#### Matching Algorithm Tests (52 new tests)
- [x] TestExactPOMatching (10): full 3-way, PO+invoice only, PO+receipt only, no match, multiple POs, case-insensitive, receipt via invoice ref, one-to-one, duplicate PO numbers, PO without number
- [x] TestFuzzyFallback (8): vendor match, disabled, below threshold, amount proximity, date proximity, composite below threshold, with receipt, only used for unmatched
- [x] TestVarianceAnalysis (10): amount/quantity/price/date variances, within tolerance, high/medium/low severity, null documents, to_dict
- [x] TestUnmatched (6): orphan POs/invoices/receipts, to_dict, mixed, preserves data
- [x] TestSummary (5): counts, amounts, risk low/high, to_dict
- [x] TestEdgeCases (5): empty files, single row, all unmatched, large dataset (100 rows), whitespace PO numbers
- [x] TestSerialization (4): match to_dict, full result, JSON safe, variance in result
- [x] TestAPIRouteRegistration (4): route registered, POST method, tag, all_routers

#### Verification
- [x] `pytest tests/test_three_way_match.py` — 114 tests pass (62 Sprint 91 + 52 Sprint 92)
- [x] `pytest` — 1,562 total tests pass (zero regressions)

---

### Sprint 93: Three-Way Match — Frontend MVP — COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor
> **Focus:** Tool 7 page with 3-file upload, match results display, variance table
> **Leverage:** Bank rec dual-upload as template, extended to 3 dropzones

#### Types & Hook
- [x] Created `frontend/src/types/threeWayMatch.ts` (~165 lines)
  - Types: `TWMMatchType`, `TWMRiskLevel`, `VarianceSeverity`, `POData`, `InvoiceData`, `ReceiptData`
  - `MatchVarianceData`, `ThreeWayMatchData`, `UnmatchedDocumentData`, `ThreeWayMatchSummaryData`
  - `ThreeWayMatchDataQuality`, `ColumnDetectionData`, `ThreeWayMatchResult`
  - Theme maps: `MATCH_TYPE_COLORS`, `MATCH_TYPE_LABELS`, `VARIANCE_SEVERITY_COLORS`, `RISK_COLORS`, `RISK_BG_COLORS`
- [x] Created `frontend/src/hooks/useThreeWayMatch.ts` (~45 lines)
  - Wrapper around `useAuditUpload<ThreeWayMatchResult>`
  - Custom `buildFormData` for 3 files: `po_file`, `invoice_file`, `receipt_file`
- [x] Exported from `frontend/src/hooks/index.ts`

#### Components
- [x] Created `frontend/src/components/threeWayMatch/MatchSummaryCard.tsx` (~85 lines)
  - Match rate cards (full/partial/material variances/net variance)
  - Risk assessment badge, amount totals by document type
- [x] Created `frontend/src/components/threeWayMatch/MatchResultsTable.tsx` (~215 lines)
  - Sortable/filterable/paginated table of matched documents
  - Columns: Vendor, PO#, Invoice#, Receipt#, PO Amt, Inv Amt, Variance, Type, Confidence
  - Filter by match type, search by vendor/PO#/invoice#, pagination (25 per page)
- [x] Created `frontend/src/components/threeWayMatch/UnmatchedDocumentsPanel.tsx` (~107 lines)
  - Collapsible panel with tabs for unmatched POs, Invoices, Receipts
  - Document details + reason for non-match
- [x] Created `frontend/src/components/threeWayMatch/VarianceDetailCard.tsx` (~116 lines)
  - Material variances grouped by type (amount/quantity/price/date)
  - Severity badges, amounts, percentages
- [x] Created `frontend/src/components/threeWayMatch/index.ts` — barrel export

#### Tool Page
- [x] Created `frontend/src/app/tools/three-way-match/page.tsx` (~380 lines)
  - 3-file FileDropZone layout (Purchase Orders, Invoices, Receipts/GRN)
  - "Run Match" button activates when all 3 files selected
  - Full results display: MatchSummaryCard, MatchResultsTable, VarianceDetailCard, UnmatchedDocumentsPanel
  - Auth gating, VerificationBanner, Guest CTA, Zero-Storage notice
  - 3 info cards for idle state (Phase 1: Exact PO#, Phase 2: Fuzzy, Analysis: Variance)
- [x] Added `'three-way-match'` to ToolNav `ToolKey` union + TOOLS array (7 tools)

#### Verification
- [x] `npm run build` passes (24 routes including `/tools/three-way-match`)
