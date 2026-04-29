# ADR-015: Backend Route / Service Boundaries

**Status:** Accepted (Sprint 745 + Sprint 746a; broader adoption ongoing)
**Date:** 2026-04-29
**Decision-makers:** Engineering team

## Context

Before Sprint 745, ~12 backend route modules (`routes/auth_routes.py`,
`routes/activity.py`, `routes/diagnostics.py`, `routes/billing.py`, etc.)
duplicated the same commit/rollback/sanitized-500 triad:

```python
try:
    db.commit()
    db.refresh(thing)
except SQLAlchemyError as e:
    db.rollback()
    logger.exception("Database error during ...")
    raise HTTPException(
        status_code=500,
        detail=sanitize_error(e, log_label="..."),
    )
```

Plus inline `HTTPException(...)` raises with ad-hoc detail strings, scattered
across 4xx (validation), 403 (entitlement), 404 (not-found), and 5xx (service)
paths.

Auth routes specifically (`routes/auth_routes.py` — 778 lines) carried mixed
orchestration + business logic: registration, login, token refresh, logout,
verification, password reset, session inventory/revocation all lived in one
file with their full implementation inline, not delegating to services.

## Decision

### 1. Unit-of-work helper for DB transactions

`shared.db_unit_of_work.db_transaction(db, *, log_label, log_message=None)`
is the canonical context manager for any route handler that mutates the
database. Replaces the inline triad above with:

```python
with db_transaction(db, log_label="db_register"):
    db.add(user)
db.refresh(user)  # outside the with block; commit already ran
```

On `SQLAlchemyError`: rolls back, logs, raises sanitized
`HTTPException(500)`. Non-SQLAlchemy exceptions propagate uncaught.

### 2. Shared route-error helper for non-DB error paths

`shared.route_errors.raise_http_error(status_code, *, label, user_message,
exception, operation, allow_passthrough)` is the canonical helper for
4xx and non-DB 5xx error responses. Centralizes:

- `sanitize_error` integration (no PII / SQL / paths leaked in detail).
- Structured-log metadata via `log_secure_operation(label, ...)`.
- Passthrough mode for business-logic `ValueError` whose message is
  already user-facing.

### 3. Service layer for multi-step business logic

When a route handler exceeds ~25 lines or interleaves multiple persistence
+ validation + side-effect concerns, extract the workflow to a service
module:

```
backend/services/<domain>/<workflow>.py
```

The route becomes a thin controller: validate input → call service → return
typed response (or map service exceptions to `HTTPException`).

Service modules must:

- Accept the SQLAlchemy `Session` as an argument (no global session lookup).
- Raise domain-specific exception subclasses (e.g., `PasswordResetError(ValueError)`)
  for business-logic failures; routes map these to 4xx `HTTPException`.
- Use `db_transaction` for any commit/rollback work.
- Not import from `fastapi` (no `HTTPException`, `Request`, `Response`,
  `BackgroundTasks` — those are HTTP-layer concerns owned by the route).

## Boundary discipline

The cookie / CSRF primitives in `routes/auth_routes.py` (`_set_refresh_cookie`,
`_set_access_cookie`, `_clear_refresh_cookie`, `_clear_access_cookie`) are
**security-sensitive and stay in the route layer.** Service-layer extractions
move business logic only. This honors the deferred-items guidance in
`tasks/todo.md`: "touching cookie/token primitives without a specific bug or
audit finding is net-negative."

## Enforcement

Pattern-only for now. Sprint 756 adds CI conformance checks:

- Forbidden imports (route → engine internals; service → fastapi).
- Banned direct DB commit/rollback in routes (must go through `db_transaction`).
- Module-boundary tests asserting routes don't bypass service contracts.

Until Sprint 756, code review enforces the pattern. New route handlers
should reach for `db_transaction` and `raise_http_error` by default.

## Migration

Incremental, route by route. Status per module is tracked in `tasks/todo.md`.

| Module | Status | Sprint |
|--------|--------|--------|
| `routes/activity.py` | Migrated (4 sites) | 745 |
| `routes/auth_routes.py` — recovery (2 routes) | Migrated to `services/auth/recovery.py` | 746a |
| `routes/auth_routes.py` — identity / registration / sessions | PENDING | 746b/c/d |
| Remaining ~10 route modules | PENDING — natural follow-ups in Sprints 747–755 | — |

## Consequences

- New route handlers default to `db_transaction` + `raise_http_error`
  instead of inline `try/except SQLAlchemyError` patterns.
- Service modules become testable in isolation (no FastAPI fixtures
  needed to exercise business logic).
- Auth routes can shrink from 778 lines to ~300 over Sprints 746b/c/d as
  identity / registration / sessions extractions land.
- `db.refresh(...)` after the `with db_transaction(...)` block is virtually
  guaranteed not to raise on a healthy session, since the transaction is
  already durable. If it does, the 500 propagates uncaught — same observable
  behavior as the legacy code (which would call `db.rollback()` on an
  already-committed transaction, a no-op, before raising).

## Alternatives considered

- **Decorator instead of context manager** (`@with_db_transaction`).
  Rejected — context manager makes the transaction boundary explicit at the
  call site and composes cleanly with non-DB code in the same handler.
- **Single mega-helper** combining `db_transaction` + `raise_http_error`.
  Rejected — different ergonomic surfaces (one wraps a block, the other is
  a one-shot raise) deserve separate APIs.
- **Skip the service layer; just clean up routes in place.** Rejected — the
  point is testability + decomposability for Sprints 747–759. Inline cleanup
  doesn't deliver that.

## See also

- Sprint 745 + Sprint 746a reviews in `tasks/todo.md`.
- `backend/shared/db_unit_of_work.py` and `backend/tests/test_db_unit_of_work.py`.
- `backend/shared/route_errors.py` and `backend/tests/test_route_errors.py`.
- `backend/services/auth/recovery.py` — first service-layer module.
- `tasks/todo.md` Deferred Items: cookie/CSRF helper extraction (boundary).
