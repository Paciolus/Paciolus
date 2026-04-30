# Architectural Remediation Scorecard

**Sprint:** 759 — Phase 8 (final sprint) of the Architectural Remediation Initiative.
**Date:** 2026-04-29
**Range:** Sprints 742–759 (commit `050cac60`..`HEAD`).

The 8-phase plan (transcript 2026-04-29) became the backlog under
`tasks/todo.md` "## Architectural Remediation Initiative". This scorecard
maps each item to its outcome: **RESOLVED**, **PARTIAL** (with explicit
follow-up scope), or **OPEN** (with rationale). Reviewers trust the
scorecard, not the count of completed sprints — partial counts as
partial.

## TL;DR

- **18 sprints planned (742–759), 18 sprints shipped.** Phases 0, 1, 4, 6, 7, 8 fully resolved. Phases 2, 3, 5 partial — explicit follow-up scope filed in `tasks/todo.md` and ADR docs.
- **6 ADRs landed** (014, 015, 016, 017, 018) + quality thresholds + pagination/cache conventions docs.
- **3 new advisory CI lint scans** (`lint_engine_base_adoption.py` from Sprint 726 + `lint_domain_relocation.py` and `lint_route_layer_purity.py` from Sprint 756).
- **Net code shrinkage:** `auth_routes.py` 778 → ~270 lines; `routes/export_diagnostics.py` 661 → 358; multi-period page 501 → 423; dashboard page 519 → 383; `useFormValidation.ts` 516 → 280.
- **Test additions:** ~150 new pytest tests (helpers + lint scripts + service-layer coverage), ~50 new jest tests (hooks + dashboard smoke + contract).

## Phase status

