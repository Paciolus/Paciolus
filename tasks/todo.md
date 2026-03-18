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

- [2026-03-07] fb8a1fa: accuracy remediation — test count, storage claims, performance copy (16 frontend files)
- [2026-02-28] e3d6c88: Sprint 481 — undocumented (retroactive entry per DEC F-019)

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Composite Risk Scoring | Requires ISA 315 inputs — auditor-input workflow needed | Phase XI |
| Management Letter Generator | **REJECTED** — ISA 265 boundary, auditor judgment | Phase X |
| Expense Allocation Testing | 2/5 market demand | Phase XII |
| Templates system | Needs user feedback | Phase XII |
| Related Party detection | Needs external APIs | Phase XII |
| Marketing pages SSG | **Not feasible** — CSP nonce (`await headers()` in root layout) forces dynamic rendering; Vercel edge caching provides near-static perf | Phase XXVII |
| Test file mypy — full cleanup | 804 errors across 135 files (expanded from 68); `python_version` updated to 3.12 in Sprint 543 | Sprint 475/543 |

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

### Sprint 557 — AUDIT-06 Billing Concurrency & Race Conditions Remediation
**Status:** COMPLETE
**Scope:** 4 fixes from AUDIT-06 Billing Concurrency and Race Conditions review

- [x] **FIX 1 (HIGH):** Seat mutation race condition — serialize with FOR UPDATE + Stripe idempotency keys
- [x] **FIX 2 (HIGH):** Entitlement state-model mismatch — derive entitlements from subscription status, not tier alone
- [x] **FIX 3 (MEDIUM):** APScheduler multi-worker duplication — DB-backed execution lock for all scheduled jobs
- [x] **FIX 4 (LOW):** Upload endpoint deduplication — SHA-256 dedup key to prevent duplicate submissions

**Review:**
- FIX 1: `seat_version` column added to `subscriptions` table. `add_seats()` and `remove_seats()` use `SELECT ... FOR UPDATE` for row-level locking plus Stripe idempotency keys (`seat-mutation-{sub_id}-v{version}`). On Stripe failure, DB rollback preserves version integrity.
- FIX 2: `get_effective_entitlements(user, db)` checks `Subscription.status` — PAST_DUE/CANCELED → free-tier. Applied to all 11 check functions in `entitlement_checks.py`, `enforce_tool_access` in `testing_route.py` (+ 4 route callers), `create_client` in `clients.py`, and `_resolve_org_subscription` for org-level checks. Graceful fallback when db is not a Session (unit test compatibility).
- FIX 3: `scheduler_locks` table + `with_scheduler_lock()` context manager. All 8 scheduled jobs (7 via `_run_cleanup_job` + 1 `_job_bulk_upload_cleanup` + watchdog) wrapped with DB lock. `reset_upload_quotas` converted to atomic `UPDATE ... SET uploads_used_current_period = 0 WHERE ...`. New `_job_expired_upload_dedup` cleanup job added.
- FIX 4: `upload_dedup` table with SHA-256-based dedup key (`{user_id}:{engagement_id}:{file_hash}:{endpoint}`). 5-minute TTL. Checked before analysis in `audit_trial_balance()`. Returns HTTP 409 on duplicate. Expired rows purged hourly by scheduler.
- Migrations: 3 Alembic migrations (c7d8e9f0a1b2 → d8e9f0a1b2c3 → e9f0a1b2c3d4), all chain from head correctly.
- Verification: 6,700 backend tests pass. 5 pre-existing failures (Sprint 553 SQLite schema + rate limit coverage).
- Files: `subscription_model.py`, `subscription_manager.py`, `entitlement_checks.py`, `entitlements.py`, `testing_route.py`, `cleanup_scheduler.py`, `audit_pipeline.py`, `clients.py`, `ar_aging.py`, `bank_reconciliation.py`, `sampling.py`, `three_way_match.py`, `database.py`, `env.py`, `scheduler_lock_model.py`, `upload_dedup_model.py`, 3 migrations, `conftest.py`

