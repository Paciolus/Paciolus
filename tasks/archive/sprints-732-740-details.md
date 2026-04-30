# Sprints 732 / 739 / 740 — cleanup_scheduler stabilization

Archived 2026-04-29 as part of the todo.md "pending-only" cleanup. Sprint 738 stays in `tasks/todo.md` (still PENDING).

### Sprint 732: cleanup_scheduler recurring InternalError triage
**Status:** **STEPS 1-3 COMPLETE 2026-04-28 — Sprint 740 ships the structural fix; awaits next post-deploy cycle to surface the actual root psycopg2 class for Sprint 741.** Initial post-Sprint-737-deploy silence (13:00–16:08 UTC, ~3h) was deployment-churn artifact: each merged PR (#117 13:00, #120 13:47, #119 14:13, #121 15:08) reset the cleanup_scheduler's 60-min interval timer, and the first post-deploy cycle on Sprint 739's deploy at 15:08 UTC fired at 16:08 UTC and **hit the failure with the new `error_orig_fqn` field populated**. The verification-window approach paid off — silence was coincidental (deploy churn, not structural fix), pattern resumed once a deploy had a clean 60-min window. Sprint 737 was NOT the fix. Sprint 740 (immediately below) addresses the cascade-masking that hid the real root class; Sprint 741 will address whatever Sprint 740 unmasks.

**Leaf class identified (16:08:55 UTC `reset_upload_quotas` + 16:09:28 UTC `dunning_grace_period`):**
```
error_type_fqn:    sqlalchemy.exc.InternalError    (SQLAlchemy wrapper)
error_cause_fqn:   psycopg2.errors.InFailedSqlTransaction
error_orig_fqn:    psycopg2.errors.InFailedSqlTransaction
error_orig_pgcode: 25P02                            ← SQLSTATE: in_failed_sql_transaction
```

**SQLSTATE 25P02** ("current transaction is aborted, commands ignored until end of transaction block") means a prior statement in the cleanup job's session/transaction failed, and subsequent statements are rejected until rollback. **The real failing statement is masked by this cascade** — likely the lock-release `DELETE FROM scheduler_locks` in `with_scheduler_lock`'s finally block (`backend/cleanup_scheduler.py:154-157`) firing on a session whose actual cleanup work already failed silently. Step 3's fix needs to rollback the session BEFORE the lock release tries to use it.
**Priority:** P2 → P1 once Phase 4.1 lands (silent recurring failure on `dunning_grace_period` blocks delinquent-subscription auto-cancellation, which becomes customer-visible the moment real money flows).
**Source:** Sprint 715 Render-log sweep 2026-04-26.

**Observed signal (2026-04-25 to 2026-04-26 in Render logs, srv-d6ie9l56ubrc73c7eq2g):**
```
ERROR cleanup_scheduler  Cleanup job failed: {... 'job_name': 'reset_upload_quotas',  'error': 'InternalError: scheduled cleanup failed'}
ERROR cleanup_scheduler  Cleanup job failed: {... 'job_name': 'dunning_grace_period', 'error': 'InternalError: scheduled cleanup failed'}
```
Both jobs fire roughly every hour; each invocation completes in 30–80ms with `records_processed: 0` and the same `InternalError`. **Diagnosis (2026-04-27):** the bare class name `InternalError` is ambiguous — Python's `builtins`, `sqlalchemy.exc`, and `psycopg2` all expose it. `cleanup_scheduler._run_cleanup_job` was using `sanitize_exception(exc, context="scheduled cleanup")` (correct PII-safe choice) but that strips both the message and the module path, leaving the log fingerprint useless for triage.

**Step 1 — Observability fix (DONE):**
- `backend/cleanup_scheduler.py::CleanupTelemetry` — added `error_type_fqn` field (e.g. `sqlalchemy.exc.InternalError`, `psycopg2.errors.SerializationFailure`). Module-path metadata only; no PII risk.
- `_run_cleanup_job` populates `error_type_fqn` from `caught_exc` so the structured log carries the disambiguating fingerprint without leaking exception messages.
- `tests/test_cleanup_scheduler.py::test_failure_log_includes_traceback_exc_info` extended to assert `error_type_fqn` appears with the FQN (`builtins.RuntimeError` for the test's deliberate `RuntimeError`). 28/28 cleanup-scheduler tests passing.

**Step 2 — Root cause investigation (DONE 2026-04-28):**
- Sub-step 2a (DONE 2026-04-27 17:14 UTC): Pulled Render logs filtered to `error_type_fqn` after Step 1's deploy (`dep-d7nom57avr4c73fgn9ig`, live 16:14:41 UTC). **Result: `sqlalchemy.exc.InternalError` on both jobs** (`reset_upload_quotas` + `dunning_grace_period`, both at 17:14 UTC). This is the SQLAlchemy wrapper — the leaf cause sits one level deeper inside `caught_exc.__cause__` / `caught_exc.orig`.
- Sub-step 2b (DONE 2026-04-27 via PR #117): Extended cleanup_scheduler observability to also capture `__cause__` (raise-from chain), `.orig` (SQLAlchemy DBAPIError attribute holding the wrapped psycopg2 exception), and `orig.pgcode` (Postgres SQLSTATE — standardized 5-char code, no PII). 29/29 cleanup-scheduler tests passing.
- **Sub-step 2c (DONE 2026-04-28 16:08 UTC): leaf class identified via the new fields.** First post-deploy cycle on Sprint 739's deploy (15:08 UTC) fired at 16:08 UTC for `reset_upload_quotas` and 16:09 UTC for `dunning_grace_period` — both with full new-field population. Leaf: `psycopg2.errors.InFailedSqlTransaction` (SQLSTATE 25P02). The intervening 13:00–16:08 UTC silence was deploy-churn artifact (4 successive PR merges each reset the cleanup_scheduler's 60-min interval timer; first uninterrupted 60-min window was Sprint 739's deploy → 16:08 cycle).
- Sub-step 2d (Sentry cross-check — NO LONGER NEEDED): root cause now identified directly from Render logs via the Sprint 732 step 2b new fields. Sentry tracebacks for past 48h would corroborate if needed, but the SQLSTATE + class-name pair is unambiguous.

**Step 3 — Fix + coverage (REQUIRED, file as Sprint 740):**

The InFailedSqlTransaction error is a **cascade symptom**, not the root failure. SQLSTATE 25P02 means "the prior statement in this transaction failed; subsequent statements are rejected." The visible failure is whatever statement fired AFTER the actual root failure on the same session — most likely the lock-release `DELETE FROM scheduler_locks` in `backend/cleanup_scheduler.py::with_scheduler_lock`'s finally block (line 154–157). The real first failure (in `cleanup_func` body) is masked.

Sprint 740 fix outline:
1. **Save & rollback:** wrap the `cleanup_func(db)` invocation inside `_run_cleanup_job` in its own `try/except` that calls `db.rollback()` on any exception BEFORE the `with_scheduler_lock` finally block runs. That way the lock release runs on a clean session, the InFailedSqlTransaction cascade is broken, and the original exception (with its real class + traceback) surfaces in the log + Sentry instead of the generic 25P02.
2. **Or:** use a separate `SessionLocal()` for the lock acquire/release vs. the cleanup work. Two sessions = lock-release session is unaffected by cleanup-session aborts. Slightly heavier infra change but eliminates the failure mode entirely.
3. **Either way, add an integration test** (`tests/test_cleanup_scheduler_session_isolation.py` or extend the existing file) that injects a deliberate IntegrityError mid-cleanup and asserts: (a) the original exception class surfaces in logs (not InFailedSqlTransaction), (b) the lock is still released, (c) subsequent cleanup cycles run normally.
4. **Verify dunning escalation end-to-end** on a staging-equivalent fixture once the cascade is fixed — was originally blocked by the masked failure; now actionable.

**Effort estimate:** Step 3 work as Sprint 740 = 0.5–1 sprint. Total Sprint 732 = ~1 sprint (Steps 1–2 done) + Sprint 740's 0.5–1 sprint for the structural fix.

**Pre-requisites for Sprint 740:** None — observability is already shipped, root cause is named, fix path is mechanical.

---

### Sprint 739: Remove orphaned `bulk_upload_cleanup` job (post-Sprint-720 dead code)
**Status:** COMPLETE 2026-04-28. Deleted `_job_bulk_upload_cleanup` (~22 lines) + its scheduler registration (~7 lines) from `backend/cleanup_scheduler.py`. 29/29 cleanup_scheduler tests passing post-deletion. Production verification post-deploy: `Bulk upload cleanup failed: ImportError` log pattern should drop to zero firings.
**Priority:** P3 (production noise; not customer-facing). Surfaced during Sprint 732 Step 2c log analysis 2026-04-28.
**Source:** Sprint 720's `bulk_job_store` refactor removed `_evict_stale_jobs` from `routes/bulk_upload.py` (the new store handles eviction internally — `routes/bulk_upload.py:74` comment: *"bulk_job_store handles eviction itself (Redis TTL or in-memory LRU+age cap); no explicit _evict_stale_jobs call needed"*). The cleanup_scheduler call site at `cleanup_scheduler.py:403` was orphaned with `from routes.bulk_upload import _evict_stale_jobs`, raising `ImportError` on every scheduled run since Sprint 720's deploy. Render logs confirm firings going back at least 11:54 UTC 2026-04-28 today (and through Sprint 732 Step 2c's window).

**What landed:**
- Deleted `_job_bulk_upload_cleanup` function from `backend/cleanup_scheduler.py:390-411`.
- Removed scheduler registration block at `cleanup_scheduler.py:636-642` (the `_scheduler.add_job(_job_bulk_upload_cleanup, ...)` entry).
- Net: ~30 lines removed; no replacement needed (per Sprint 720's own design).

**Why it took 8 sprints to surface:** the failure log message starts with "Bulk upload cleanup failed", not "Cleanup job failed" — Sprint 732's investigation queries filtered for the latter. Sprint 732 Step 2c's broader cleanup_scheduler-logger query caught it.

**Out of scope:**
- No regression test added — the absence of the schedule registration *is* the test. Adding `_scheduler.add_job(_job_bulk_upload_cleanup, ...)` back would fail because the function doesn't exist.

**Verification:**
- 29/29 `test_cleanup_scheduler.py` tests passing.
- Production deploy after Sprint 739 lands: zero `Bulk upload cleanup failed` log entries on the next 30-min cycle window.

---

### Sprint 740: rollback before lock release in `_run_cleanup_job` (Sprint 732 Step 3 fix)
**Status:** COMPLETE 2026-04-28. 3-line fix added to `_run_cleanup_job` + 1 new contract test pinning the rollback-ordering invariant. 30/30 cleanup_scheduler tests passing locally. Ships the structural fix Sprint 732 Step 3 was waiting on.
**Priority:** P2 (cleanup-scheduler is failing every ~60 min in production with masked-symptom 25P02; Sprint 740 unmasks the real root cause for the next investigation sprint).
**Source:** Sprint 732 Step 2c (2026-04-28 16:08 UTC) identified the leaf class as `psycopg2.errors.InFailedSqlTransaction` (SQLSTATE 25P02). Investigation revealed this was a cascade symptom — the cleanup_func body fails first (real root, masked), session enters aborted state, `with_scheduler_lock`'s finally executes `DELETE FROM scheduler_locks` on the same aborted session, that DELETE fails with 25P02, and the 25P02 propagates out as the visible exception.

**The fix:** wrap `cleanup_func(db)` in a try/except inside the `with with_scheduler_lock(...)` block. On any exception, call `db.rollback()` BEFORE re-raising. The lock-release DELETE in `with_scheduler_lock`'s finally then runs on a clean session, the DELETE succeeds, and the original `cleanup_func` exception class propagates out unmasked.

**Side benefit beyond stability:** Sprint 732 step 2b's leaf-class observability fields (`error_orig_fqn`, `error_cause_fqn`, `error_orig_pgcode`) now capture the ACTUAL root psycopg2 class instead of the cascade symptom. Sprint 740's first post-deploy cleanup cycle will reveal what's truly failing inside the cleanup_func body — the data Sprint 732 was originally chasing.

**What landed:**
- `backend/cleanup_scheduler.py::_run_cleanup_job` — inner try/except around `cleanup_func(db)` invocation; rollback-then-raise on exception. ~10 lines added (mostly comment explaining the cascade and why this ordering matters).
- `backend/tests/test_cleanup_scheduler.py::test_session_rollback_runs_before_lock_release_on_cleanup_failure` — new contract test mocks the session and asserts the FIRST rollback call's index < the DELETE FROM scheduler_locks call's index. A regression that moves rollback after the lock release fails this test loudly.
- Existing `test_session_rollback_before_close_on_failure` updated: it asserted `rollback.assert_called_once()`; Sprint 740 makes rollback called twice (Sprint 740's inner + Sprint 711's outer-finally). Test now asserts `call_count >= 1` — the original "rollback before close" semantic intent is preserved.

**Verification:**
- 30/30 cleanup_scheduler tests passing locally.
- Post-Sprint-740 production deploy + 1h: pull `error_orig_fqn` from the next cleanup cycle's failure log. Expected: a non-cascade psycopg2 class (likely `psycopg2.errors.SerializationFailure`, `psycopg2.OperationalError` with pgcode `08006` matching Sentry's SSLEOFError signal, or something genuinely surprising). That class names the real root for **Sprint 741** — the actual structural fix to the cleanup_func body's failing statement.

**Out of scope:**
- The actual root-cause fix for whatever cleanup_func is doing wrong — that's Sprint 741, contingent on Sprint 740's first post-deploy log read.
- Approach 2 from the close-out doc (separate session for lock vs cleanup) — not adopted; Approach 1 (inner rollback) is sufficient and 1/3 the diff.