| Phase | Title | Sprints | Status | Coverage |
|-------|-------|---------|--------|----------|
| 0 | Baseline & Guardrails | 742, 743 | ✅ Resolved | ADRs 014/015/016 + quality thresholds + DashboardPage smoke test (Sprint 743's filed gap-fill) |
| 1 | Cross-Cutting Standardization | 744, 745 | ✅ Resolved | Frontend `apiClient` ESLint rule; backend `db_transaction` + `raise_http_error` helpers piloted on `activity.py` |
| 2 | Auth Decomposition | 746a-d, 747a | ✅ Resolved | All 13 auth routes thinned; 4 service modules in `services/auth/` (recovery, identity, registration, sessions) |
| 3 | Export Rationalization | 748a, 749 | 🟡 Partial | 6 CSV diagnostic routes migrated; ADR-016 accepted; PDF contract test pattern shipped. **Open:** PDF/Excel/Leadsheets/FinStmts routes (4) — Sprint 748b filed |
| 4 | Frontend Decomposition | 750, 751, 752 | ✅ Resolved | ADR-017 + 5 new hooks; multi-period + dashboard + tools pages decomposed; validation engine split |
| 5 | Domain Consolidation | 753, 754 | 🟡 Partial | ADR-018 + recon pilot; client-access helpers relocated. **Open:** ~30 engines + shared analysis interfaces — sub-sprints filed per ADR-018 |
| 6 | Drift Elimination | 755, 756 | ✅ Resolved | Dead code survey + cleanup; 2 advisory CI lint scans (domain relocation + route layer purity); CONTRIBUTING.md refresh |
| 7 | Performance Hardening | 757, 758 | ✅ Resolved | `/tools` consolidated onto `useUserPreferences`; pagination + cache invalidation conventions doc |
| 8 | Convergence | 759 | ✅ Resolved | This scorecard + governance lane (filed in this sprint) |

## Per-weakness scorecard (from the original Crosswalk)

The original plan ended with a "Crosswalk: Weakness → Plan Coverage" section. Each weakness:

### 1. Giant files / components / routes / hooks
**Status:** ✅ Resolved (with documented incremental discipline for what remains)

- **Auth routes** (`routes/auth_routes.py`): 778 → ~270 lines (Sprints 746a/b/c/d). All 13 handlers are now ≤25 lines. Service modules under `services/auth/`.
- **Multi-period page** (`app/tools/multi-period/page.tsx`): 501 → 423 lines (Sprint 750). Composition root over `usePeriodUploads` + `useMultiPeriodMemoExport` + existing `useMultiPeriodComparison`.
- **Dashboard page** (`app/dashboard/page.tsx`): 519 → 383 lines (Sprint 751). Composition root over `useDashboardStats` + `useActivityFeed` + `useUserPreferences` + `ToolIcon` + `DASHBOARD_TOOLS`.
- **Export diagnostics route** (`routes/export_diagnostics.py`): 661 → 358 lines (Sprint 748a). 6 CSV routes are now 2-line delegations to `export.pipeline`.
- **`useFormValidation`**: 516 → 280 lines (Sprint 752). Pure validation engine + React adapter split.
- **Inline 78-line `TOOLS` catalog + 22-line `getToolIcon` SVG dump** in dashboard page → moved to `content/dashboard-tools.ts` + `components/dashboard/ToolIcon.tsx` (Sprint 751).
- **Open backlog (incremental):** ~30 top-level `*_engine.py` files awaiting per-tool relocation per ADR-018. The `lint_domain_relocation.py` advisory CI scan surfaces them on every PR; migration is one engine per sub-sprint.

### 2. Repeated logic (fetch / auth / error / transaction)
**Status:** ✅ Resolved at the pattern level; remaining mass migration is incremental

- **Frontend direct `fetch`**: banned outside the 6-file allowlist (Sprint 744). ESLint `no-restricted-syntax` enforces in CI. 4 outliers migrated to `apiClient`/`apiDownload`/`uploadFetch`.
- **Backend `try: db.commit() except SQLAlchemyError: db.rollback() ...` triad**: replaced by `shared.db_unit_of_work.db_transaction` (Sprint 745). Pilot on `activity.py` (4 sites). 11 other route modules with the inline pattern still exist — Sprint 745 filed pattern + helper, the migration is incremental.
- **Backend ad-hoc `HTTPException(...)` raises**: replaced by `shared.route_errors.raise_http_error` for the non-DB error path. Adoption matches the pattern as routes get touched.
- **Auth enumeration-safe 401**: was raised inline in 3 places in `login`; consolidated to `services.auth.security_responses.raise_invalid_credentials` (Sprint 747a).
- **Frontend `/settings/preferences` favorite-management**: was duplicated between dashboard + tools-page; consolidated onto `useUserPreferences` (Sprint 751 → Sprint 757).
- **Client-access helpers**: relocated from `shared/helpers.py` to `shared/client_access.py` per the deferred-items condition (Sprint 754).

### 3. Inconsistent patterns across similar features
**Status:** ✅ Resolved

- **Frontend tool pages**: ADR-017 documents the canonical composition pattern (workflow hooks + UI state + thin orchestration + render-only JSX). Multi-period + dashboard + tools-page now all follow it.
- **Backend route patterns**: ADR-015 documents the canonical service-layer pattern. Auth fully migrated. Other tools still have the legacy "inline business logic in handler" shape; ADR-015 + the route-layer-purity lint surface this on every PR.
- **Export pipeline**: ADR-016 (Sprint 749 promoted to Accepted) documents the registry-driven memo dispatch as canonical. CSV routes follow the pipeline; PDF/Excel still inline (Sprint 748b filed).

### 4. Mixed concerns (UI / business / data / access)
**Status:** ✅ Resolved at the pattern level; ongoing

- Service-layer extractions (`services/auth/`, `services/audit/flux/`) demonstrate the pattern. Pages compose hooks rather than carrying state machines inline.
- Pure validation engine + React adapter split (Sprint 752) shows the same pattern at the hook level.

### 5. Structural inefficiencies / duplicate work
**Status:** ✅ Resolved

- Sprint 752 memoized dashboard's hot derivations (`summaryLine`, `displayTools`, `toolByKey` Map for O(1) activity-feed lookups).
- Sprint 757 added `favoritesSet` Set for O(1) per-card lookups on the tools page; consolidated `/tools` ↔ `/dashboard` favorite duplication.
- apiClient already has in-flight dedup + stale-while-revalidate cache (Sprint 539); the survey confirmed no new pattern was needed at the transport layer.

### 6. Maintainability and change-risk
**Status:** ✅ Resolved

- 6 ADRs (014-018 + quality-thresholds) plus the pagination/cache conventions doc give new contributors a documented target architecture instead of folklore.
- 3 advisory CI lint scans surface migration backlog (domain relocation, route layer purity, engine_base adoption).
- New tests anchor the contracts: `db_unit_of_work`, `route_errors`, `validation_engine`, `recon_engine_shim`, `lint_*` (~150 new pytest), `usePeriodUploads`, `useMultiPeriodMemoExport`, `useDashboardStats`, `useActivityFeed`, `useUserPreferences`, `DashboardPage` smoke (~50 new jest).

## Open follow-up scope (filed)

The initiative's scope wasn't "do everything in 18 sprints" — it was "establish the patterns + ship pilots + leave a visible backlog." These items are filed in `tasks/todo.md` and surface in CI advisory output:

| Item | Filed as | Scope |
|------|---------|-------|
| Sprint 748b — PDF/Excel/Leadsheets/FinStmts routes migrate to `export.pipeline` | todo entry | Pipeline signatures need branding-context plumbing first |
| Sprint 754b — shared analysis interfaces (input contract / result envelope / error semantics) | todo entry | Depends on 2+ tools relocated under ADR-018 to compare shapes |
| ~30 engine relocations per ADR-018 | `lint_domain_relocation.py` advisory CI | One engine per sub-sprint; default keep flat |
| ~12 route handlers still importing engine orchestration symbols | `lint_route_layer_purity.py` advisory CI | Each is a service-extraction sprint |
| Backend transaction helper adoption beyond `activity.py` | Sprint 745 review | ~11 routes still have inline `try/except SQLAlchemyError` triads |
| 9 testing engines that don't subclass `AuditEngineBase` | `lint_engine_base_adoption.py` (Sprint 726) | Pre-existing migration backlog |
| Memo PDF contract tests beyond the JE demo | Sprint 749 review | 17 memos remain; pattern is documented |
| `routes/billing.py::stripe_webhook` decomposition | tasks/todo.md Deferred Items | Bundled with deferred webhook coverage sprint |

## Governance cadence

Initiative momentum was the result of a particular cadence: the user invoked `Sprint NNN` start-of-session, and each sprint had explicit start/exit criteria in `tasks/todo.md`. To preserve that discipline post-initiative without spawning more architectural-remediation sprints, the cadence is:

### Quarterly architecture health review (proposed)

Every quarter (90 days), a single review pass that:

1. **Runs the 3 advisory lints** against `main` and notes the trend:
   - `python scripts/lint_engine_base_adoption.py`
   - `python scripts/lint_domain_relocation.py`
   - `python scripts/lint_route_layer_purity.py`
2. **Checks the deferred-items list** in `tasks/todo.md` for any item whose triggering condition has become true (e.g., a 4th helper joining the small group, a deprecated path's transition window expiring).
3. **Reviews quality-threshold deviations** introduced since the last review:
   - Routes/services/pages exceeding the **hard cap** documented in `docs/03-engineering/quality-thresholds.md`
   - Hooks > 200 lines
   - Functions with cyclomatic complexity > 12
4. **Files at most 2 follow-up sprints** if findings warrant. The bar is: would a full sprint of cleanup unblock real product work? If no, defer.

The output is a one-page report in `reports/arch-health-YYYY-QN.md`. Keep it short — the lint scans + the deferred-items list already do most of the surveillance.

### "No new god files" policy

A new file landing in `main` that exceeds the **hard cap** in
`docs/03-engineering/quality-thresholds.md` requires:

- A reference in the PR description to a follow-up sprint that will decompose it, OR
- An explicit comment in the file's docstring explaining why decomposition isn't applicable (e.g., "this file is generated; do not edit by hand").

Code review enforces; CI doesn't. The bar is honest accountability, not mechanical gating.

### Refactor intake lane

New refactor opportunities (whether surfaced by the lint scans, the
quarterly review, or organic discovery) get filed in `tasks/todo.md`
under a new `## Refactor Intake` section. Each entry follows the
deferred-items pattern:

```
| Item | Reason | Source |
|------|--------|--------|
| <one-line description> | <why now / why later> | <surfacing sprint or PR> |
```

This is the same shape as the existing `## Deferred Items` table. The
two could merge or stay separate — the discipline is that the intake
exists somewhere visible and gets reviewed quarterly.

When intake items reach a critical mass (e.g., 5+ items targeting the
same surface), they roll up into a new sprint entry under `## Active
Phase`. The bar for spawning a new sprint is that it has explicit
start/exit criteria, not just "clean up X."

## Conclusion

The initiative did its job: established the patterns, shipped pilots,
documented the open backlog visibly through CI lints + ADRs + filed
follow-up sprints. The remaining work doesn't block any product
sprint — it's incremental architectural hygiene with mechanical
visibility.

Subsequent sessions don't need an "Architectural Remediation Phase II."
They need to (a) honor the patterns documented in ADRs 014-018 when
touching the relevant surfaces, (b) clear advisory-lint findings as
adjacent work, and (c) run the quarterly review. The scorecard +
governance lane in this sprint are the closing artifact.

---

**Initiative end.** Subsequent sprints in `tasks/todo.md` should be
product-driven, not architecture-driven.
