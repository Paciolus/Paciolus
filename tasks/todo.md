# Paciolus Development Roadmap

> **Protocol:** See [`tasks/PROTOCOL.md`](PROTOCOL.md) for lifecycle rules, post-sprint checklist, and archival thresholds.
>
> **Completed eras:** See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for all historical phase summaries.
>
> **Executive blockers:** See [`tasks/EXECUTIVE_BLOCKERS.md`](EXECUTIVE_BLOCKERS.md) for CEO/legal/security pending decisions.
>
> **CEO actions:** All pending items requiring your direct action are tracked in [`tasks/ceo-actions.md`](ceo-actions.md).

---

## Hotfixes

> For non-sprint commits that fix accuracy, typos, or copy issues without
> new features or architectural changes. Each entry is one line.
> Format: `- [date] commit-sha: description (files touched)`

- [2026-03-21] 8b3f76d: resolve 25 test failures (4 root causes: StyleSheet1 iteration, Decimal returns, IIF int IDs, ActivityLog defaults), 5 report bugs (procedure rotation, risk tier labels, PDF overflow, population profile, empty drill-downs), dependency updates (Next.js 16.2.1, Sentry, Tailwind, psycopg2, ruff)
- [2026-03-21] 8372073: resolve all 1,013 mypy type errors — Mapped annotations, Decimal/float casts, return types, stale ignores (#49)
- [2026-03-20] AUDIT-07-F5: rate-limit 5 unprotected endpoints — webhook (10/min), health (60/min), metrics (30/min); remove webhook exemption from coverage test
- [2026-03-19] CI fix: 8 test failures — CircularDependencyError (use_alter), scheduler_locks mock, async event loop, rate limit decorators, seat enforcement assertion, perf budget, PG boolean literals
- [2026-03-18] 7fa8a21: AUDIT-07-F1 bind Docker ports to loopback only (docker-compose.yml)
- [2026-03-18] 52ddfe0: AUDIT-07-F2 replace curl healthcheck with python-native probe (backend/Dockerfile)
- [2026-03-18] 5fc0453: AUDIT-07-F3 create /app/data with correct ownership before USER switch (backend/Dockerfile)
- [2026-03-07] fb8a1fa: accuracy remediation — test count, storage claims, performance copy (16 frontend files)
- [2026-02-28] e3d6c88: Sprint 481 — undocumented (retroactive entry per DEC F-019)

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| ~~Password reset flow (NEW-015)~~ | RESOLVED — Sprint 572 | Sprint 569 |

---

## Active Phase
> Sprints 478–531 archived to `tasks/archive/sprints-478-531-details.md` (consolidated).
> Sprints 532–561 archived to `tasks/archive/sprints-532-561-details.md` (consolidated).
> FIX-1A/1B, Sprint 562, FIX-2A/2B archived to `tasks/archive/fix-1-2-sprint562-details.md`.
> FIX-3–8B, AUDIT-09–10 archived to `tasks/archive/fix-3-8b-audit-09-10-details.md`.
> Sprints 563–569, CI-FIX archived to `tasks/archive/sprints-563-569-details.md`.
> Sprints 570–571 archived to `tasks/archive/sprints-570-571-details.md`.
> Sprints 572–578 archived to `tasks/archive/sprints-572-578-details.md`.

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

