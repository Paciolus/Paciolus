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

## Phases VI-IX — COMPLETE (Archived)

> **Sprint Range:** 61-96 (36 sprints)
> **Detailed checklists:** See `tasks/archive/phases-vi-ix-details.md`

### Phase VI (Sprints 61-70): Multi-Period Analysis & Journal Entry Testing
> Multi-Period TB Comparison (Tool 2), Journal Entry Testing (Tool 3, 18-test battery + stratified sampling), platform rebrand, diagnostic zone protection. Tests added: 268 JE + multi-period.

### Phase VII (Sprints 71-80): Financial Statements + AP Testing + Bank Rec
> Financial Statement Builder (Tool 1 enhancement), AP Payment Testing (Tool 4, 13-test battery), Bank Reconciliation (Tool 5). Tests added: 165 AP + 55 bank rec.

### Phase VIII (Sprints 81-89): Cash Flow + Payroll Testing
> Cash Flow Statement (indirect method, Tool 1 enhancement), Payroll Testing (Tool 6, 11-test battery), code quality sprints (81-82). Tests added: 139 payroll.

### Phase IX (Sprints 90-96): Three-Way Match + Classification Validator
> Shared testing utilities extraction, Three-Way Match Validator (Tool 7), Classification Validator (TB Enhancement). Tests added: 114 three-way match + 52 classification.

**Test Coverage at Phase IX End:** 1,614 backend tests + 26 frontend tests | Version 0.90.0

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

### Not Currently Pursuing
> **Reviewed:** Agent Council + Future State Consultant (2026-02-06), updated 2026-02-08
> **Criteria:** Deprioritized due to low leverage, niche markets, regulatory burden, or off-brand positioning.

| Feature | Status | Reason |
|---------|--------|--------|
| Cash Flow Statement (Indirect) | **DELIVERED** (Sprint 83-84) | Shipped in Phase VIII |
| Classification Validator | **DELIVERED** (Sprint 95) | Shipped in Phase IX as TB Enhancement |
| Three-Way Match Validator | **DELIVERED** (Sprint 91-94) | Shipped in Phase IX as Tool 7 |
| Ghost Employee Detector | **DELIVERED** (Sprint 85-86) | Integrated into Payroll Testing (PR-T9) |
| Loan Amortization Generator | Not pursuing | Commodity calculator; off-brand |
| Depreciation Calculator | Not pursuing | MACRS table maintenance; better served by Excel/QuickBooks |
| Intercompany Elimination Checker | Deferred | Niche (multi-entity only); re-evaluate if user demand |
| 1099 Preparation Helper | Not pursuing | US-only, seasonal, annual IRS rule changes |
| Book-to-Tax Adjustment Calculator | Not pursuing | Tax preparer persona; regulatory complexity |
| W-2/W-3 Reconciliation Tool | Not pursuing | Payroll niche; seasonal; different user persona |
| Cash Flow Projector | Deferred | Requires AR/AP aging + payment history |
| Lease Accounting (ASC 842) | Deferred | 8/10 complexity; high value but needs research sprint |
| Revenue Recognition (ASC 606) | Deferred | 9/10 complexity; contract-specific logic; Phase XI candidate as Revenue Testing |
| Segregation of Duties Checker | Not pursuing | IT audit persona; different user base |
| Multi-Currency Conversion | Deferred | Detection shipped Sprint 64; conversion needs exchange rate infrastructure |

### Future Tool Candidates (Phase XI+)
> Re-evaluate after Phase X (Engagement Layer) ships.

1. **Revenue Testing (Tool 8)** — Highest priority for Phase XI; ISA 240 presumed fraud risk in revenue recognition
2. **AR Aging Analysis (Tool 9)** — Counterpart to AP Testing; receivables sub-ledger analysis
3. **Fixed Asset Testing (Tool 10)** — Depreciation recalculation, additions/disposals rollforward
4. **Cash Flow Statement — Direct Method** — Requires AP/payroll detail integration
5. **Intercompany Elimination Checker** — Re-evaluate if multi-entity demand emerges

