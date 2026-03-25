# Sprints 579–585: Mission Control, Client Hub, Nightly Remediation, UX Polish

Archived from `tasks/todo.md` Active Phase on 2026-03-24.

---

### Sprint 579: Mission Control Dashboard + Multi-Tool UX Overhaul
> Source: CEO directive — de-emphasize TB, surface all 12 tools equally, improve cohesion

#### Backend
- [x] `ToolActivity` model — lightweight, user-level, all-tools activity log (models.py)
- [x] `GET /dashboard/stats` — expanded with tool_runs_today, total_tool_runs, active_workspaces, tools_used
- [x] `GET /activity/tool-feed` — unified activity feed across all tools
- [x] `POST /activity/tool-log` — log tool executions to unified feed
- [x] `GET /settings/preferences` — user tool favorites
- [x] `PUT /settings/preferences` — update favorites (validates tool names)
- [x] `maybe_record_tool_run()` — wired to also create ToolActivity entries
- [x] `testing_route.py`, `file_tool_scaffold.py`, `audit_pipeline.py` — pass filename + record_count

#### Frontend
- [x] MegaDropdown: solid `bg-oatmeal-50` background (was transparent `bg-oatmeal-50/95 backdrop-blur-xl`)
- [x] Dashboard "Mission Control" redesign:
  - 4-column stats: Runs Today / Clients / Workspaces / Last Activity (was TB-only 3-column)
  - Quick Launch grid with 6 pinnable favorite tools (was single TB hero card)
  - Tool-inclusive activity feed with tool icons + labels (was TB-only)
  - Tool-agnostic empty state: "Explore Tools" → /tools (was "Upload first trial balance")
- [x] Tools Catalog page (`/tools`): 13 tools in 3 categories with descriptions, ISA references, tier badges, favorite pins
- [x] toolbarConfig: `/tools` added to `ALL_TOOL_HREFS` for active state detection

- **Tests:** 1,735 frontend — 0 failures; 9 activity API backend tests — 0 failures
- **Verification:** npm run build PASS, npm test PASS (1,735/1,735), pytest test_activity_api PASS (9/9)
- **Status:** COMPLETE

### Sprint 580: Merge Portfolio & Workspaces into Unified Client Hub
> Source: CEO directive — eliminate redundant Portfolio vs. Workspaces navigation

#### Backend
- [x] `ClientEngagementSummary` + `ClientWithSummaryResponse` Pydantic models (schemas/client_schemas.py)
- [x] `get_clients_with_engagement_summary()` — LEFT JOIN clients → engagements → tool_runs (client_manager.py)
- [x] `GET /clients/with-engagement-summary` endpoint (routes/clients.py)

#### Frontend
- [x] ClientCard enhanced: engagement summary inline, expandable workspace list with lazy-load, "New Workspace" button
- [x] Workspace detail route: `/portfolio/[clientId]/workspace/[engagementId]` — extracted 4-tab detail view (Status/Follow-Up/Workpaper/Convergence)
- [x] Portfolio page: wired to enriched client data, CreateEngagementModal with defaultClientId pre-fill
- [x] Engagements page → redirect to `/portfolio`
- [x] Navigation: removed "Workspaces" from TOOLBAR_NAV and ACCOUNT_NAV
- [x] Dashboard: merged Portfolio + Workspaces quick-access into single card
- [x] CreateEngagementModal: added `defaultClientId` prop
- [x] Types: `ClientEngagementSummary`, `ClientWithSummary`, `ClientWithSummaryListResponse`
- [x] Hook: `fetchClientsWithSummary()` in useClients

#### Tests
- [x] PortfolioPage tests updated: mocks for CreateEngagementModal + useClients
- [x] EngagementsPage tests rewritten: redirect behavior (2 tests)

- **Tests:** 1,729 frontend — 0 failures
- **Verification:** npm run build PASS, npm test PASS (1,729/1,729)
- **Status:** COMPLETE

### Sprint 581: Nightly Report Remediation — 7 Bug Fixes + QA + Dependency Upgrades
> Source: 2026-03-24 nightly report (report_auditor YELLOW, dependency_sentinel YELLOW)

#### Bug Fixes (Report Auditor)
- [x] BUG-001: Follow-up procedures now rotate via prefix variation when no alternates exist (follow_up_procedures.py)
- [x] BUG-002: Risk tier assessment generates dynamic text for unrecognized tiers instead of silent "low" fallback (memo_template.py)
- [x] BUG-003: Drill-down column widths proportional to header text length, not naive equal division (drill_down.py)
- [x] BUG-004: Removed orphaned ASC 250-10 reference from sampling memo — replaced with generic standard language (sampling_memo_generator.py)
- [x] BUG-005: Confirmed false positive — `&amp;` is correct ReportLab XML encoding; updated detection keywords (config.py)
- [x] BUG-006: Data quality scoring now domain-aware via hash-based micro-offset; domain param added to 6 engines (data_quality.py + 6 engine files)
- [x] BUG-007: Default `suppress_empty` changed to `False` — empty drill-downs render labeled placeholder instead of silent omission (drill_down.py)

