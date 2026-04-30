# ADR-018: Backend Domain Package Relocation

**Status:** Accepted (Sprint 753 — pilot landed; full migration is incremental)
**Date:** 2026-04-29
**Decision-makers:** Engineering team

## Context

The backend has 34 top-level `*_engine.py` modules (e.g., `flux_engine.py`,
`recon_engine.py`, `je_testing_engine.py`, `payroll_testing_engine.py`,
`fixed_asset_testing_engine.py`, ...). Each one mixes:

- Domain dataclasses (e.g., `FluxResult`, `ReconScore`, `JETestResult`)
- Analysis logic (e.g., `FluxEngine`, `ReconEngine`, `run_je_testing()`)
- Implicit export contracts (the dict shapes the route + memo generator
  rely on)

Two existing precedents already demonstrate per-domain decomposition:

1. **`backend/audit_engine.py`** (Sprint, pre-700s) is a backward-compat
   shim re-exporting from the `backend/audit/` package. The actual code
   lives in `audit/`, organized into `streaming.py`, `anomaly_rules.py`,
   `classification.py`, etc.
2. **`backend/services/audit/`** (Sprint 753 — this ADR) hosts thin
   service-layer orchestrators (`flux_service.py`, etc.) that route
   handlers call. The engines themselves remain top-level.

Routes, memo generators, exports, and tests reach into the engines via
top-level imports — `from flux_engine import FluxEngine`. This works
but couples consumers to module placement and makes the catalog hard to
read at a glance ("which 18 audit tools have engines? are any
duplicated?").

Sprint 753 (Phase 5 of the architectural remediation initiative) targets
a per-tool domain package layout to surface the catalog and make
engine-internal refactors safer.

## Decision

The canonical layout for new and migrated tools is:

```
backend/services/audit/<tool>/
  __init__.py       # re-exports the public symbols
  analysis.py       # the engine class + run_<tool>() entry point
  schemas.py        # @dataclass / TypedDict result shapes
  export.py         # mapper functions for CSV/PDF/Excel generators
                    # (only when the tool has non-trivial export logic
                    #  beyond a one-line generator call)
```

Top-level `<tool>_engine.py` modules become **backward-compat shims**
re-exporting from the new location, matching the `audit_engine.py`
precedent. Existing `from <tool>_engine import ...` imports continue to
work without modification.

Routes, memo generators, and exports that consume the tool import via
either path; new code SHOULD use the per-tool path
(`from services.audit.<tool>.analysis import ...`).

## Migration discipline

Migration is **incremental, one engine per sub-sprint**, mirroring
ADR-013's discipline for `AuditEngineBase` adoption. The two refactor
axes (subclass `AuditEngineBase` vs. relocate to `services/audit/<tool>/`)
are independent and can land in either order.

Default: **keep flat unless the reorganization adds clear value.** Small
calculators and indicator engines that are only consumed by one route
(e.g., `cutoff_risk_engine.py`, `going_concern_engine.py`) don't gain
much from a per-tool package — keep them at top level until a second
consumer or a non-trivial export contract justifies the split.

The migration order should prioritize:

1. **Engines paired with services already in `services/audit/`** — the
   namespace already exists and the service can move into the per-tool
   package alongside the engine.
2. **Engines with multiple non-trivial consumers** (route + memo
   generator + export serializer) where the split clarifies ownership.
3. **Engines with their own dataclasses + helpers that are co-imported
   from many places** — splitting `analysis.py` from `schemas.py` lets
   tests import the shapes without dragging in the engine.

## Pilot — `recon_engine.py` (Sprint 753)

`recon_engine.py` (193 lines, 4 public symbols: `RiskBand`, `ReconScore`,
`ReconResult`, `ReconEngine`) was selected as the pilot because:

- It's small and self-contained (only imports `flux_engine.FluxResult`
  and `security_utils`).
- It pairs with `flux_engine.py` at the route layer, and
  `services/audit/flux_service.py` already orchestrates the pair — the
  domain namespace `services/audit/flux/` is the natural home.
- It has dedicated tests in `tests/test_recon_engine.py` plus is
  exercised transitively by ~6 callers.

Sprint 753 ships:

- `backend/services/audit/flux/__init__.py` — package marker.
- `backend/services/audit/flux/recon.py` — full implementation moved
  here.
- `backend/recon_engine.py` — backward-compat shim re-exporting the 4
  public symbols. All 6 existing callers (`routes/export_diagnostics.py`,
  `shared/helpers.py`, `leadsheet_generator.py`,
  `export/serializers/excel.py`, `services/audit/flux_service.py`,
  `tests/test_recon_engine.py`) continue to work without modification.

## Lint discipline

Sprint 753 does not yet ship a domain-relocation lint script.
ADR-013's `scripts/lint_engine_base_adoption.py` already enforces the
parallel `AuditEngineBase` axis with advisory CI output; the
domain-relocation lint can be added as a similar advisory scan in
**Sprint 756** (architecture conformance CI checks) when the rest of
the conformance machinery lands.

## Consequences

- The catalog of audit tools becomes legible from `services/audit/`'s
  directory listing — eventually, every tool has a package there.
- Engine-internal refactors (e.g., splitting `analysis.py` into
  `pipeline.py` + `helpers.py`) stay scoped to one package and don't
  ripple through the rest of the codebase.
- The shim pattern preserves existing imports across the migration, so
  engines can move one at a time without coordinated PRs across all
  consumers.
- Per-tool package layout doesn't impose extra files when they're not
  warranted — `schemas.py` and `export.py` are optional. Add them only
  when the tool actually has separable concerns.

## Alternatives considered

- **Big-bang migration of all 34 engines in one sprint.** Rejected —
  high merge-conflict risk, hard to review, hard to roll back. The
  incremental pattern is what worked for ADR-013.
- **Relocate engines without shims.** Rejected — every consumer would
  need updates in the same PR, defeating the incremental approach.
- **Keep engines flat; rely on the lint scan to prevent new top-level
  engines.** Rejected — doesn't address the actual readability /
  catalog-legibility problem.

## See also

- ADR-013 — `AuditEngineBase` adoption (parallel axis, same
  incremental-migration discipline).
- ADR-015 — backend route/service boundaries (Sprint 745+746, the
  template `services/auth/<workflow>.py` pattern this sprint mirrors
  for `services/audit/<tool>/`).
- `backend/audit_engine.py` — existing shim precedent.
- `backend/services/audit/flux_service.py` — existing service-layer
  precedent that the flux pilot is co-locating with.