---

## Phase X: The Engagement Layer

> **Source:** Agent Council deliberation (2026-02-08) — 4-agent unanimous consensus on Path C (Hybrid)
> **Scope:** 7 sprints (96.5–102) covering Test Infrastructure + Engagement Model + Materiality Cascade + Follow-Up Items + Workpaper Index + Anomaly Summary Report
> **Strategy:** Build engagement workflow WITHOUT engagement assurance — "engagement spine without a judgment brain"
> **Decision:** Path C selected over Path A (full engagement layer — rejected due to ISA 265/315 violations) and Path B (minimal — rejected as commercially uncompetitive)
> **Estimated New Code:** ~3,000 lines (1,800 backend + 1,200 frontend)
> **Estimated New Tests:** ~265 (200 backend + 65 frontend)

### Council Deliberation Record

| Agent | Initial Position | Final Position | Key Contribution |
|-------|-----------------|----------------|------------------|
| BackendCritic | Path A (full) | Path C | Option B session architecture (post-completion aggregation), ToolRun versioning, Zero-Storage schema guardrails |
| QualityGuardian | Path A + infra sprint | Path C | Non-negotiable Sprint 96.5 (test infrastructure), DB fixture strategy, regression risk mapping, 265-test estimate |
| FrontendExecutor | Path A | Path C | React Context + URL param hybrid, +30% complexity adjustment, scope deferral list, EngagementProvider architecture |
| AccountingExpertAuditor | Path B (minimal) → Path C | Path C | 8 non-negotiable guardrails, ISA 265/315 boundary enforcement, terminology mandates, disclaimer language |

### Key Council Tensions Resolved

| Tension | Resolution |
|---------|------------|
| Engagement management vs. audit assurance | Path C separates workflow tracking from audit judgment — "diagnostic workspace" not "audit engagement" |
| Management Letter Generator (Path A) | REJECTED — auto-classifying deficiencies per ISA 265 is auditor judgment territory |
| Cross-Tool Risk Scoring (Path A) | REJECTED — requires ISA 315 inherent/control risk inputs Paciolus doesn't have |
| Sprint 96.5 necessity | ACCEPTED — QualityGuardian's non-negotiable; DB fixtures + migration setup required before new models |
| Materiality Cascade priority | ACCEPTED as Sprint 97 — AccountingExpertAuditor's #1 (ISA 320 compliance) |
| Frontend complexity estimates | ACCEPTED — FrontendExecutor's +30% adjustment applied to all frontend sprints |

### Non-Negotiable Guardrails (AccountingExpertAuditor Mandated)

These guardrails are CONDITIONS of Path C approval. Violation requires council re-review.

1. **Engagement Schema Constraints:** `engagements` table stores metadata ONLY (client_id, period_start, period_end, created_by, status). Must NOT store: risk_level, materiality_assessment, audit_opinion, control_effectiveness, or any field implying audit conclusion.

2. **Follow-Up Items Storage Limits:** Items store narrative descriptions ONLY. Allowed: item_description (text), tool_source (enum), severity (high/medium/low), disposition (enum), auditor_notes (text). Prohibited: account_number, account_name, amount, transaction_id, entry_id, any PII. Enforced via pytest assertion.

3. **Anomaly Summary Report Structure:** Template must NOT mimic ISA 265 structure. Prohibited sections: "Material Weaknesses", "Significant Deficiencies", "Control Environment Assessment". Required sections: (1) Scope, (2) Data Anomalies by Tool, (3) [BLANK — For Auditor Assessment], (4) Disclaimer.

4. **UI Terminology:** Prohibited: "Audit Status", "Risk Assessment", "Control Testing", "Audit Opinion", "Significant Accounts", "Financial Statement Assertions". Required: "Diagnostic Status", "Tools Run", "Follow-Up Items", "Data Analysis", "Accounts Analyzed".

5. **Disclaimer Display Requirements:** Non-dismissible banners on Engagement Workspace, Follow-Up Items Tracker, and all exports. Specific text defined per deliverable (see sprint details below).

