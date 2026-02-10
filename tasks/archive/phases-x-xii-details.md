# Archived Sprint Details: Phases X-XII

> **Archived:** 2026-02-09 — Moved from todo.md to reduce context bloat.
> **These are completed sprint checklists. For current work, see todo.md.**

---

## Phase X: The Engagement Layer (Sprints 96.5–102)

> **Source:** Agent Council deliberation (2026-02-08) — 4-agent unanimous consensus on Path C (Hybrid)
> **Scope:** 7 sprints covering Test Infrastructure + Engagement Model + Materiality Cascade + Follow-Up Items + Workpaper Index + Anomaly Summary Report
> **Strategy:** Build engagement workflow WITHOUT engagement assurance — "engagement spine without a judgment brain"
> **Decision:** Path C selected over Path A (full — rejected due to ISA 265/315 violations) and Path B (minimal — rejected as commercially uncompetitive)

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

5. **Disclaimer Display Requirements:** Non-dismissible banners on Engagement Workspace, Follow-Up Items Tracker, and all exports. Specific text defined per deliverable.

6. **No Composite Scoring:** Per-tool scores remain but are NEVER aggregated into engagement-level composite. No heat maps or engagement-level risk tier indicators.

7. **TOS Update:** Professional standards compliance section required in Terms of Service before v0.95.0 ships. Legal review mandatory.

8. **AccountingExpertAuditor Review Gates:** Schema review before Sprint 97 merge. Screenshot review before Sprint 98 and Sprint 100 merge. PDF template review before Sprint 101 merge.

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

---

### Sprint 96.5: Test Infrastructure — DB Fixtures + Migration + Frontend Backfill
> **Complexity:** 2/10 | **Agent Lead:** QualityGuardian

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
- [x] Create `backend/shared/metadata_persistence_policy.md`

#### Verification
- [x] All existing 1,614+ backend tests still pass
- [x] `npm run build` passes
- [x] New frontend tests pass (50 backfill tests)

---

### Sprint 97: Engagement Model + Materiality Cascade
> **Complexity:** 6/10 | **Agent Lead:** BackendCritic + AccountingExpertAuditor

- [x] Create `backend/engagement_model.py` (Engagement, ToolRun, enums)
- [x] Guardrail 1 enforcement: NO risk_level, NO audit_opinion fields
- [x] Create `backend/routes/engagements.py` (CRUD + materiality)
- [x] Materiality cascade: basis, percentage, amount, PM factor, trivial threshold
- [x] Update all 7 tool routes to accept optional `engagement_id`
- [x] Shared `maybe_record_tool_run()` helper
- [x] 54 tests — `pytest` passes (1,707 total)

---

### Sprint 98: Engagement Workspace (Frontend)
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor + FintechDesigner

- [x] Create `contexts/EngagementContext.tsx` (provider, URL param sync)
- [x] Create `app/engagements/page.tsx` (client filter, status tabs, CRUD)
- [x] Create engagement components (EngagementList, EngagementCard, ToolStatusGrid, CreateEngagementModal)
- [x] Non-dismissible disclaimer banner (Guardrail 5)
- [x] Add "Workspaces" to ToolNav + portfolio nav
- [x] `npm run build` passes

---

### Sprint 99: Follow-Up Items Tracker (Backend)
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic + QualityGuardian

- [x] Create `backend/follow_up_items_model.py` (FollowUpItem, Disposition enum)
- [x] Guardrail 2: NO account_number, NO amount fields
- [x] Create `backend/routes/follow_up_items.py` (CRUD + filtering + summary + auto-population)
- [x] Auto-populate HIGH severity findings from tool runs
- [x] 59 tests (schema, CRUD, filtering, aggregation, auto-population, cascade, Zero-Storage)

---

### Sprint 100: Follow-Up Items UI + Workpaper Index
> **Complexity:** 6/10 | **Agent Lead:** FrontendExecutor + BackendCritic

