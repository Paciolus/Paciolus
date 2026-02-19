# Phase XLI: Cross-Tool Workflow Integration (Sprints 308–312)

## Overview
Bridges 5 workflow gaps between existing tools — small, high-value connective tissue. No new tools or modules; all changes additive to existing infrastructure.

---

## Sprint 308 — Lead Sheet Cross-Refs + Convergence Completion

| # | Task | Status |
|---|------|--------|
| 1 | Add A-Z lead sheet codes to `TOOL_LEAD_SHEET_REFS` in `workpaper_index_generator.py` | COMPLETE |
| 2 | Add `FLUX_ANALYSIS` to `ToolName` enum in `engagement_model.py` | COMPLETE |
| 3 | Create Alembic migration `f8a3d1c09b72` for PG enum expansion | COMPLETE |
| 4 | Register `extract_flux_accounts` in `ACCOUNT_EXTRACTORS` registry | COMPLETE |
| 5 | Wire flux route for engagement (engagement_id, BackgroundTasks, flagged accounts) | COMPLETE |
| 6 | Add `tools_covered` / `tools_excluded` to `ConvergenceResponse` | COMPLETE |
| 7 | Add `CONVERGENCE_TOOLS` / `CONVERGENCE_EXCLUDED` constants | COMPLETE |
| 8 | Update frontend `ToolName` type, `TOOL_NAME_LABELS`, `TOOL_SLUGS` | COMPLETE |
| 9 | Update frontend `ConvergenceResponse` type | COMPLETE |
| 10 | Fix 6 existing tests with hardcoded tool counts (12→13) | COMPLETE |
| 11 | Add 17 new tests (flux extractor, enum, lead sheet refs, convergence coverage) | COMPLETE |

**Review:**
- 7 GL-account-level tools now have convergence extractors (was 6)
- `extract_flux_accounts` was defined but unregistered — now wired into convergence pipeline
- Flux route gains engagement_id + BackgroundTasks for tool run recording
- A-Z financial statement lead sheet codes added to 10 tools (e.g., "G (Accounts Payable)" for AP)
- `tools_covered`/`tools_excluded` in convergence response documents coverage boundaries

---

## Sprint 309 — Pre-Flight → Column Passthrough (Frontend Only)

| # | Task | Status |
|---|------|--------|
| 1 | Extract column mappings from `preflight.report.columns` in `handlePreflightProceed` | COMPLETE |
| 2 | Add `columnMappingSource` state ('preflight' / 'manual' / null) | COMPLETE |
| 3 | Pass extracted mapping to `runAudit()` | COMPLETE |
| 4 | Reset `columnMappingSource` on file upload and column mapping modal | COMPLETE |
| 5 | Add 8 frontend tests for extraction logic | COMPLETE |

**Review:**
- Pre-flight columns with `status==='found'` and `confidence >= 0.8` passed directly to TB audit
- Requires all 3 columns (account, debit, credit) to meet threshold; otherwise TB re-detects
- `columnMappingSource` exposed in hook return for UI indicator
- Zero backend changes — `column_mapping` Form parameter already existed

---

## Sprint 310 — Materiality Cascade Passthrough

| # | Task | Status |
|---|------|--------|
| 1 | Add `_resolve_materiality()` helper to `routes/audit.py` | COMPLETE |
| 2 | Apply to trial-balance endpoint | COMPLETE |
| 3 | Apply to flux endpoint | COMPLETE |
| 4 | Apply to expense-category endpoint | COMPLETE |
| 5 | Add `materiality_source` to `TrialBalanceResponse` schema | COMPLETE |
| 6 | Add frontend `useEffect` for engagement materiality pre-fill | COMPLETE |
| 7 | Add 8 backend tests for `_resolve_materiality()` | COMPLETE |

**Review:**
- Priority: explicit threshold > engagement cascade > default (0.0)
- Returns `(threshold, source)` tuple where source is 'manual', 'engagement', or 'none'
- Performance materiality (PM = amount × factor) used from engagement cascade
- Frontend pre-fills slider from `engagement.materiality.performance_materiality`
- Backend helper is defense-in-depth for direct API callers

---

## Sprint 311 — Composite Score Trend

| # | Task | Status |
|---|------|--------|
| 1 | Add `get_tool_run_trends()` to `EngagementManager` | COMPLETE |
| 2 | Add `ToolRunTrendResponse` schema to `routes/engagements.py` | COMPLETE |
| 3 | Add `GET /engagements/{id}/tool-run-trends` endpoint | COMPLETE |
| 4 | Add `ToolRunTrend` type to frontend `types/engagement.ts` | COMPLETE |
| 5 | Add `getToolRunTrends()` to `useEngagement` hook | COMPLETE |
| 6 | Add `TrendIndicator` component + wire into `ToolStatusGrid` | COMPLETE |
| 7 | Add 9 backend tests (empty, single, improving, degrading, stable, exclusions, sorting) | COMPLETE |

**Review:**
- Scores represent flag density — lower = fewer flags = improving
- Direction: delta < -1 → improving, delta > 1 → degrading, else stable
- Only completed runs with non-null composite_score qualify
- Frontend shows directional arrows: ↓ sage (improving), ↑ clay (degrading), ↔ muted (stable)
- `trends` prop optional on ToolStatusGrid for backward compatibility

---

## Sprint 312 — Phase XLI Wrap

| # | Task | Status |
|---|------|--------|
| 1 | Full `pytest` regression | COMPLETE |
| 2 | `npm run build` passes | COMPLETE |
| 3 | Archive to `tasks/archive/phase-xli-details.md` | COMPLETE |
| 4 | Update `CLAUDE.md`, `MEMORY.md`, `tasks/todo.md` | COMPLETE |
| 5 | Git commit | COMPLETE |