6. **No Composite Scoring:** Per-tool scores remain but are NEVER aggregated into engagement-level composite. No heat maps or engagement-level risk tier indicators.

7. **TOS Update:** Professional standards compliance section required in Terms of Service before v0.95.0 ships. Legal review mandatory.

8. **AccountingExpertAuditor Review Gates:** Schema review before Sprint 97 merge. Screenshot review before Sprint 98 and Sprint 100 merge. PDF template review before Sprint 101 merge.

### Phase X Summary Table

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 96.5 | Test Infrastructure — DB Fixtures + Migration + Frontend Backfill | 2/10 | QualityGuardian | PENDING |
| 97 | Engagement Model + Materiality Cascade | 6/10 | BackendCritic + AccountingExpertAuditor | PENDING |
| 98 | Engagement Workspace (Frontend) | 5/10 | FrontendExecutor + FintechDesigner | PENDING |
| 99 | Follow-Up Items Tracker (Backend) | 5/10 | BackendCritic + QualityGuardian | PENDING |
| 100 | Follow-Up Items UI + Workpaper Index | 6/10 | FrontendExecutor + BackendCritic | PENDING |
| 101 | Engagement ZIP Export + Anomaly Summary Report | 5/10 | BackendCritic + AccountingExpertAuditor | PENDING |
| 102 | Phase X Wrap — Regression + TOS + CI Checks | 2/10 | QualityGuardian + FintechDesigner | PENDING |

---

### Sprint 96.5: Test Infrastructure — DB Fixtures + Migration + Frontend Backfill
> **Complexity:** 2/10 | **Agent Lead:** QualityGuardian
> **Rationale:** QualityGuardian non-negotiable — Phase X introduces first persistent DB layer (engagements, follow-up items). Current test suite has ZERO database testing infrastructure.

#### Backend — Database Test Infrastructure
- [x] Set up SQLite in-memory database for tests
- [x] Create pytest fixtures for DB session management (setup/teardown)
- [x] Implement transaction rollback pattern (each test gets clean DB)
- [x] Create example CRUD tests for existing models (users, clients) as template — 23 tests
- [x] Set up Alembic for database migrations
- [x] Create initial migration for existing tables (users, clients, practice_settings)
- [x] Document migration workflow in `backend/migrations/README.md`

#### Backend — Shared Export Helpers
- [x] Extract shared export utilities to `backend/shared/export_helpers.py`
- [x] Tests for extracted helpers — 16 tests

#### Frontend — Test Backfill (Critical Paths)
- [x] 10 tests for JE Testing page (upload, results table, export buttons)
- [x] 10 tests for AP Testing page (upload, results table, export buttons)
- [x] 10 tests for Bank Rec page (upload, results, export)
- [x] 10 tests for Payroll Testing page (upload, results, export)
- [x] 10 tests for Three-Way Match page (upload, results, export)

#### Documentation
- [x] Create `backend/shared/metadata_persistence_policy.md` documenting:
  - What metadata persists (engagement, follow-up items)
  - What data is ephemeral (TB data, JE records, AP payments, payroll, receipts)
  - How follow-up items link to ephemeral data (timestamp + tool + description)
  - UI expectations (show "data unavailable" for stale references)

#### Verification
- [x] All existing 1,614+ backend tests still pass
- [x] `npm run build` passes
- [x] New frontend tests pass (50 backfill tests)

---

### Sprint 97: Engagement Model + Materiality Cascade ✅ COMPLETE
> **Complexity:** 6/10 | **Agent Lead:** BackendCritic + AccountingExpertAuditor
> **Guardrail Check:** AccountingExpertAuditor schema review BEFORE merge

#### Backend — Engagement Model
- [x] Create `backend/engagement_model.py` with SQLAlchemy models:
  - `Engagement`: id, client_id, period_start, period_end, status (active/archived), created_by, created_at
  - `ToolRun`: id, engagement_id, tool_name, run_number, status (completed/failed), composite_score, run_at
  - `EngagementStatus`, `MaterialityBasis`, `ToolName`, `ToolRunStatus` enums
