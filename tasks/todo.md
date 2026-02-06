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

### Sprint 62: Route Scaffolding + Multi-Period API/Frontend — PLANNED
> **Complexity:** 6/10 | **Agent Lead:** FrontendExecutor + BackendCritic
> **Focus:** Tool route structure, multi-period API endpoint, dual-file upload UI, movement table
> **Change:** Rebrand deferred to Sprint 66 per auditor/council recommendation — tools-first priority

#### Route Scaffolding (from original Sprint 62)
- [ ] Create tool route structure (no visual rebrand yet)
  - `/tools/trial-balance` — TB Diagnostics (move from `/`)
  - `/tools/multi-period` — Multi-Period Comparison
  - `/tools/journal-entry-testing` — Journal Entry Testing (placeholder until Sprint 66)
- [ ] Platform navigation: Tools dropdown with links to each tool route
- [ ] Redirect `/` → `/tools/trial-balance` temporarily (full homepage rebrand in Sprint 66)
- [ ] Update all internal links that point to `/` expecting the diagnostic workspace

#### Backend API (from original Sprint 63)
- [ ] POST `/audit/compare-periods` endpoint
  - Accepts two audit result sets (current + prior) in request body
  - Returns MovementSummary with categorized account movements
  - Zero-Storage: both files processed in-memory, results ephemeral
- [ ] Movement summary statistics: net change by category, largest movements, new/closed account lists
- [ ] Lead sheet grouping for movement results
- [ ] 15+ API integration tests

#### Frontend — Standalone Tool Route `/tools/multi-period`
> **CEO Directive:** This is a separate tool, not a tab within TB Diagnostics.
- [ ] Create `/tools/multi-period` page as standalone tool experience
  - Own hero header with tool-specific icon (dual-document / timeline motif)
  - Own upload flow — completely independent from TB Diagnostics
  - Persistent "Multi-Period Comparison" identity in nav and breadcrumb
- [ ] DualFileUpload component: side-by-side dropzones for "Prior Period" and "Current Period"
  - Period labels (e.g., "FY2024", "FY2025") with text inputs
  - Reuse existing dropzone styling (Oat & Obsidian)
  - File validation: same format requirements as single-file upload
- [ ] ComparisonWorkspace component: orchestrates dual audit + comparison flow
  - State: priorFile, currentFile, priorResult, currentResult, comparison
  - Flow: upload both → audit both → compare → display results

#### Frontend — Results Display
- [ ] AccountMovementTable component (7/10 complexity)
  - Sortable columns: Account, Prior Balance, Current Balance, Change, Change %, Movement Type
  - Color-coded movement badges (sage=increase, clay=decrease, oatmeal=unchanged)
  - Significance indicators (material/significant/minor)
  - Filter by movement type and significance tier
- [ ] MovementSummaryCards: visual summary (NEW: X, CLOSED: X, SIGN_CHANGE: X, etc.)
- [ ] CategoryMovementSection: group by lead sheet with expand/collapse
- [ ] Account dormancy detection: flag UNCHANGED accounts with zero balance as "potentially dormant"
- [ ] `npm run build` passes

---

### Sprint 63: Multi-Period Polish + Three-Way Comparison — PLANNED
> **Complexity:** 4/10 | **Agent Lead:** BackendCritic + FrontendExecutor
> **Focus:** Three-way TB comparison, export, UX polish
> **New sprint:** Added per auditor recommendation for three-way comparison capability

#### Three-Way TB Comparison
- [ ] Extend compare_trial_balances() to accept 2-3 periods
  - Support: Prior Year vs Current Year vs Budget/Forecast
  - Third period optional — gracefully degrade to two-way when absent
- [ ] ThreeWayComparisonTable component: additional column for third period
  - Variance columns: Prior→Current, Budget→Current
  - Highlight where actuals deviate from both prior and budget
- [ ] Period selector: dropdown to choose which periods to compare

#### Export
- [ ] PDF export for multi-period comparison results
  - Movement summary page + detailed account movements
  - Reuse existing PDF generator pattern (Renaissance Ledger)
- [ ] CSV export for movement data
- [ ] Zero-Storage: exports generated in-memory, streamed to user

#### Polish
- [ ] Loading states for dual-file audit flow
- [ ] Error handling: mismatched account structures, different date ranges
- [ ] 10+ additional tests for three-way comparison
- [ ] `pytest` passes
- [ ] `npm run build` passes