#### QA Fix
- [x] Migration duplicate revision ID: `b1c2d3e4f5a6` used by two files — renamed newer migration to `c2d3e4f5a6b7` (clean_stale_organization_tier)
- [x] `test_migration_f4a5b6c7d8e9_exists` now passes (was CycleDetected from duplicate revision)

#### Dependency Upgrades (Safe)
- [x] fastapi 0.135.1 → 0.135.2 (security patch)
- [x] pypdf ≥6.9.1 → ≥6.9.2 (patch)
- [x] werkzeug ≥3.1.6 → ≥3.1.7 (patch)
- [x] @typescript-eslint/* 8.57.1 → 8.57.2 (patch)

#### Skipped (Require Evaluation)
- [ ] starlette 0.52.1 → 1.0.0 (major — FastAPI pins this; defer until FastAPI supports it)
- [ ] TypeScript 5.9.3 → 6.0.2 (major — potential breaking changes; needs dedicated sprint)
- [ ] pdfminer.six 20251230 → 20260107 (major label but minor maintenance — evaluate separately)

#### Report Auditor Config
- [x] Narrowed BUG_KEYWORDS to target specific anti-patterns, not domain terms (scripts/overnight/config.py)

- **Tests:** 1,729 frontend, 654 core engine, 248 memo, 172 sampling/accrual, 17 drill-down/quality — 0 failures
- **Verification:** npm run build PASS, npm test PASS, pytest targeted suites PASS, migration test PASS
- **Status:** COMPLETE

### Sprint 582: Global Toast Notification System
> Source: UX polish — no feedback system for file uploads, exports, and actions

- [x] `ToastContext` + `ToastProvider` — global toast state with success/error/info types
- [x] `ToastContainer` component — animated bottom-right notifications (framer-motion)
- [x] `useToast` hook — convenience methods (success, error, info) with auto-dismiss (4s success, 6s error)
- [x] No-op fallback when used outside provider (test compatibility)
- [x] Wired into `providers.tsx` provider chain
- [x] Barrel export from `components/shared/index.ts` and `hooks/index.ts`
- [x] Oat & Obsidian themed: sage (success), clay (error), oatmeal (info)
- [x] Accessible: `aria-live="polite"`, `role="status"` on each toast, dismiss button with aria-label

- **Tests:** 8 new tests (ToastSystem.test.tsx) — 0 failures
- **Verification:** npm run build PASS, npm test PASS (1,745/1,745)
- **Status:** COMPLETE

### Sprint 583: First-Run Onboarding Experience
> Source: UX polish — new users land on empty dashboard with no guidance

- [x] `WelcomeModal` component — 3-step onboarding guide
  - Step 1: Upload a Trial Balance (core action)
  - Step 2: Run Diagnostic Tools (12 tools overview)
  - Step 3: Export Audit-Ready Memos (deliverable)
- [x] Progress bar (sage-500) showing current step
- [x] Skip button + completion persistence via `localStorage`
- [x] Shows once per user (800ms delay so dashboard renders first)
- [x] `forceShow` prop for testing/demo purposes
- [x] Accessible: `role="dialog"`, `aria-modal`, `aria-labelledby`
- [x] Wired into dashboard page

- **Tests:** 8 new tests (WelcomeModal.test.tsx) — 0 failures
- **Verification:** npm run build PASS, npm test PASS (1,745/1,745)
- **Status:** COMPLETE

### Sprint 584: Accessibility Fixes
> Source: UX audit — decorative SVGs announced by screen readers, missing dialog semantics

- [x] `ShareExportModal`: added `role="dialog"`, `aria-modal="true"`, `aria-labelledby="share-export-title"`, `id` on h2
- [x] Dashboard stat card SVGs (4): added `aria-hidden="true"`
- [x] Dashboard `getToolIcon` helper SVG: added `aria-hidden="true"`
- [x] Dashboard empty state + Explore Tools button SVGs: added `aria-hidden="true"`
- [x] Dashboard portfolio card SVG: added `aria-hidden="true"`
- [x] Command palette search icon SVG: added `aria-hidden="true"`
- [x] Command palette `EmptyState`: added `role="status"` for dynamic content

- **Tests:** no regressions — 0 failures
- **Verification:** npm run build PASS, npm test PASS (1,745/1,745)
- **Status:** COMPLETE

### Sprint 585: Actionable Error Messages + Toast Wiring
> Source: UX polish — generic error messages, no feedback on upload/export success

#### useAuditUpload — Actionable Error Messages
- [x] Status-aware error mapper: 401 (session expired), 403 (plan upgrade), 413 (file too large), 415 (unsupported format), 422 (column mapping hint), 429 (rate limit), 500 (server issue), 0 (network)
- [x] Toast notification on successful analysis (filename + row count)
- [x] Toast notification on error (actionable message)
- [x] Updated 3 existing tests to match new error message format

#### useTestingExport — Export Feedback
- [x] Toast on successful PDF memo export (filename)
- [x] Toast on successful CSV export (filename)
- [x] Toast on export failure (actionable retry message)

- **Tests:** 1,745 total — 0 failures (3 tests updated for new messages)
- **Verification:** npm run build PASS, npm test PASS (1,745/1,745)
- **Status:** COMPLETE
