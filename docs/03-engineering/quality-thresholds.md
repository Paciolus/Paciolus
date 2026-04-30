# Code Quality Thresholds

**Status:** Advisory (Sprint 742 — definitions only). Becomes enforceable via CI in Sprint 756.

These thresholds set targets for module size, function complexity, and hook
size. They are deliberately advisory at first so the architectural-remediation
sprints (744–759) can land without CI churn. Sprint 756 wires the
enforcement step.

## Why these thresholds

Empirically, modules and functions exceeding these bands in the Paciolus
codebase have been the ones flagged for decomposition by code reviews and
agent sweeps. The numbers below are calibrated against the existing healthy
modules (which mostly clear them) and the modules tagged for refactor in
Sprints 746–752 (which do not).

## Module size (lines of code)

| Layer | Target | Hard cap |
|-------|--------|----------|
| Backend route module (`routes/<x>.py`) | 500 | 800 |
| Backend service module (`services/<domain>/<workflow>.py`) | 300 | 500 |
| Backend engine (`*_engine.py`) | 600 | 1000 |
| Frontend page (`app/.../page.tsx`) | 400 | 700 |
| Frontend component (`components/.../*.tsx`) | 300 | 500 |
| Frontend hook (`hooks/use*.ts`) | 200 | 400 |
| Test module | (no limit — split by surface, not size) |

A module exceeding the **target** earns a code-review flag.
A module exceeding the **hard cap** must be decomposed in the same PR
(or a follow-up explicitly filed before merge).

## Function / method complexity

| Metric | Target | Hard cap |
|--------|--------|----------|
| Cyclomatic complexity (per function) | 8 | 12 |
| Lines per function (excluding docstring) | 40 | 80 |
| Function arguments | 5 | 8 (kwargs-only above 5) |

Tools:

- Backend: `ruff` rule `C901` (configurable threshold). Currently advisory.
- Frontend: ESLint `complexity` rule. Currently advisory.

## React hook size

| Metric | Target | Hard cap |
|--------|--------|----------|
| Lines per hook | 150 | 300 |
| `useState` declarations per hook | 4 | 8 |
| Returned API surface (count of returned fields) | 6 | 12 |

Hooks above the hard cap must split into a pure-logic engine + React
adapter (per the Sprint 752 template).

## Direct fetch ban (already enforced)

Direct `fetch()` is banned outside the allowlist documented in
[ADR-014](adr-014-canonical-frontend-network-layer.md). This is a
**hard rule**, not an advisory threshold — enforced in CI by ESLint
`no-restricted-syntax` (Sprint 744).

## Inline DB transaction ban (advisory until Sprint 756)

Inline `try: db.commit() except SQLAlchemyError: db.rollback()` blocks in
route handlers are forbidden going forward. Use `db_transaction` from
`shared.db_unit_of_work` per [ADR-015](adr-015-backend-route-service-boundaries.md).

Sprint 756 will add a CI check (forbidden pattern detection) for new
violations.

## How to apply

When opening a PR that adds or modifies code:

- New code SHOULD clear the **target** thresholds.
- New code MUST clear the **hard cap** thresholds.
- Modifying existing code that already exceeds a target is fine, but
  prefer to split as part of the change rather than grow the violation.

When a sprint touches a module whose existing size exceeds the hard cap
(e.g., `routes/auth_routes.py` at 778 lines today), the sprint either:

- Decomposes the module as part of its scope (Sprint 746a's pattern), or
- Documents the deferral with a follow-up sprint number.

## See also

- [ADR-014](adr-014-canonical-frontend-network-layer.md) — frontend network
  layer enforcement.
- [ADR-015](adr-015-backend-route-service-boundaries.md) — route/service
  decomposition pattern.
- [ADR-016](adr-016-export-architecture.md) — export mapper/generator
  separation.
- `tasks/todo.md` Architectural Remediation Initiative — Sprints 744–759.