- [x] Create `FollowUpItemsTable.tsx` (sortable, filterable, inline disposition)
- [x] Create `WorkpaperIndex.tsx` (document register, follow-up summary, sign-off)
- [x] Create `backend/workpaper_index_generator.py` (auto-generated index, 17 tests)
- [x] Tabbed workspace detail view (Diagnostic Status | Follow-Up Items | Workpaper Index)
- [x] `npm run build` + `pytest` pass

---

### Sprint 101: Engagement ZIP Export + Anomaly Summary Report
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic + AccountingExpertAuditor

- [x] Create `backend/anomaly_summary_generator.py` (scope + anomalies + blank auditor section)
- [x] Guardrail 3: Template does NOT mimic ISA 265
- [x] Create `backend/engagement_export.py` (ZIP with PDF + JSON + manifest with SHA-256)
- [x] Strengthened disclaimers in `shared/memo_base.py`
- [x] 28 tests (anomaly summary, ZIP structure, disclaimers, routes)

---

### Sprint 102: Phase X Wrap — Regression + TOS + CI Checks
> **Complexity:** 2/10 | **Agent Lead:** QualityGuardian + FintechDesigner

- [x] Full regression: 1,811 backend tests, all frontend routes
- [x] Navigation + homepage updates for workspace marketing
- [x] CI/CD guardrail grep checks (6 guardrails documented in `docs/guardrail-checks.md`)
- [x] TOS Section 8 draft (`docs/tos-section-8-draft.md`)
- [x] CLAUDE.md: Phase X COMPLETE, version 0.95.0

### Phase X Review — COMPLETE (2026-02-08)
**Delivered:** Full engagement workflow layer — 8 new backend modules, 8 new frontend components, 158 engagement-related tests, all 8 guardrails satisfied.

---

### Phase X Explicit Exclusions (Deferred)

| Feature | Reason | Earliest Phase |
|---------|--------|----------------|
| Cross-Tool Composite Risk Scoring | ISA 315 violation | REJECTED |
| Management Letter Generator | ISA 265 violation | REJECTED |
| Heat Map / Risk Visualization | Depends on composite scoring | REJECTED |
| Finding Comments / Threads | Scope creep; disposition sufficient for MVP | Phase XI |
| Finding Assignments (team member) | Multi-user; single-user MVP first | Phase XI |
| Finding Attachments (PDF docs) | Contradicts Zero-Storage | Phase XII+ |
| Real-Time Collaboration | WebSocket; 9/10 complexity | Phase XII+ |
| Custom Report Builder | Rich text + templating | Phase XII+ |
| Engagement Templates | Premature; needs user feedback | Phase XI |
| Historical Engagement Comparison | Needs persistent aggregated data | Phase XII+ |

---

## Phase XI: Tool-Engagement Integration + Revenue Testing + AR Aging (Sprints 103–110)

> **Source:** Agent Council Path B deliberation — 2026-02-08
> **Strategy:** Integration first (make workspace functional), then new tools that auto-link from day one
> **Target Version:** 1.0.0

---

### Sprint 103: Tool-Engagement Integration (Frontend)
> **Complexity:** 3/10 | **Agent Lead:** FrontendExecutor

- [x] Create `app/tools/layout.tsx` wrapping all tool pages in EngagementProvider
- [x] EngagementProvider reads `?engagement=X` URL param on mount
- [x] useAuditUpload auto-injects engagement_id (5 tools), explicit injection for TB + Multi-Period
- [x] Create EngagementBanner.tsx + ToolLinkToast.tsx
- [x] Auto-refresh ToolRun list in workspace after linked tool run
- [x] `npm run build` passes, `pytest` passes (1,811 tests)

---

### Sprint 104: Revenue Testing — Engine + Routes
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic

- [x] Create `backend/revenue_testing_engine.py` (~1,660 lines, 12 tests)
- [x] 12-test battery: 5 structural (RT-01 to RT-05) + 4 statistical (RT-06 to RT-09) + 3 advanced (RT-10 to RT-12)
- [x] Create `backend/routes/revenue_testing.py` (POST /audit/revenue-testing)
- [x] Add REVENUE_TESTING to ToolName enum
- [x] 110 tests — full regression: 1,921 passed

---