---

### Sprint 64: JE Testing — Backend Foundation + Config + Dual-Date — PLANNED
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic
> **Focus:** GL parsing engine, data model, Tier 1 tests (structural), config dataclass, dual-date support
> **Council additions:** JETestingConfig dataclass, entry_date/posting_date columns, multi-currency detect-and-warn, GL data quality scoring

#### Data Model
- [ ] Create `backend/je_testing_engine.py` — core JE testing framework
  - JournalEntry dataclass: entry_id, entry_date, posting_date, account, description, debit, credit, posted_by, source, reference, currency
  - TestResult dataclass: test_name, test_tier, entries_flagged, total_entries, flag_rate, severity, details
  - JETestBattery class: orchestrates all tests, produces composite score
  - CompositeScore dataclass: score (0-100), risk_tier, tests_run, flags_by_tier, top_findings
  - JETestingConfig dataclass: configurable thresholds for all tests (defaults hardcoded, UI in Sprint 68)
    - round_amount_threshold, unusual_amount_stddev, weekend_posting_enabled, month_end_days, etc.
- [ ] GL file parser: CSV/Excel column detection for journal entry fields
  - Required columns: date, account, amount (or debit/credit)
  - Optional columns: description/memo, posted_by/user, source/module, reference/doc_number
  - Dual-date support: detect entry_date vs posting_date columns separately
  - Confidence-based column mapping (reuse existing column detection pattern)
- [ ] Risk tier enum: LOW (0-9), ELEVATED (10-24), MODERATE (25-49), HIGH (50-74), CRITICAL (75+)

#### GL Data Quality Scoring (Council addition)
- [ ] GLDataQuality dataclass: completeness_score, field_fill_rates, detected_issues
  - Track fill rates per column (e.g., 95% of entries have description, 60% have posted_by)
  - Flag quality issues: mixed date formats, blank descriptions, missing references
  - Return quality score (0-100) alongside test results to contextualize findings

#### Multi-Currency Detection (Council addition — CEO approved detect-and-warn)
- [ ] Detect multiple currencies in GL data (currency column or amount format analysis)
- [ ] Warn user if multi-currency detected: "Multi-currency GL detected. Results may be affected by exchange rate differences."
- [ ] Do NOT attempt conversion — detection and warning only

#### Tier 1 Tests — Structural (5 tests)
- [ ] **T1: Unbalanced Entries** — Flag entries where debits != credits (group by entry_id/reference)
- [ ] **T2: Missing Fields** — Flag entries with blank account, date, or amount
- [ ] **T3: Duplicate Entries** — Exact match on date + account + amount + description
- [ ] **T4: Round Dollar Amounts** — Flag entries at $X,000 or $X,00,000 (reuse rounding pattern from Sprint 42)
- [ ] **T5: Unusual Amounts** — Flag entries exceeding configurable stddev threshold (default 3x) of account's typical posting
- [ ] Create `backend/tests/test_je_testing.py` — 30+ tests for parser + Tier 1 tests + quality scoring
- [ ] `pytest` passes

---

### Sprint 65: JE Testing — Statistical Tests + Benford Pre-Checks — PLANNED
> **Complexity:** 7/10 | **Agent Lead:** BackendCritic + QualityGuardian
> **Focus:** Benford's Law with pre-validation, date-based tests, composite scoring, calibration fixtures
> **Council additions:** Benford minimum thresholds (500 entries, 2 orders of magnitude), synthetic GL test fixtures, context weighting

#### Benford Pre-Check Validation (Council + Auditor recommendation)
- [ ] Minimum entry count: 500 journal entries required for Benford analysis
  - Below threshold: skip Benford test, return "Insufficient data" result (not a failure)
- [ ] Minimum magnitude range: entries must span 2+ orders of magnitude ($10→$1,000+)
- [ ] Exclude amounts <$1 from Benford analysis (sub-dollar entries distort distribution)
- [ ] Return pre-check results alongside Benford results for transparency

#### Tier 1 Tests — Statistical (3 tests)
- [ ] **T6: Benford's Law** — First-digit distribution analysis
  - Chi-squared statistic calculation (8 degrees of freedom)
  - MAD (Mean Absolute Deviation) thresholds: conforming (<0.006), acceptable (0.006-0.012), marginally acceptable (0.012-0.015), nonconforming (>0.015)
  - Return expected vs actual distribution, deviation by digit
  - Flag individual entries whose first digits fall in most-deviated buckets