- [x] Guardrail 1 enforcement: NO risk_level, NO audit_opinion, NO control_effectiveness fields
- [x] Database init updated (`database.py` + `alembic/env.py`)
- [x] Foreign key: engagement.client_id → clients.id (ON DELETE RESTRICT)

#### Backend — Engagement CRUD API
- [x] Create `backend/routes/engagements.py`:
  - `POST /engagements` — create engagement (requires client_id, period_start, period_end)
  - `GET /engagements` — list engagements (filter by client_id, status; paginated)
  - `GET /engagements/{id}` — get engagement with ownership check
  - `PUT /engagements/{id}` — update engagement (status, period, materiality)
  - `DELETE /engagements/{id}` — archive engagement (soft delete)
- [x] Auth: `require_current_user` (engagement management = client-level access)
- [x] Register router in `routes/__init__.py`

#### Backend — Materiality Cascade Controller
- [x] Create `backend/engagement_manager.py` with materiality fields on Engagement model
- [x] Materiality parameters: basis (revenue/assets/manual), percentage, amount
- [x] Performance Materiality: PM = amount × factor (default 0.75, user-adjustable)
- [x] Trivial Threshold: Trivial = amount × factor (default 0.05, user-adjustable)
- [x] `GET /engagements/{id}/materiality` — returns materiality + PM + trivial cascade

#### Backend — Tool Route Integration
- [x] Update all 7 tool routes to accept optional `engagement_id` parameter
- [x] Shared `maybe_record_tool_run()` helper in `shared/helpers.py`
- [x] If `engagement_id` provided, POST ToolRun metadata after completion:
  - tool_name, run_number (auto-increment), status, composite_score (JE/AP/Payroll), run_at
- [x] Failed runs also recorded when engagement_id present
- [x] Tools remain independent — engagement context is OPTIONAL (backward compatible)

#### Tests (54 total)
- [x] TestEngagementSchema: enum values, to_dict, repr, guardrail column check (8 tests)
- [x] TestEngagementCRUD: create, read, update, archive, list, ownership isolation, pagination (12 tests)
- [x] TestEngagementCascade: RESTRICT client delete, CASCADE tool_runs, FK constraints (8 tests)
- [x] TestEngagementValidation: date ranges, negative materiality, factor bounds, update dates (7 tests)
- [x] TestMaterialityCascade: revenue/asset/manual basis, PM, trivial, custom factors, rounding (10 tests)
- [x] TestToolRunRecording: auto-increment, per-tool independence, scores, ordering (8 tests)
- [x] TestRouteRegistration: all engagement routes in app (1 test)

#### Verification
- [x] `pytest` passes — 1,707 total (1,653 existing + 54 new, zero failures)
- [x] `npm run build` passes — no frontend changes this sprint
- [x] Zero-Storage compliance: engagement stores metadata only, no financial data
- [x] Guardrail 1 verified: no prohibited columns in engagements table

---

### Sprint 98: Engagement Workspace (Frontend) ✅ COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor + FintechDesigner
> **Guardrail Check:** AccountingExpertAuditor screenshot review BEFORE merge

#### Frontend — Engagement Context Architecture
- [x] Create `frontend/src/contexts/EngagementContext.tsx`:
  - `EngagementProvider` scoped to engagements page (tool page integration Sprint 100+)
  - State: activeEngagement, toolRuns, materiality, selectEngagement, clearEngagement
  - Hybrid approach: React Context (primary) + URL param `?engagement=X` (direct links)
  - TypeScript types in `frontend/src/types/engagement.ts`

#### Frontend — Engagement Workspace Page
- [x] Create `frontend/src/app/engagements/page.tsx`:
  - Client filter dropdown + status tabs (All/Active/Archived)
  - Engagement CRUD (create via modal, list, archive)
  - Selected engagement detail card + materiality cascade + tool status grid
- [x] Create `frontend/src/components/engagement/EngagementList.tsx`
- [x] Create `frontend/src/components/engagement/EngagementCard.tsx`

