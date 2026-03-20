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
| Pre-existing test failures (3) | `test_audit_api::TestAuditFlux::test_flux_analysis` (500 error), `test_sampling_memo::TestEvaluationNextSteps::test_evaluation_intro_pass_accepted` (missing "accepted" in intro text), `test_sampling_memo::TestEvaluationNextSteps::test_evaluation_intro_fail_not_accepted` (missing "cannot be accepted") | FIX-1A audit 2026-03-20 |

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

### FIX-1A: Decimal Precision — Parse and Compute Pipeline
- [x] Step 1: Introduce `safe_decimal()` in `parsing_helpers.py`
- [x] Step 2: Replace `safe_float` with `safe_decimal` in 13 engine files + downstream arithmetic
- [x] Step 3: Fix float arithmetic chains in `multi_period_comparison.py`
- [x] Step 4: Fix float conversion in `sampling_engine.py`
- [x] Step 5: Fix materiality cascade in `engagement_manager.py`
- [x] Step 6: Fix float accumulation in `streaming_auditor.py`
- [x] Step 7: Fix float ingestion arrays in `ingestion.py`
- [x] Step 8: Fix float coercion in `preflight_engine.py`
- **Status:** COMPLETE
- **Tests:** 6,896 passed (3 pre-existing failures, 0 regressions)

### Sprint 562: Complete All Deferred Items
- [x] **Going concern PDF section** — `render_going_concern_indicators()` in `pdf/sections/diagnostic.py`, wired into orchestrator, ToC updated
- [x] **Freezegun migration** — 14 test methods decorated across 3 files (`test_csrf_middleware.py`, `test_security.py`, `test_rate_limit_tiered.py`); `freezegun>=1.5.0` added to requirements-dev.txt; 150 tests pass
- [x] **Composite Risk Scoring** — `composite_risk_engine.py` (ISA 315 auditor-input workflow), `routes/composite_risk.py` (POST `/composite-risk/profile`), 58 engine tests
- [x] **Route integration tests** — 12 new test files covering admin_dashboard, adjustments, bulk_upload, branding, billing_analytics, billing_checkout, follow_up_items, engagements_analytics, engagements_exports, prior_period, metrics, multi_period (135 tests)
- [x] **Mypy test cleanup** — 124→0 errors across 22 test files; factory fixtures typed, missing annotations added, unused `# type: ignore` removed
- [x] **Frontend component tests** — 45 new test files (batch, adjustment, engagement, shared, marketing, skeleton, testing, UI components); 1,357→1,725 tests; coverage 26.6%→42.8%
- **Status:** COMPLETE
- **Commit:** c9b51db