- [ ] **T7: Weekend/Holiday Postings** — Flag entries posted on Saturday/Sunday
  - Configurable via JETestingConfig: some businesses post on weekends legitimately
  - Return count and percentage of weekend entries
- [ ] **T8: Month-End Clustering** — Flag unusual concentration of entries in last 3 days of month
  - Compare last-3-day volume to monthly average
  - Significance threshold: >2x average daily volume (configurable)

#### Context Weighting (Council addition)
- [ ] Weight weekend/holiday postings by amount (large weekend entries more suspicious than small ones)
- [ ] Weight round-dollar amounts by context (reuse classification_rules.py weighted keyword pattern)
  - Loan/mortgage accounts: round amounts are normal → reduce flag severity
  - Revenue/expense accounts: round amounts more suspicious → maintain flag severity

#### Composite Scoring Engine
- [ ] Score calculation: weighted sum of test results
  - Each test contributes based on flag_rate x severity_weight
  - 1.25x multiplier for entries triggering 3+ different test types
  - Normalize to 0-100 scale
- [ ] Top findings generator: rank flagged entries by composite risk
- [ ] Summary statistics: total entries, total flagged, flag rate, risk tier

#### Scoring Calibration Fixtures (Council addition — QualityGuardian priority)
- [ ] Create synthetic GL test fixtures with known risk profiles
  - "Clean" GL: ~5% flag rate, LOW risk tier
  - "Moderate risk" GL: ~25% flag rate, MODERATE tier
  - "High risk" GL: ~60% flag rate, HIGH tier with known fraud indicators
- [ ] Validate scoring engine produces expected tiers for each fixture
- [ ] 25+ tests for statistical tests + scoring engine + calibration
- [ ] `pytest` passes

---

### Sprint 66: JE Testing — Frontend MVP + Platform Rebrand — PLANNED
> **Complexity:** 7/10 | **Agent Lead:** FrontendExecutor + FintechDesigner
> **Focus:** JE Testing upload UI + results display + Benford chart + platform homepage rebrand
> **Change:** Platform Rebrand moved here from Sprint 62 per auditor/council recommendation

#### API Endpoint
- [ ] POST `/audit/journal-entries` — accepts GL file, runs Tier 1 battery, returns results
  - Zero-Storage: file processed in-memory, results ephemeral
  - Returns: composite_score, risk_tier, test_results[], flagged_entries[], benford_distribution, data_quality

#### Frontend — Standalone Tool Route `/tools/journal-entry-testing`
> **CEO Directive:** This is a separate tool, not a feature of TB Diagnostics.
- [ ] Create `/tools/journal-entry-testing` page as standalone tool experience
  - Own hero header with tool-specific icon (magnifying glass / shield motif)
  - Own upload flow — completely independent from TB Diagnostics and Multi-Period
  - Persistent "Journal Entry Testing" identity in nav and breadcrumb
- [ ] GLFileUpload component: single dropzone for GL extract (reuse dropzone pattern)
  - Accepted formats: CSV, XLSX
  - File size limit: 50MB (consistent with existing limits)
- [ ] JEScoreCard: large composite score display with risk tier badge and color
- [ ] TestResultGrid: grid of test result cards showing flag counts and severity
- [ ] GLDataQualityBadge: show data quality score with fill rate indicators
- [ ] BenfordChart (8/10 complexity): bar chart comparing expected vs actual first-digit distribution
  - Use recharts (already installed) for bar chart
  - Expected distribution line overlay
  - Deviation highlighting (clay-* bars for nonconforming digits, not red-*)
  - Show pre-check status (sufficient data / insufficient data message)

#### Platform Homepage Rebrand (deferred from Sprint 62)
- [ ] Transform `/` from redirect into platform marketing page
  - New Hero Section: platform-level pitch ("Professional Audit Intelligence Suite")
  - Sub-headline: emphasize suite breadth + Zero-Storage + professional-grade
  - Primary CTA: "Explore Our Tools" or "Get Started Free"
