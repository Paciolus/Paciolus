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
| ~~Composite Risk Scoring~~ | ~~Requires ISA 315 inputs~~ — **RESOLVED Sprint 562** | Phase XI |
| ~~Test file mypy — full cleanup~~ | ~~804 errors across 135 files~~ — **RESOLVED Sprint 562** (124→0 errors, 22 files fixed) | Sprint 475/543 |
| ~~Route-level integration tests (10+ routes)~~ | ~~Requires dedicated multi-sprint effort~~ — **RESOLVED Sprint 562** (12 routes, 135 tests) | DEC 2026-03-19 F-003 |
| ~~Frontend component test coverage (25% → 60%+)~~ | ~~147/195 untested~~ — **RESOLVED Sprint 562** (45 new test files, 26.6%→42.8%) | DEC 2026-03-19 F-004 |
| ~~Going concern section in TB Diagnostic PDF~~ | ~~Missing from PDF export~~ — **RESOLVED Sprint 562** (section renderer + orchestrator wiring) | DEC 2026-03-19 F-010 |
| ~~Time-dependent test patterns → `freezegun`~~ | ~~Wall-clock assertions~~ — **RESOLVED Sprint 562** (14 methods across 3 files) | DEC 2026-03-19 F-013 |
| ~~Pre-existing test failures (3)~~ | ~~flux_analysis fixed by FIX-1B flux_engine.py Decimal handling; sampling_memo fixed by adding ISA 530 "accepted"/"cannot be accepted" language~~ — **RESOLVED** | FIX-1A audit 2026-03-20 |
| Rate limiter → Redis storage backend | In-memory counters reset on worker restart and are not shared across workers; requires Redis infrastructure | AUDIT-07 Phase 5 |

---

## Active Phase
> Sprints 478–497 archived to `tasks/archive/sprints-478-497-details.md`.
> Sprints 499–515 archived to `tasks/archive/sprints-499-515-details.md`.
> Sprints 516–526 archived to `tasks/archive/sprints-516-526-details.md`.
> Sprints 517–531 archived to `tasks/archive/sprints-517-531-details.md`.
> Sprints 532–536 archived to `tasks/archive/sprints-532-536-details.md`.
> Sprints 537–541 archived to `tasks/archive/sprints-537-541-details.md`.
> Sprints 542–546 archived to `tasks/archive/sprints-542-546-details.md`.
> Sprints 547–551 archived to `tasks/archive/sprints-547-551-details.md`.
> Sprints 552–556 archived to `tasks/archive/sprints-552-556-details.md`.
> Sprints 553–561 archived to `tasks/archive/sprints-553-561-details.md`.
> FIX-1A/1B, Sprint 562, FIX-2A/2B archived to `tasks/archive/fix-1-2-sprint562-details.md`.

### FIX-3: Anomaly Coverage Mapping (AUDIT-06 Phase 3)
- [x] Step 1: Create authoritative coverage map (`backend/tests/anomaly_framework/COVERAGE_MAP.md`)
- [x] Step 2: Expose `min_detectable_threshold` in anomaly registry via `ANOMALY_REGISTRY_META`
- [x] Step 3: Document duplicate_entry per-tool detection contract (`DUPLICATE_ENTRY_CONTRACT.md`)
- [x] Step 4: Add coverage map validation test (`test_coverage_map.py` — 2 tests)
- **Tests:** 10 passed (2 new + 8 existing), 0 regressions
- **Status:** COMPLETE

### FIX-4: Partial Systemic Bug Resolutions (AUDIT-06 Phase 4)
- [x] FIX 1: Risk tier label boundary validation + regression test (9 tests)
- [x] FIX 2: Widen narrow free-text columns in fixed asset memo tables (1.3→1.5 inches)
- [x] FIX 3: Document and guard ASC 250-10 YAML entries; add canary test (2 tests)
- [x] FIX 4: Render labeled empty state in drill-down instead of silent omission (4 tests)
- **Tests:** 15 new tests (9 + 2 + 4), 0 regressions
- **Status:** COMPLETE

### FIX-5: Brute Force Protection Hardening (AUDIT-07 Phase 4)
- [x] F4 (HIGH): Unified auth failure response — locked/invalid/nonexistent all return 401 with identical body; no lockout info in response
- [x] F3 (MEDIUM): Configurable lockout thresholds via `LOCKOUT_MAX_FAILED_ATTEMPTS` and `LOCKOUT_DURATION_MINUTES` env vars
- [x] F2 (MEDIUM): Per-IP sliding-window failure tracker — blocks IPs after 20 failures/15 min; configurable via `IP_FAILURE_THRESHOLD`/`IP_FAILURE_WINDOW_SECONDS`
- **Tests:** 128 passed (7 new: 3 integration + 6 per-IP unit − 2 removed lockout-response tests), 0 regressions
- **Status:** COMPLETE

### FIX-6: File Ingestion Abuse Surface (AUDIT-07 Phase 3)
- [x] Step 1 (HIGH): Move row-count gate before full parse — CSV streaming estimator + XLSX metadata check
- [x] Step 2 (MEDIUM): Server-side content sniffing for text-based upload formats
- [x] Step 3 (MEDIUM): Streaming body size limit regardless of Content-Length header
- [x] Step 4 (MEDIUM): Explicit data_only/keep_vba Excel load on main ingestion path
- **Tests:** 7,007 passed, 0 regressions (4 commits)
- **Status:** COMPLETE

### FIX-8A: Entitlement Enforcement — Incorrect Helper Invocation (AUDIT-08 Phase 2)
- [x] Step 1: Fix `/upload/bulk` entitlement check — corrected `(db, user.id)` → `(user, db)`; also fixed `check_upload_limit`
- [x] Step 2: Fix `/branding/*` entitlement check — corrected `(db, user.id)` → `(user, db)` in `_get_branding()`
- [x] Step 3: Fix `/export-sharing/create` — added `db` session to `check_export_sharing_access(user, db)`
- [x] Step 4: Fix `/admin/*` — added `db` session to `check_admin_dashboard_access(user, db)` in `_get_admin_org()`
- **Tests:** 7,007 passed, 0 regressions
- **Risk:** HIGH — subscription-status bypass / entitlement not enforced
- **Status:** COMPLETE

### FIX-8B: Org-Aware Export Access & Multi-Tenant Roadmap (AUDIT-08 Phase 1/3)
- [x] FIX 1: Verified — both generators already use `EngagementManager.get_engagement()` (org-aware via `_get_accessible_user_ids()`); no `Client.user_id ==` pattern exists
- [x] FIX 2: Verified — `engagements_exports.py` already returns 404 (not 400) on access failures
- [x] FIX 3: Created `docs/architecture/MULTI_TENANT_ROADMAP.md` — 5 sections covering current state, user-centric tables, migration path, regression tests, key invariants
- **Risk:** MEDIUM/LOW + documentation
- **Status:** COMPLETE

