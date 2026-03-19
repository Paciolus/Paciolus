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

### Sprint 559 — AUDIT-08 Stripe Event Coverage Completeness Remediation
**Status:** COMPLETE
**Scope:** 6 fixes from AUDIT-08 Stripe Event Coverage Completeness review

- [x] **FIX 1 (HIGH):** Extend SubscriptionStatus enum (4→8 values, 1:1 mapping), fail closed to PAUSED on unknown status, gate tier writes to entitled statuses only
- [x] **FIX 2 (CRITICAL):** Revoke paid access on invoice.payment_failed (tier→FREE + org downgrade), fix handle_subscription_updated downgrade condition to include all non-entitled statuses
- [x] **FIX 3 (HIGH):** Add customer.subscription.created handler for non-checkout subscription flows
- [x] **FIX 4 (HIGH):** Add invoice.payment_succeeded handler to restore access from non-entitled states
- [x] **FIX 5 (HIGH+MEDIUM):** Add charge.dispute.created/closed handlers with access suspension/restoration policy
- [x] **FIX 6 (MEDIUM):** Add invoice.created handler for lifecycle observability (analytics only)

**Review:**
- FIX 1: `SubscriptionStatus` extended to 8 values (active, past_due, canceled, trialing, incomplete, incomplete_expired, unpaid, paused). `_STATUS_MAP` now 1:1 (no collapsing). Unknown status → PAUSED with error log. `_ENTITLED_STATUSES = {ACTIVE, TRIALING}` gates `user.tier` writes in `sync_subscription_from_stripe`. Alembic migration f0a1b2c3d4e5 extends both `subscriptionstatus` and `billingeventtype` PostgreSQL enum types.
- FIX 2: `handle_invoice_payment_failed` now sets `user.tier = FREE` + calls `_downgrade_org_members_to_free`. `handle_subscription_updated` downgrade condition expanded from `("canceled", "unpaid")` to include `past_due`, `incomplete`, `incomplete_expired`, `paused`.
- FIX 3: `handle_subscription_created` resolves user, calls `sync_subscription_from_stripe`, records analytics only if first to create local row (prevents duplicate events with checkout.session.completed).
- FIX 4: `handle_invoice_payment_succeeded` restores from PAST_DUE/INCOMPLETE/UNPAID → ACTIVE with plan-appropriate tier. Idempotent: no-op if already ACTIVE.
- FIX 5: `handle_dispute_created` suspends access (PAUSED + FREE + org downgrade). `handle_dispute_closed` restores on `won`, cancels on `lost`, leaves suspended for other statuses. Policy documented in handler docstrings.
- FIX 6: `handle_invoice_created` records analytics event with invoice_id, amount_due, billing_reason. No status/tier changes.
- `BillingEventType` extended with 6 new values: payment_succeeded, invoice_created, dispute_created, dispute_resolved_won, dispute_resolved_lost, dispute_closed_other.
- `WEBHOOK_HANDLERS` now has 11 entries (6 existing + 5 new).
- Verification: 6,701 backend tests pass. 5 pre-existing failures (Sprint 558 backlog).
- Files: `subscription_model.py`, `billing/subscription_manager.py`, `billing/webhook_handler.py`, 1 Alembic migration, test assertion updates in 4 test files.

### Sprint 558 — Pre-existing Test Failures Remediation (Sprint 553 Debt)
**Status:** COMPLETE
**Scope:** Fix 5 pre-existing test failures introduced by Sprint 553 (AUDIT-02) on SQLite

- [x] **SQLite schema mismatch:** `refresh_tokens` table missing `last_used_at`, `user_agent`, `ip_address` columns — fixed by column patching in `init_db()` + `_init_app_db()` conftest fixture
  - `test_email_verification.py::TestRegistrationWithDisposableEmail::test_allows_legitimate_email_registration`
  - `test_security.py::TestAccountLockoutIntegration::test_failed_login_returns_lockout_info`
  - `test_pdf_upload_integration.py::TestPdfParseDispatch::test_pdf_magic_byte_guard`
  - `test_transport_hardening.py::TestRequestIdMiddleware::test_no_header_generates_id`
- [x] **Rate limit coverage gap:** `@limiter.limit(RATE_LIMIT_AUTH)` already present on both session endpoints
  - `test_rate_limit_coverage.py::TestMutatingEndpointCoverage::test_no_unprotected_mutating_endpoints`

### Sprint 560 — Nightly Report 2026-03-19 Remediation
**Status:** COMPLETE
**Scope:** 5 report bugs + 1 security update from overnight brief

- [x] **BUG-001 (Procedure Rotation):** Added `SUGGESTED_PROCEDURES_ALT` alternate pool + `rotation_index` param to `get_tb_suggested_procedure()`. Caller in `diagnostic.py` passes `idx`.
- [x] **BUG-002 (Hardcoded Risk Labels):** All 9 consumers of `RISK_TIER_DISPLAY` now append numeric score: `"MODERATE (18/100)"`. Added `format_risk_tier_label()` helper in `memo_base.py`.
- [x] **BUG-003 (PDF Cell Overflow):** Results table in `build_results_summary_section()` now wraps all cell data in `Paragraph` objects for word-wrapping.
- [x] **BUG-006 (Identical Data Quality):** `data_quality_score` in `get_benchmark_set()` now computed from ratio coverage (50%) + percentile completeness (50%) instead of hardcoded 0.85.
- [x] **BUG-007 (Empty Drill-Down):** Generic detail table fallback in `fixed_asset`, `payroll`, and `revenue` memo generators — renders proper 4-column table (ID, Name/Desc, Issue, Amount) instead of empty bullet points.
- [x] **Security:** Next.js 16.1.7 → 16.2.0 (security-flagged minor update)

**Review:**
- All 68 benchmark tests pass. All 134 diagnostic tests pass. All 867 memo tests pass. All 83 report regression tests pass. All 206 anomaly/engagement/bank-rec tests pass. 1,426 frontend tests pass. Frontend build succeeds.
- Files: `benchmark_engine.py`, `shared/memo_base.py`, `shared/tb_diagnostic_constants.py`, `pdf/sections/diagnostic.py`, `anomaly_summary_generator.py`, `bank_reconciliation_memo_generator.py`, `engagement_dashboard_memo.py`, `multi_period_memo_generator.py`, `three_way_match_memo_generator.py`, `fixed_asset_testing_memo_generator.py`, `payroll_testing_memo_generator.py`, `revenue_testing_memo_generator.py`, `frontend/package.json`, `frontend/package-lock.json`