- [ ] Tool Showcase Section: three tool cards
  - Each card: distinct icon, tool name, 2-line description, "Try It" CTA
  - Trial Balance Diagnostics → `/tools/trial-balance` (headliner)
  - Multi-Period Comparison → `/tools/multi-period`
  - Journal Entry Testing → `/tools/journal-entry-testing`
- [ ] Revise FeaturePillars: platform-level value props (Zero-Storage, Professional-Grade, Complete Toolkit)
- [ ] DemoZone: TB Diagnostics demo as headliner, teaser cards for other tools
- [ ] `npm run build` passes

---

### Sprint 67: JE Testing — Results Table + Export + Testing Memo — PLANNED
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor + BackendCritic
> **Focus:** Flagged entry table, filtering, export, auto-generated testing memo
> **Council addition:** JE Testing Memo per PCAOB AS 1215 / ISA 530 documentation requirements

#### Frontend — Results Detail
- [ ] FlaggedEntryTable (8/10 complexity): sortable, filterable table of flagged entries
  - Columns: Entry ID, Date, Account, Description, Amount, Tests Failed, Risk Score
  - Filter by test type, severity, date range
  - Expandable row detail showing which tests flagged the entry and why
  - Pagination for large result sets (100+ flagged entries)
- [ ] TestDetailPanel: expandable panel for each test showing methodology and results
- [ ] FilterBar: test type checkboxes + severity dropdown + search

#### JE Testing Memo (Council addition — unanimous agreement)
- [ ] Auto-generated PDF memo documenting the JE testing engagement
  - Header: client name, period tested, date of testing, preparer
  - Scope: total entries tested, date range, GL source description
  - Methodology: list of tests applied with brief description of each
  - Results summary: composite score, risk tier, flag counts by test
  - Findings: top flagged entries with risk explanation
  - Conclusion: overall assessment with professional language
  - SHA-256 hashed filename for Zero-Storage compliance
- [ ] Reuse existing PDF generator pattern (Renaissance Ledger aesthetic)
- [ ] "Download Testing Memo" button alongside existing export options

#### Export
- [ ] PDF export for JE testing results (detailed workpaper format)
  - Cover page with composite score and risk tier
  - Test-by-test breakdown with flag counts
  - Top 20 flagged entries with details
  - Benford's Law distribution chart (as table in PDF)
- [ ] CSV export for flagged entries list
- [ ] Zero-Storage: exports generated in-memory, streamed to user
- [ ] `npm run build` passes

---

### Sprint 68: JE Testing — Tier 2 Tests + Threshold Config UI — PLANNED
> **Complexity:** 6/10 | **Agent Lead:** BackendCritic + FrontendExecutor
> **Focus:** User/time-based anomaly tests, configurable threshold UI
> **Council addition:** Threshold Config UI integrated into Practice Settings page (not a new page)

#### Tier 2 Tests (5 tests)
- [ ] **T9: Single-User High-Volume** — Flag users posting >X% of total entries
- [ ] **T10: After-Hours Postings** — Flag entries posted outside business hours (configurable via JETestingConfig)
- [ ] **T11: Sequential Numbering Gaps** — Flag gaps in entry reference numbers
- [ ] **T12: Backdated Entries** — Flag entries where posting_date significantly differs from entry_date (uses dual-date from Sprint 64)
- [ ] **T13: Suspicious Keywords** — Flag descriptions containing keywords (reuse classification_rules.py weighted keyword pattern)
  - Keywords: "adjust", "reverse", "correct", "override", "manual", "reclass", "write-off"
  - Context weighting: weight by amount and account type

#### Threshold Config UI (Council addition — deferred from Sprint 64 data model)
- [ ] JE Testing section in Practice Settings page (`/settings/practice`)
  - Do NOT create a separate page — integrate into existing Practice Settings
- [ ] Tiered presets (QualityGuardian recommendation — reduces test matrix):
  - Conservative: lower thresholds, more flags, fewer false negatives
  - Standard: balanced defaults (current hardcoded values)
  - Permissive: higher thresholds, fewer flags, fewer false positives
- [ ] Custom overrides: allow individual threshold adjustments per test
- [ ] API: PUT `/settings/je-testing` to save JETestingConfig per user
- [ ] Zero-Storage: config is practice settings (stored), not financial data

#### Integration
- [ ] Add Tier 2 tests to JETestBattery (opt-in based on available columns)
- [ ] Update scoring engine weights for Tier 2 tests
- [ ] Update frontend TestResultGrid to display Tier 2 results
- [ ] 20+ new tests
- [ ] `pytest` passes
- [ ] `npm run build` passes