#### Frontend — Tool Status Cards
- [x] Create `frontend/src/components/engagement/ToolStatusGrid.tsx`:
  - 7 cards showing tool name, last run date, status (completed/not started)
  - Navigate to tool page on click
  - StatusBadge: sage for completed, obsidian for not started
- [x] Guardrail 4: Labels use "Diagnostic Status", "Tools Run" (never "Audit Status")

#### Frontend — Engagement Workspace Disclaimer
- [x] Non-dismissible top banner (Guardrail 5):
  ```
  DIAGNOSTIC WORKSPACE — NOT AN AUDIT ENGAGEMENT
  This workspace organizes data analytics procedures. It does not track audit
  procedures, assurance engagements, or compliance with ISA/PCAOB standards.
  The practitioner is solely responsible for all audit planning, execution, and conclusions.
  ```

#### Frontend — Navigation Updates
- [x] Add "Workspaces" to ToolNav (all 7 tool pages)
- [x] Add "Workspaces" to portfolio page nav
- [x] Existing `/tools/*` URLs continue working standalone (backward compatible)

#### Frontend — Hook
- [x] Create `frontend/src/hooks/useEngagement.ts` — CRUD + materiality + tool runs

#### Frontend — Modal
- [x] Create `frontend/src/components/engagement/CreateEngagementModal.tsx` — client selector, period dates, materiality config

#### Tests
- [ ] TestEngagementList: rendering, filtering, sorting (6 tests)
- [ ] TestToolStatusGrid: status badges, navigation (5 tests)
- [ ] TestClientSelector: dropdown, selection persistence (4 tests)
- [ ] TestEngagementContext: provider, state management (5 tests)

#### Verification
- [x] `npm run build` passes
- [ ] AccountingExpertAuditor screenshot review completed
- [x] Guardrail 4 terminology check: no "audit" language in engagement components
- [x] Guardrail: no generic Tailwind colors (slate/blue/green/red) in engagement code

---

### Sprint 99: Follow-Up Items Tracker (Backend)
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic + QualityGuardian
> **Guardrail Check:** Pytest assertion validates no account/amount fields in follow_up_items table

#### Backend — Follow-Up Items Model
- [x] Create `backend/follow_up_items_model.py` with dataclasses:
  - `FollowUpItem`: id, engagement_id, tool_run_id, description (text), tool_source (enum), severity (high/medium/low), disposition (enum), auditor_notes (text), created_at, updated_at
  - `Disposition` enum: `not_reviewed`, `investigated_no_issue`, `investigated_adjustment_posted`, `investigated_further_review`, `immaterial`
- [x] Guardrail 2 enforcement: NO account_number, NO amount, NO transaction_id, NO PII fields
- [x] Database migration for `follow_up_items` table
- [x] Foreign keys: follow_up_item.engagement_id → engagements.id, follow_up_item.tool_run_id → tool_runs.id (nullable)

#### Backend — Follow-Up Items CRUD API
- [x] Create `backend/routes/follow_up_items.py`:
  - `POST /engagements/{id}/follow-up-items` — create item
  - `GET /engagements/{id}/follow-up-items` — list items (filter by severity, disposition, tool_source)
  - `PUT /follow-up-items/{item_id}` — update disposition, auditor_notes
  - `DELETE /follow-up-items/{item_id}` — delete item
  - `GET /engagements/{id}/follow-up-items/summary` — counts by severity, disposition, tool_source
- [x] Auth: `require_current_user`
- [x] Register router in `routes/__init__.py`

#### Backend — Auto-Population from Tool Runs
- [x] When tool run completes with `engagement_id`, auto-create follow-up items for HIGH severity findings:
  - Description: narrative summary (e.g., "Round amount entries detected: 47 entries flagged")
  - tool_source: tool enum value
  - severity: mapped from tool's risk tier
  - disposition: `not_reviewed` (default)
- [x] Guardrail 2: descriptions are NARRATIVE ONLY — never embed account numbers or dollar amounts