### Sprint 105: Revenue Testing — Memo + Export
> **Complexity:** 3/10 | **Agent Lead:** BackendCritic + AccountingExpertAuditor

- [x] Create `backend/revenue_testing_memo_generator.py` (ISA 240/PCAOB AS 2401)
- [x] PDF + CSV export routes
- [x] 28 tests — full regression: 1,949 passed

---

### Sprint 106: Revenue Testing — Frontend + 8-Tool Nav
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor + FintechDesigner

- [x] Create types, hook, 4 components, page for Revenue Testing
- [x] Update ToolNav (8-tool), homepage, engagement types
- [x] `npm run build` passes

---

### Sprint 107: AR Aging — Engine + Routes
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic

- [x] Create `backend/ar_aging_engine.py` (~1,100 lines, 11 tests, dual-input TB + sub-ledger)
- [x] 11-test battery: 4 structural (AR-01 to AR-04) + 5 statistical (AR-05 to AR-09) + 2 advanced (AR-10 to AR-11)
- [x] Create `backend/routes/ar_aging.py` (POST /audit/ar-aging, dual file upload)
- [x] 131 tests — full regression: 2,080 passed

---

### Sprint 108: AR Aging — Memo + Export
> **Complexity:** 3/10 | **Agent Lead:** BackendCritic + AccountingExpertAuditor

- [x] Create `backend/ar_aging_memo_generator.py` (ISA 500/540, PCAOB AS 2501)
- [x] PDF + CSV export routes
- [x] 34 tests — full regression: 2,114 passed

---

### Sprint 109: AR Aging — Frontend + 9-Tool Nav
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor + FintechDesigner

- [x] Create types, hook, 4 components, page for AR Aging (dual dropzone: TB + sub-ledger)
- [x] Update ToolNav (9-tool), homepage, engagement types
- [x] `npm run build` passes

---

### Sprint 110: Phase XI Wrap — Regression + v1.0.0
> **Complexity:** 2/10 | **Agent Lead:** QualityGuardian

- [x] Full regression: 2,114 backend tests, 27 frontend routes
- [x] All 9 tool pages function with and without engagement context
- [x] CLAUDE.md: Phase XI COMPLETE, version 1.0.0
- [x] All 6 guardrails verified

---

## Phase XII: Nav Infrastructure + Collaboration + Fixed Assets + Inventory (Sprints 111–120)

> **Source:** Agent Council Path C (Hybrid) — 2026-02-09
> **Strategy:** Prerequisites first, collaboration quick wins, then two new tools (11-tool suite)
> **Target Version:** 1.1.0

---

### Sprint 111: Prerequisites — Nav Overflow + ToolStatusGrid + FileDropZone Extraction
> **Complexity:** 3/10 | **Agent Lead:** FintechDesigner + FrontendExecutor

- [x] Redesign ToolNav with overflow dropdown ("More" for tools 7+ with INLINE_COUNT=6)
- [x] Fix ToolStatusGrid: derive from TOOL_NAME_LABELS instead of hardcoded 7-tool array
- [x] Extract FileDropZone to `components/shared/FileDropZone.tsx`
- [x] `npm run build` passes (27 routes)

---

### Sprint 112: Finding Comments — Backend Model + API + Tests
> **Complexity:** 3/10 | **Agent Lead:** BackendCritic + QualityGuardian

- [x] Add FollowUpItemComment model (threaded, self-FK for replies)
- [x] CRUD endpoints on routes/follow_up_items.py
- [x] Include comments in engagement ZIP export
- [x] 41 tests — full regression: 2,155 passed

---

### Sprint 113: Finding Assignments + Collaboration Frontend
> **Complexity:** 3/10 | **Agent Lead:** BackendCritic + FrontendExecutor

- [x] Add assigned_to FK column to FollowUpItem (SET NULL on delete)
- [x] Assignment API endpoints (my-items, unassigned)
- [x] Create CommentThread.tsx + useFollowUpComments.ts hook
- [x] Integrate into FollowUpItemsTable expanded view
- [x] "All / My Items / Unassigned" filter presets
- [x] 15 assignment tests — full regression: 2,170 passed
- [x] `npm run build` passes

