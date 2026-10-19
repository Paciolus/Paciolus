# Session State

_Updated at the end of every Claude Code session. Overwrite the previous state — this is not a history log._

## Last Session

**Date:** 2026-10-19
**Branch:** `sprint-774-rate-limit-outage-resilience` (off `main` @ `51906004`)

**Context:** First session after ~5.5 months of repo dormancy (previous commit 2026-05-01). Started as a status review; became a P0 incident response.

### 🔴 Production was DOWN and is now RESTORED

Every backend endpoint had been returning HTTP 500 since roughly 2026-05. Two independent faults, both fixed:

1. **`AUDIT_CHAIN_SECRET_KEY` was never set on Render.** Sprint 768 turned the silent dev fallback into a production hard-fail (correctly), but the variable was never added, so the Sprint 768 deploy (`c58cbbb5`) exited 1 at startup. Render kept the prior image serving, making the failure invisible — **Sprint 768's P1 security fixes had never reached production.** Now set; deploy `dep-dbb2glcs728c73a67s5g` is live on `51906004`.
2. **The Upstash Redis host stopped resolving.** Every rate-limited route (i.e. the whole API, health probes included) raised out of slowapi's limit check. Replaced with Render Key Value `paciolus-ratelimit` (`red-dbb2gdqjnfac739l4p5g`, free, virginia, same region as the service) and repointed `REDIS_URL` at its internal URL.

**Production verified:** all four health probes 200, `/health/redis` connected (5.76ms), DB 9.96ms, and a full auth round-trip green against live prod (register → `/auth/me` → login → wrong-password 401 → uppercase-email login → logout → post-logout 401).

### Sprint 774 — code work (COMPLETE, uncommitted at time of writing)

So a dead cache can never take the API down again:

- `in_memory_fallback_enabled=True` on the Limiter — storage errors degrade to in-process counters (same limit values, still enforced) and self-heal when Redis returns.
- New `RATE_LIMIT_STORAGE_FAILURE_POLICY` (`degrade` default | `fail_closed`), split out from `RATE_LIMIT_STRICT_MODE` which keeps its original "Redis must be configured" meaning.
- **Found: the old fail-closed guarantee never worked.** `limits`' `Storage.check()` returns `False` instead of raising; the code only caught exceptions. The Sprint 696 tests passed only because they mocked `check()` to raise — which real `RedisStorage` never does.
- **Found: `scripts/smoke_test_render.sh` could never pass.** It used `@paciolus.test`, which `email-validator` rejects as a reserved TLD, so `/auth/register` always 422'd. Fixed, plus the stale Sprint 768 `access_token` assertions.
- `/health/ready` now reports a `rate_limit_storage` dependency and `status: "degraded"` (still 200).
- 13 new tests; 4 pre-existing tests updated to the new posture.

## Current Environment State

**App status:** Working — production live and verified.
**Last passing smoke test:** 2026-10-19 (14/14 prod auth checks).
**Test counts:** 8,685 backend + 2,013 frontend as of the 2026-10-14 nightly; Sprint 774 adds 13 backend tests.

**Open blockers:**
- **Nothing alerted for 5.5 months.** Filed as Sprint 775 (external uptime monitoring + deploy-failure alerting). Highest-value follow-up.
- 1 known-failing backend test: `test_inventory_testing.py::TestCompositeScore::test_clean_data_low_score` — a **wall-clock time bomb, not a regression.** Its fixture hardcodes `Last Movement Date` values in late 2025 which crossed the slow-moving threshold around 2026-05-31. Needs frozen or relative dates.
- **Dependency drift is now large:** 70 backend + 25 frontend outdated; 7 security-relevant (`PyJWT` flagged PAST DEADLINE, plus `cryptography` 46→50, `stripe` 15→16, `fastapi`, `SQLAlchemy`, `next`, `react`).
- **Scheduled GitHub Actions are disabled** — GitHub switches cron workflows off after ~60 days of repo inactivity; last scheduled run was ~2026-09-01. `dependency-compliance` and `Backup Integrity Check (Monthly)` were also failing before they stopped.
- 25 open PRs: 10 real work (#134, #137–#145), 15 Dependabot. None merged since #129; all ~6 months behind `main`.
- Phase 4.1 Stripe cutover, 4.2 legal sign-off, 4.3 custom domain (`api.paciolus.com` still 404s) — all still CEO-gated.

## Next Priority

1. Commit + PR Sprint 774, and **verify the live deploy SHA equals `main` afterwards** — the lesson of this session is that "merged" is not "deployed."
2. Sprint 775 — external uptime monitoring. Alert on `/health/ready` returning `status != "healthy"`, not just on non-200.
3. Security dependency updates, `PyJWT` first.
4. Archive Active Phase (now at 4 completed sprints; the commit-msg hook rejects at 5).

## Recent Git Context

```
90740910 fix: nightly audit artifacts (2026-04-30 + 2026-05-01) + tmp_report cleanup
a1449c41 Sprint 762: flux_expectations memo PDF contract test (close 17/18 → 18/18)
42cedfbf Sprint 773c: hoist sort comparator + row motion literals
51906004 Merge pull request #129 (main HEAD — what production now runs)
c58cbbb5 Merge pull request #128 (Sprint 768 — the deploy that failed on 2026-04-30)
```