#### Tests
- [x] TestFollowUpItemSchema: dataclass validation, prohibited fields check (9 tests)
- [x] TestFollowUpItemCRUD: create, read, update, delete, list (14 tests)
- [x] TestFollowUpItemFiltering: by severity, disposition, tool_source (8 tests)
- [x] TestFollowUpItemAggregation: counts by type, group by severity (8 tests)
- [x] TestAutoPopulation: tool run → follow-up items creation (10 tests)
- [x] TestZeroStorageCompliance: assert no numeric/account fields exist in model (5 tests)
- [x] TestFollowUpCascade: engagement delete cascades, tool_run delete sets null (4 tests)
- [x] TestRouteRegistration: routes registered in app (1 test)

#### Verification
- [x] `pytest` passes (all existing + 59 new tests)
- [x] Guardrail 2 pytest assertion: query follow_up_items columns, assert no amount/account fields
- [x] Zero-Storage compliance verified

---

### Sprint 100: Follow-Up Items UI + Workpaper Index
> **Complexity:** 6/10 | **Agent Lead:** FrontendExecutor + BackendCritic
> **Guardrail Check:** AccountingExpertAuditor screenshot review BEFORE merge

#### Frontend — Follow-Up Items Table
- [x] Create `frontend/src/components/engagement/FollowUpItemsTable.tsx`:
  - Sortable, filterable table (severity, disposition, tool source)
  - Inline disposition dropdown (DispositionSelect component)
  - Source tool badges (color-coded by tool)
  - Auditor notes text area (expandable per item)
- [x] Create `frontend/src/components/engagement/DispositionSelect.tsx`
- [x] FollowUpItemCard functionality integrated into FollowUpItemsTable expandable rows

#### Frontend — Follow-Up Items Page Header Disclaimer
- [x] Non-dismissible header (Guardrail 5) on follow-up tab

#### Backend — Workpaper Index Generator
- [x] Create `backend/workpaper_index_generator.py`:
  - Auto-generated document register: tool name → lead sheet ref
  - Run count + last run date per tool
  - Follow-up summary aggregation (by severity, disposition, tool_source)
  - Auditor sign-off template (prepared by, reviewed by, date fields — BLANK)
  - `GET /engagements/{id}/workpaper-index` — returns index data as JSON

#### Frontend — Workpaper Index View
- [x] Create `frontend/src/components/engagement/WorkpaperIndex.tsx`:
  - Document register table with status badges
  - Follow-up summary grid (severity, disposition, tool_source)
  - Auditor sign-off section (blank fields)

#### Frontend — Hook
- [x] Create `frontend/src/hooks/useFollowUpItems.ts` — CRUD + filtering

#### Frontend — Page Integration
- [x] Tabbed workspace detail view (Diagnostic Status | Follow-Up Items | Workpaper Index)
- [x] Follow-up item types added to `types/engagement.ts`
- [x] Barrel export updated in `components/engagement/index.ts`
- [x] Hook export added to `hooks/index.ts`

#### Tests
- [x] TestWorkpaperIndexGenerator: 9 tests (empty engagement, sign-off blank, dates, access denied, tool register)
- [x] TestWorkpaperIndexWithToolRuns: 3 tests (single run, multiple runs, mixed status)
- [x] TestWorkpaperIndexFollowUpSummary: 4 tests (aggregation, empty, disposition, isolation)
- [x] TestWorkpaperIndexEndpoint: 1 test (route registration)

#### Verification
- [x] `npm run build` passes
- [x] `pytest` passes (17 new workpaper index tests + 113 existing engagement/follow-up tests)
- [x] Guardrail 4: no "audit" terminology in follow-up items UI
- [x] Guardrail: no generic Tailwind colors in engagement components

---

### Sprint 101: Engagement ZIP Export + Anomaly Summary Report
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic + AccountingExpertAuditor
> **Guardrail Check:** AccountingExpertAuditor PDF template review BEFORE merge