---

### Sprint 69: JE Testing — Tier 3 + Sampling + Fraud Indicators — PLANNED
> **Complexity:** 7/10 | **Agent Lead:** BackendCritic + QualityGuardian
> **Focus:** Advanced statistical tests, stratified sampling, deeper fraud indicators
> **CEO decision:** Full stratified sampling included (not deferred to Phase VII)

#### Tier 3 Tests (4 tests)
- [ ] **T14: Reciprocal Entries** — Flag matching debit/credit pairs posted close together (potential round-tripping)
- [ ] **T15: Just-Below-Threshold** — Flag entries just below common approval thresholds ($5K, $10K, $25K, $50K)
- [ ] **T16: Account Frequency Anomaly** — Flag accounts receiving entries at unusual frequency vs historical
- [ ] **T17: Description Length Anomaly** — Flag entries with unusually short or blank descriptions vs account norms

#### Stratified Sampling (CEO approved — full implementation)
- [ ] Sampling engine: stratified random sampling from full GL population
  - Stratify by: account category, amount range, posting period, user
  - CSPRNG required: use `secrets` module, NOT `random` (QualityGuardian requirement — PCAOB compliance)
  - Configurable sample size: percentage or fixed count per stratum
- [ ] Sampling parameters UI: 3-step flow
  - Step 1: Select stratification criteria (checkboxes)
  - Step 2: Preview stratum counts and set sample sizes
  - Step 3: Execute sampling and display selected entries
- [ ] Sample results: exportable list of sampled entries for manual review
- [ ] Audit trail: record sampling parameters, seed, and selection for reproducibility

#### Deeper Fraud Indicators (Council addition — expanded scope)
- [ ] Enhance T14 (Reciprocal Entries): detect cross-account round-tripping patterns
- [ ] Enhance T15 (Just-Below-Threshold): detect split transactions that together exceed threshold
- [ ] New: **T18: Unusual Account Combinations** — Flag rarely-seen debit/credit account pairings

#### Polish
- [ ] Add Tier 3 tests + sampling to battery and scoring
- [ ] Update frontend with Tier 3 display + sampling UI
- [ ] Comprehensive test suite for Tier 3 + sampling (20+ tests)
- [ ] End-to-end integration test: upload GL → run all tiers → sample → verify score → verify export
- [ ] `pytest` passes
- [ ] `npm run build` passes

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
| 62 | Route Scaffolding + Multi-Period API/Frontend | 6/10 | FrontendExecutor + BackendCritic | PLANNED |
| 63 | Multi-Period Polish + Three-Way Comparison | 4/10 | BackendCritic + FrontendExecutor | PLANNED |
| 64 | JE Testing — Backend Foundation + Config + Dual-Date | 5/10 | BackendCritic | PLANNED |
| 65 | JE Testing — Statistical Tests + Benford Pre-Checks | 7/10 | BackendCritic + QualityGuardian | PLANNED |
| **66** | **JE Testing — Frontend MVP + Platform Rebrand** | **7/10** | **FrontendExecutor + FintechDesigner** | **PLANNED** |
| 67 | JE Testing — Results Table + Export + Testing Memo | 5/10 | FrontendExecutor + BackendCritic | PLANNED |
| 68 | JE Testing — Tier 2 Tests + Threshold Config UI | 6/10 | BackendCritic + FrontendExecutor | PLANNED |
| 69 | JE Testing — Tier 3 + Sampling + Fraud Indicators | 7/10 | BackendCritic + QualityGuardian | PLANNED |
| 70 | Diagnostic Zone Protection + Wrap | 2/10 | QualityGuardian | PLANNED |

### Deferred Items
- **Contra-Account Validator** — Requires industry-specific accounting rules (all agents: defer indefinitely)
- **Print Styles** — Accounting expert: "Print is legacy" (all agents: not worth the sprint)
- **Batch Upload Processing** — Foundation built (Sprint 38-39), processing pipeline deferred until user demand
- **Multi-Currency Conversion** — Detection added in Sprint 64; full conversion support deferred to Phase VII
- **Full Population Sampling UI** — Stratified sampling of flagged entries in Sprint 69; broader population sampling tools deferred to Phase VII