---

### Sprint 114: Fixed Asset Testing — Engine + Routes
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic + AccountingExpertAuditor

- [x] Create `backend/fixed_asset_testing_engine.py` (~800 lines, 9 tests)
- [x] 9-test battery: 4 structural (FA-01 to FA-04) + 3 statistical (FA-05 to FA-07) + 2 advanced (FA-08 to FA-09)
- [x] Create `backend/routes/fixed_asset_testing.py` (POST /audit/fixed-assets)
- [x] Add FIXED_ASSET_TESTING to ToolName enum (10 tools)
- [x] 133 tests — full regression: 2,303 passed

---

### Sprint 115: Fixed Asset Testing — Memo + Export
> **Complexity:** 3/10 | **Agent Lead:** BackendCritic + AccountingExpertAuditor

- [x] Create `backend/fixed_asset_testing_memo_generator.py` (IAS 16/ISA 540/500, PCAOB AS 2501)
- [x] PDF + CSV export routes
- [x] 38 tests — full regression: 2,341 passed

---

### Sprint 116: Fixed Asset Testing — Frontend + 10-Tool Nav
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor + FintechDesigner

- [x] Create types, hook, 4 components, page for Fixed Asset Testing
- [x] Update ToolNav (10-tool), homepage ("Ten"), engagement types
- [x] `npm run build` passes

---

### Sprint 117: Inventory Testing — Engine + Routes
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic + AccountingExpertAuditor

- [x] Create `backend/inventory_testing_engine.py` (~900 lines, 9 tests)
- [x] 9-test battery: 3 structural (IN-01 to IN-03) + 4 statistical (IN-04 to IN-07) + 2 advanced (IN-08 to IN-09)
- [x] Create `backend/routes/inventory_testing.py` (POST /audit/inventory-testing)
- [x] Add INVENTORY_TESTING to ToolName enum (11 tools)
- [x] 136 tests — full regression passes

---

### Sprint 118: Inventory Testing — Memo + Export
> **Complexity:** 3/10 | **Agent Lead:** BackendCritic + AccountingExpertAuditor

- [x] Create `backend/inventory_testing_memo_generator.py` (IAS 2/ISA 501/540, PCAOB AS 2501)
- [x] PDF + CSV export routes
- [x] 38 tests — full regression: 2,515 passed

---

### Sprint 119: Inventory Testing — Frontend + 11-Tool Nav
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor + FintechDesigner

- [x] Create types, hook, 4 components, page for Inventory Testing
- [x] Update ToolNav (11-tool), homepage ("Eleven"), engagement types
- [x] `npm run build` passes (29 routes)

---

### Sprint 120: Phase XII Wrap — Regression + v1.1.0
> **Complexity:** 2/10 | **Agent Lead:** QualityGuardian

- [x] Full regression: 2,515 backend tests, 29 frontend routes, 11 tool pages
- [x] All 6 guardrails verified (PASS)
- [x] AccountingExpertAuditor memo review (Fixed Assets + Inventory — COMPLIANT)
- [x] CLAUDE.md: Phase XII COMPLETE, version 1.1.0

### Phase XII Explicit Exclusions (Deferred)

| Feature | Reason | Earliest Phase |
|---------|--------|----------------|
| Budget Variance Deep-Dive | Multi-Period tab refactor prerequisite | Phase XIV |
| Accrual Reasonableness Testing (Tool 12) | Dual-input fuzzy matching complexity | Phase XIV |
| Intercompany Transaction Testing (Tool 13) | Cycle-finding algorithm; narrow applicability | Phase XIV |
| Multi-Currency Conversion | Cross-cutting 11+ engine changes; needs RFC | Phase XIV |
| Engagement Templates | Premature; needs user feedback | Phase XIV |
| Related Party Transaction Screening | Needs external data APIs; 8/10 complexity | Phase XIV+ |
| Expense Allocation Testing | 2/5 market demand; niche | DROPPED |
| Cross-Tool Composite Risk Scoring | ISA 315 violation | REJECTED |
| Management Letter Generator | ISA 265 violation | REJECTED |