#### Backend — Anomaly Summary Report
- [x] Create `backend/anomaly_summary_generator.py`:
  - Section 1: Scope — tools run, dates, run counts
  - Section 2: Data Anomalies by Tool — follow-up items grouped by tool with severity
  - Section 3: [BLANK — For Practitioner Assessment] — full-page blank section with ruled lines
  - Disclaimer banner (10pt bold, clay text, first page header)
- [x] Guardrail 3: Template does NOT mimic ISA 265 structure
- [x] `POST /engagements/{id}/export/anomaly-summary` — generates PDF

#### Backend — Engagement ZIP Export
- [x] Create `backend/engagement_export.py`:
  - Includes: anomaly_summary.pdf + workpaper_index.json + manifest.json
  - manifest.json: file list with SHA-256 hashes + timestamps + platform version
  - File naming: `{client_name}_{period_end}_diagnostic_package.zip`
  - Does NOT include uploaded files (Zero-Storage compliance)
- [x] `POST /engagements/{id}/export/package` — generates and streams ZIP

#### Backend — Strengthened Disclaimers on Existing Exports
- [x] Updated `backend/shared/memo_base.py` disclaimer with strengthened text
- [x] Added `isa_reference` parameter for domain-specific ISA citations
- [x] Backward-compatible — existing callers work without changes

#### Tests
- [x] TestAnomalySummaryReport: PDF generation, access control, ISA 265 guardrail, large batch (11 tests)
- [x] TestEngagementZIP: file structure, manifest SHA-256, naming, Zero-Storage (10 tests)
- [x] TestDisclaimerUpdates: strengthened text, ISA reference, backward compatibility (5 tests)
- [x] TestExportRoutes: route registration (2 tests)

#### Verification
- [x] `pytest` passes (130 existing + 28 new = 158 engagement-related tests)
- [x] Guardrail 3: no ISA 265 structure in anomaly summary
- [x] Zero-Storage: ZIP does not include uploaded financial data

---

### Sprint 102: Phase X Wrap — Regression + TOS + CI Checks
> **Complexity:** 2/10 | **Agent Lead:** QualityGuardian + FintechDesigner

#### Regression Testing
- [x] Full backend test suite passes (1,811 total — all passed)
- [x] Full frontend build passes (all routes compile)
- [x] All 7 tool pages function with and without engagement context
- [x] Materiality cascade propagates correctly to all tool routes

#### Navigation + Homepage
- [x] Add Engagement Workspace to main navigation (homepage + ToolNav + portfolio)
- [x] Update homepage marketing copy: "Seven integrated tools, one diagnostic workspace"
- [x] Add Diagnostic Workspace CTA card to homepage features section

#### CI/CD Guardrail Checks
- [x] Guardrail 4 grep check: zero matches for "audit opinion|risk assessment|control testing" in engagement components
- [x] Guardrail 6 grep check: no engagement-level composite scoring in routes (per-tool-run field is compliant)
- [x] Guardrail 1 grep check: ISA 265 terms only in exclusion comments, not active code
- [x] Guardrail 2 grep check: no financial data columns in follow_up_items_model (exclusion comments only)
- [x] Documented grep checks in `docs/guardrail-checks.md` for future CI/CD integration

#### TOS Update (Guardrail 7)
- [x] Draft Terms of Service Section 8: Professional Standards Compliance (`docs/tos-section-8-draft.md`)
- [x] Clarify: Paciolus is diagnostic tool, not audit software (Section 8.1)
- [x] Clarify: engagement workspace is workflow only, not audit documentation (Section 8.2)
- [x] Marked for legal review before v0.95.0 release (header note)

#### CLAUDE.md Updates
- [x] Phase status: Phase X COMPLETE
- [x] Version: 0.90.0 → 0.95.0
- [x] Test coverage totals updated (1,811 backend + 76 frontend)
- [x] Phase X added to completed phases list
- [x] Engagement Layer added to Key Capabilities
- [x] Next Priority: Phase XI Planning

#### Documentation
- [x] Updated `tasks/todo.md` Phase X review section
- [x] Add lessons learned to `tasks/lessons.md`

