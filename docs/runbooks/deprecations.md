# Deprecation Register

> Central index for production code paths and fields that are formally
> deprecated but still present for compatibility. Every entry must have
> an owner and a removal trigger so deprecations do not linger indefinitely.
>
> Added in Sprint 677 (dead-code hygiene).

## How to use this register

- Add an entry the moment a code path is marked deprecated (docstring,
  `@deprecated`, feature flag, or runtime warning).
- Keep the **removal trigger** concrete: a callsite-count threshold, a
  downstream migration, or a calendar date. "Someday" is not a trigger.
- Move an entry to **Removed** once the code is deleted (keep for one
  sprint for traceability, then prune).

## Active Deprecations

| Component / File | Deprecation reason | Owner | Removal trigger | Target sprint/date | Status |
|------------------|-------------------|-------|-----------------|-------------------|--------|
| `backend/excel_generator.py` (`prepared_by`, `reviewed_by`, `workpaper_date`, `include_signoff`) | Workpaper sign-off rendering moved to engagement-layer flow in Sprint 7; fields retained for backward-compatible callers that still set `include_signoff=True` | IntegratorLead | Zero external callers setting `include_signoff=True` across three consecutive nightly reports | Review 2026-Q3 | Active — gated (default off) |
| `backend/pdf/orchestrator.py` (`include_signoff` path through `render_workpaper_signoff`) | Same Sprint 7 migration — PDF signoff section is dead unless explicitly opted into by the caller | IntegratorLead | Concurrent removal with `excel_generator.py` signoff block | Review 2026-Q3 | Active — gated (default off) |
| `backend/shared/schemas.py` workpaper signoff fields (`prepared_by`, `reviewed_by`, `workpaper_date`, `include_signoff` in `ExportRequest`) | Schema fields retained to avoid breaking serialized requests while `include_signoff` is still a valid toggle | IntegratorLead | Concurrent removal with generator + orchestrator sign-off blocks | Review 2026-Q3 | Active — schema-present, default off |
| `backend/shared/parsing_helpers.py::safe_float` | Deprecated for monetary values per Sprint 340+ Decimal migration; float precision is unsafe for currency arithmetic. `safe_decimal` is the canonical replacement | IntegratorLead | Zero callers in monetary paths; retain for non-monetary numeric parsing (ratios, rates, etc.) | Ongoing hygiene | Active — non-monetary uses allowed |
| `frontend/src/utils/motionTokens.ts::DISTANCE` | Entrance distances migrated to `lift` in `@/lib/motion`; `DISTANCE` retained only for internal tool-state transitions that predate the migration | IntegratorLead | Remaining internal callers inside `motionTokens.ts` refactored to `lift`/spring tokens | Post-design-lock (est. Sprint 700 window) | Active — internal-only |

## Removed (historical, prune after one sprint)

_None at Sprint 677._
