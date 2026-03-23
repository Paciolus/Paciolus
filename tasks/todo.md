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
| ~~Rate limiter → Redis storage backend~~ | RESOLVED — Sprint 563 | AUDIT-07 Phase 5 |
| ~~ORGANIZATION tier cleanup migration~~ | RESOLVED — Sprint 570 (Alembic `b1c2d3e4f5a6`) | Sprint 565 NEW-001 |
| Password reset flow (NEW-015) | Requires dedicated backend sprint (token generation, email dispatch, reset endpoint) | Sprint 569 |

---

## Active Phase
> Sprints 478–531 archived to `tasks/archive/sprints-478-531-details.md` (consolidated).
> Sprints 532–561 archived to `tasks/archive/sprints-532-561-details.md` (consolidated).
> FIX-1A/1B, Sprint 562, FIX-2A/2B archived to `tasks/archive/fix-1-2-sprint562-details.md`.
> FIX-3–8B, AUDIT-09–10 archived to `tasks/archive/fix-3-8b-audit-09-10-details.md`.
> Sprints 563–569, CI-FIX archived to `tasks/archive/sprints-563-569-details.md`.

### Sprint 570: DEC 2026-03-23 Remediation (5 Findings)
> Source: `reports/council-audit-2026-03-23.md`

#### P2 — Medium
- [x] **F-002:** Alembic migration `b1c2d3e4f5a6` to clean stale `ORGANIZATION` tier values in `users.tier` → `FREE`
- [x] **F-001:** Route-level tests for `audit_flux.py` (5 tests: auth gates, validation, success, error) and `audit_preview.py` (5 tests: auth gates, success, quality gate, error)

#### P3 — Low
- [x] **F-003:** Complete export schema migration — migrated 32 imports across 7 test files from `routes.export` → `shared.export_schemas`; removed re-export shim + TODO from `routes/export.py`
- [x] **F-004:** Replaced 9 `bg-white` instances with `bg-oatmeal-50` in 4 files (HeroFilmFrame, HeroProductFilm, MegaDropdown, VaultTransition)
- [x] **F-005:** Fixed archive script + commit-msg hook pattern — removed `^` anchor so `- **Status:** COMPLETE` is matched

- **Tests:** 7,096 backend (10 new), 1,725 frontend — 0 failures
- **Verification:** pytest PASS, npm run build PASS, npm test PASS (1,725/1,725), 0 `bg-white`, 0 `from routes.export import`, archive pattern verified
- **Status:** COMPLETE