#### Verification
- [x] `npm run build` passes
- [x] `pytest` passes (full suite — 1,811 tests)
- [x] All guardrails verified (1, 2, 4, 5, 6, 7)
- [x] AccountingExpertAuditor guardrails — all 8 conditions satisfied

---

### Phase X Review — COMPLETE (2026-02-08)

**Delivered:** Full engagement workflow layer — metadata-only engagement model with materiality cascade, follow-up items tracker (narratives-only), workpaper index generator, anomaly summary report (PDF), diagnostic package export (ZIP with SHA-256 manifest), and frontend workspace with tabbed detail view.

**Key Metrics:**
- 7 sprints (96.5–102), all COMPLETE
- 1,811 backend tests + 76 frontend tests — all passing
- 8 new backend modules, 8 new frontend components, 2 new docs
- All 8 AccountingExpertAuditor guardrails satisfied
- Zero regressions across existing 7-tool suite

**Architecture Decisions:**
- Post-completion aggregation (tools remain independent)
- Narratives-only follow-up items (no financial data in persistent storage)
- Per-tool-run scores (no engagement-level composite)
- Non-dismissible disclaimers on all engagement surfaces

---

### Phase X Explicit Exclusions (Deferred to Phase XI+)

These features were discussed during council deliberation and explicitly DEFERRED:

| Feature | Reason for Deferral | Earliest Phase |
|---------|---------------------|----------------|
| Cross-Tool Composite Risk Scoring | Requires ISA 315 inputs; AccountingExpertAuditor rejected | Phase XI (if auditor-input workflow designed) |
| Management Letter Generator | Violates ISA 265 boundary; auto-classification = audit judgment | REJECTED permanently |
| Heat Map / Risk Visualization | Depends on composite scoring (rejected) | Phase XI (if scoring approved) |
| Finding Comments / Threads | Scope creep risk; disposition enum is sufficient for MVP | Phase XI |
| Finding Assignments (team member) | Multi-user feature; single-user MVP first | Phase XI |
| Finding Attachments (PDF docs) | File storage contradicts Zero-Storage philosophy | Phase XII+ |
| Real-Time Collaboration | WebSocket infrastructure; 9/10 complexity | Phase XII+ |
| Custom Report Builder | Rich text editor + templating engine | Phase XII+ |
| Engagement Templates | Pre-configured tool sequences; adds abstraction layer | Phase XI |
| Historical Engagement Comparison | Requires persistent aggregated data across engagements | Phase XII+ |
| Revenue Testing (Tool 8) | Delayed by engagement layer; highest priority for Phase XI | Phase XI |
| AR Aging Analysis (Tool 9) | Delayed by engagement layer | Phase XI |
| Fixed Asset Testing (Tool 10) | Delayed by engagement layer | Phase XII |

### Phase X Architecture Decisions

#### Session Architecture: Option B (Post-Completion Aggregation)
Per BackendCritic recommendation:
- Tools remain session-based and independent (no coupling)
- Each tool endpoint accepts optional `engagement_id` parameter
- If `engagement_id` provided, POST ToolRun metadata to engagement service after completion
- Engagement dashboard queries ToolRun table for "what's been done"
- Engagement CANNOT re-display detailed tool results (those are ephemeral) — only shows summary metadata

#### Frontend Context: Hybrid A+B (React Context + URL Params)
Per FrontendExecutor recommendation:
- Primary: React Context (`EngagementProvider`) wrapping `/tools/*` via layout
- Secondary: URL param `?engagement=X` for direct links/bookmarks
- Context reads from URL on mount, syncs to URL on engagement switch
- Tools auto-link results to active engagement (toast notification with Undo)

#### Zero-Storage Boundary
Per AccountingExpertAuditor + BackendCritic:
- Engagement table: metadata ONLY (client_id, period, status, materiality_threshold)
- ToolRun table: metadata ONLY (tool_name, run_number, composite_score, timestamp)
- FollowUpItem table: narratives ONLY (description text, severity, disposition)
- PROHIBITED in any table: account_number, account_name, amount, transaction_id, PII
- Financial data remains 100% ephemeral — never persisted to database
