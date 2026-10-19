# Session State

_Updated at the end of every Claude Code session. Overwrite the previous state — this is not a history log._

## Last Session

**Date:** 2026-10-19
**Branch:** `sprint-774-rate-limit-outage-resilience` — 5 commits, based cleanly on `main` (`51906004`), **not yet pushed**.

**Context:** First session after ~5.5 months of repo dormancy (previous commit 2026-05-01). Began as a status review, became a P0 incident response.

### 🔴 Production was DOWN and is now RESTORED

Every backend endpoint had been returning HTTP 500 since roughly 2026-05. Two independent faults, both fixed in production:

1. **`AUDIT_CHAIN_SECRET_KEY` was never set on Render.** Sprint 768 correctly promoted the silent dev fallback to a production hard-fail, but the variable was never added, so the Sprint 768 deploy (`c58cbbb5`) exited 1 at startup. Render kept the prior image serving, so the failure was invisible — **Sprint 768's P1 security fixes had never reached production.** PR #129, merged 80 minutes later, never deployed at all: its files were outside Render's `backend` rootDir, so the commit was ignored.
2. **The Upstash Redis host stopped resolving.** Every rate-limited route (the whole API, health probes included) raised out of slowapi's limit check.

**Production actions taken:** set `AUDIT_CHAIN_SECRET_KEY` (fresh 64-hex key; safe because `verify_audit_chain` falls back to `JWT_SECRET_KEY` for pre-rotation records); provisioned Render Key Value `paciolus-ratelimit` (`red-dbb2gdqjnfac739l4p5g`, free, **virginia** — same region, so no cross-provider DNS dependency) and repointed `REDIS_URL` at its internal URL. Deploy `dep-dbb2glcs728c73a67s5g` is live on `51906004`.

**Verified against live prod:** all four health probes 200, `/health/redis` connected, DB ~9.6ms, and a full auth round-trip (register → `/auth/me` → login → wrong-password 401 → uppercase-email login → logout → post-logout 401).

### Commits on the branch

| Commit | What |
|---|---|
| `8601c4ef` | **Sprint 774** — rate-limit storage outage resilience |
| `acb00510` | inventory fixture date time-bomb (nightly RED since 2026-05-31) |
| `f3d5ae46` | nightly audit artifacts — 109-day backlog (795 files) |
| `3b7fe76e` | clear all six red CVE/dependency CI gates (backend + frontend) |
| `edfceef3` | sync `next-env.d.ts` for the Next.js 16.4.2 upgrade |

### Four latent bugs found and fixed

1. **The fail-closed rate-limit guarantee never worked.** `limits`' `Storage.check()` returns `False` instead of raising; the code only caught exceptions, so a dead backend was silently treated as healthy at boot. The Sprint 696 tests passed only because they mocked `check()` to raise — which real `RedisStorage` never does. The tests validated a false model of the library.
2. **`scripts/smoke_test_render.sh` could never pass.** It registered `@paciolus.test`, which `email-validator` rejects as a special-use TLD, so `/auth/register` always 422'd. The post-deploy verification gate had been non-functional. Also fixed its stale Sprint 768 `access_token` assertions (now sends `X-Token-Response: bearer`).
3. **The inventory test was a wall-clock time bomb**, not a regression — fixture dates hardcoded in late 2025 crossed the 180-day slow-moving threshold on 2026-05-31. Now relative via `_days_ago(n)`. The test built to catch exactly this (`test_recent_movement_no_flags`) never asserted `entries_flagged == 0` despite its name; it does now.
4. **All 13 non-dependabot PRs were BLOCKED by six failing CVE/audit jobs**, not by merge conflicts — all 25 open PRs report `MERGEABLE`. Backend tests, mypy, ruff, the accounting-policy gate and the secrets scan were all green on PR #145; only the audit jobs were red. Both backend and frontend CVEs are now cleared, so those gates should pass.

## Current Environment State

**App status:** Working — production live and verified.
**Backend tests:** **8,700 collected, 8,700 passed, 0 failed** (14m24s, `backend/venv` — the CI-representative env, with the new pins). `main` collects 8,685 with 1 failing, so this branch is +15 tests and removes the last red test.
**Frontend:** 207 suites / 2,013 tests / 5 snapshots, 0 failures; `tsc --noEmit` exit 0; `npm run build` clean with every route `ƒ (Dynamic)` and `ƒ Proxy (Middleware)` active (nonce-based CSP contract intact across the Next.js bump).
**Dependency CVEs:** backend `pip-audit` no longer flags pyjwt or python-multipart; frontend production vulnerabilities 22 → **0**.

**Note on environments:** `backend/venv` (what the nightly cron and I used) and system Python 3.12 had drifted apart, and neither matched `requirements.txt`. The nightly runs `backend\venv\Scripts\python.exe`. Both now carry the new pins.

**Open blockers:**
- **Branch is unpushed.** Production is restored but still runs `51906004`, so the Sprint 774 resilience fix itself is **not yet deployed**. Needs push → PR → merge → then verify the live deploy SHA equals `main`.
- **Nothing alerted for 5.5 months.** Filed as **Sprint 775** (external uptime monitoring + deploy-failure alerting). Highest-value follow-up. Alert on `/health/ready` returning `status != "healthy"`, not just on non-200.
- **Scheduled GitHub Actions are disabled** — GitHub switches cron workflows off after ~60 days of repo inactivity; last scheduled run ~2026-09-01. Re-enabling needs a repo-settings action.
- **Dependency pinning strategy unresolved** — filed as **Sprint 777**. The only two CVE-flagged packages were the only two with exact `==` pins; everything else uses `>=` floors and self-heals. This also changes how Sprint 761 should pin `cryptography`.
- 21 dev-only npm advisories remain (babel-jest chain); they don't gate CI (`--omit=dev`) and clearing them needs `npm audit fix --force`.
- 25 open PRs: 10 real work (#134, #137–#145), 15 Dependabot. All `MERGEABLE`; the 12 older Dependabot ones are `BEHIND` and need updating.
- Phase 4.1 Stripe cutover, 4.2 legal sign-off, 4.3 custom domain (`api.paciolus.com` still 404s) — all still CEO-gated.

## Next Priority

1. **Push the branch, open a PR, merge — then confirm the live deploy SHA equals `main`.** The lesson of this session is that "merged" is not "deployed."
2. **Sprint 775** — external uptime monitoring + deploy-failure alerting.
3. Merge **PR #145** (2 lines, qa_warden timeout). Only 43 of 109 dormant nights produced a qa_warden sentinel because the orchestrator timeout sat below the ~715–780s suite runtime — so the one agent that would have reported a red suite was the one most likely to time out.
4. **Sprint 777** — settle the pinning rule before Sprint 761.
5. Archive Active Phase when it next reaches 5 completed sprints (`sh scripts/archive_sprints.sh`; the commit-msg hook rejects at 5).

## Recent Git Context

```
edfceef3 fix: sync next-env.d.ts for the Next.js 16.4.2 upgrade
3b7fe76e fix: clear all six red CVE/dependency CI gates (backend + frontend)
f3d5ae46 fix: nightly audit artifacts — 109-day backlog (2026-05-02 to 2026-10-19)
acb00510 fix: inventory fixture date time-bomb (nightly RED since 2026-05-31)
8601c4ef Sprint 774: rate-limit storage outage resilience (P0 production restore)
51906004 Merge pull request #129  (main — what production currently runs)
```
