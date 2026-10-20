# Session State

_Updated at the end of every Claude Code session. Overwrite the previous state — this is not a history log._

## Last Session

**Date:** 2026-10-19
**Branch:** merged. PR **#165** landed on `main` as `54f1963d` and **is deployed** (Render `dep-dbb4feavcj2c738cga90`, status `live`). 9 commits.

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
4. **All 13 non-dependabot PRs were BLOCKED by six failing CVE/audit jobs**, not by merge conflicts — all 25 open PRs reported `MERGEABLE` *on 2026-10-19* (no longer true; see Open blockers). Backend tests, mypy, ruff, the accounting-policy gate and the secrets scan were all green on PR #145; only the audit jobs were red. Both backend and frontend CVEs are now cleared, so those gates should pass.

## Current Environment State

**App status:** Working — production live and verified.
**Backend tests:** **8,700 collected, 8,700 passed, 0 failed** (14m24s, `backend/venv`). Re-confirmed by the 2026-10-20 nightly: 8,700 passed / 0 failed, coverage 93.34%.
> **Correction (2026-10-20):** `backend/venv` is **not** "the CI-representative env, with the new pins". It holds `fastapi` 0.136.0 and `stripe` 15.0.1 against pins of `==0.136.1` / `==15.1.0`, and sits at the literal `>=` floor values that CI and the production Docker build resolve past on every fresh install. The two exact pins bumped on 10-19 (PyJWT, python-multipart) did land in it; the rest did not. CI is the authority and is green. **Resolved 2026-10-20 by Sprint 786a:** the venv now matches a fresh resolve, so it genuinely is CI-representative, and `ci.yml` records the resolution as a build artifact. The reconcile also showed that the `>=` floors have already shipped three unreviewed majors to production — `cryptography` 46→50, `pillow` 12→13, `redis` 7→8 — which is the risk Sprint 777 documented, now realised.
**Frontend:** 207 suites / 2,013 tests / 5 snapshots, 0 failures; `tsc --noEmit` exit 0; `npm run build` clean with every route `ƒ (Dynamic)` and `ƒ Proxy (Middleware)` active (nonce-based CSP contract intact across the Next.js bump).
**Dependency CVEs:** backend `pip-audit` no longer flags pyjwt or python-multipart; frontend production vulnerabilities 22 → **0**.

**Note on environments:** `backend/venv` (what the nightly cron uses) and system Python 3.12 had drifted apart, and neither matched `requirements.txt`. The nightly runs `backend/venv/Scripts/python.exe`. **Still true as of 2026-10-20** — see the correction above; only the two 10-19 security pins were reconciled.

**Open blockers:**
- ~~Branch unpushed / resilience fix undeployed~~ — **RESOLVED.** Merged and verified live (see above).
- **Nothing alerted for 5.5 months.** Sprint 775's in-repo half is **done and CI-verified**; an **external** monitor is still required (see Next Priority).
- ~~Scheduled GitHub Actions disabled~~ — **RESOLVED.** All five workflows re-enabled 2026-10-19 via the Actions API. But see Sprint 778: two of them cannot pass as written.
- ~~Dependency pinning strategy unresolved~~ — **RESOLVED.** Sprint 777 chose option 3 (explicit split), rule written into `backend/requirements.txt`. It explicitly **rejects** Sprint 761's premise: `cryptography` stays a floor.
- 21 dev-only npm advisories remain (babel-jest chain); they don't gate CI (`--omit=dev`) and clearing them needs `npm audit fix --force`.
- **25 open PRs, and the 9 real-work ones now all CONFLICT** (#134, #137–#144 report `DIRTY`/`CONFLICTING` as of 2026-10-20 — the 10-19/20 merges rewrote `tasks/todo.md` wholesale). They were `MERGEABLE` on 10-19; the red CVE gates that blocked them are fixed, so the only thing left between them and `main` is a rebase. Seven finished sprints are stranded. Filed as **Sprint 785**. The 15 Dependabot PRs are mostly superseded by newer releases.
- Phase 4.1 Stripe cutover, 4.2 legal sign-off, 4.3 custom domain (`api.paciolus.com` still 404s) — all still CEO-gated.

## Merge + deploy verification (2026-10-19)

PR #165 merged after **all 24 CI checks passed, 0 failures** — including the three matrices that cannot be reproduced locally (Python 3.11, PostgreSQL 15, Playwright E2E) and all four CVE/audit gates.

Merged with `--admin`. Branch protection on `main` requires 1 approving review, and GitHub blocks self-approval of your own PR, so that requirement is unsatisfiable for a solo developer; `enforce_admins` is `false`, so admin merge is the available path. **CI was green first** — the bypass covered only the review requirement, not the checks.

**"Merged" was then actually verified as "deployed"** — the explicit lesson of this session:
- Render auto-deploy `dep-dbb4feavcj2c738cga90` reached status `live`.
- Live deploy SHA `54f1963d` **==** `origin/main`.
- `/health/ready` now reports the new `rate_limit_storage` dependency (`configured_backend: redis`, `active_backend: redis`, `degraded: false`, `reachable_at_boot: true`) — proof Sprint 774's code is genuinely running, not merely merged.
- Post-deploy sanity: `/auth/csrf` unauth 401, bad-credential login 401, `/health/live` 200, `/health/redis` 200, `paciolus.com` 200.

Note: a GitHub Actions incident ("Degraded availability for Actions, Pages and Webhooks", 15:49 UTC) held every check in `queued` for ~45 minutes first. It cleared on its own.

**Sprint 775 monitoring verified in CI, not just locally.** Manually dispatched `uptime-check.yml` on `main`: run `39287982893` succeeded with `api=PASS site=PASS drift=SKIP`. The drift probe correctly SKIPs rather than false-alarming while `RENDER_API_KEY` is unset, and the failure-issue step correctly skipped.

## Next Priority

**Start here: the consolidated worklist** — `reports/next-actions-2026-10-20.md` (readable: https://claude.ai/code/artifact/cdbdd9eb-3039-44cf-a97b-23bc5c598543). It re-verified the 2026-10-19 assessment against current source — every load-bearing claim still held — and adds ten items neither earlier document covered. **It supersedes the 7-row order below**, which is kept for continuity.
Earlier artifacts: worklist https://claude.ai/code/artifact/03c5fdc7-21d6-4f5a-ad3e-75e54170a2b5 · assessment https://claude.ai/code/artifact/694c6f26-1673-48ee-88d6-4f18c2803b82 (also `reports/launch-readiness-assessment-2026-10-19.md`)

**CEO set a soft launch date (no fixed date) on 2026-10-19 and delegated the open decisions.** That reordered the plan: demand validation now leads and gates the four open accounting gaps; billing waits. Engineering is deliberately limited to work that is worth doing regardless of what CPAs say — liability, the money path, and making the system tell the truth about itself.

Two decisions are settled and recorded in `tasks/EXECUTIVE_BLOCKERS.md` → Resolved Decisions. **Do not re-open them:**
1. **Review gate removed from `main`** (all 12 required status checks kept, strict). Merges now take the normal path and CI genuinely blocks — `--admin` should no longer be needed, and needing it is a signal. Linear history is on, so **merges must squash or rebase**.
2. **The off-provider `pg_dump` → R2 backup ships BEFORE launch.** Neon PITR alone is not sufficient. *(This bullet previously recorded the opposite — deferred until before the second paying customer, on the premise that Zero-Storage meant no client financial data was persisted. That premise is false and the decision was reversed the same day it was made; `tasks/EXECUTIVE_BLOCKERS.md`, the `tasks/todo.md` DECISION block and the assessment addendum all carried the reversal, this file did not. Corrected 2026-10-20.)* The database persists auditor workpaper content: `diagnostic_summaries` (aggregate F/S totals), `uncorrected_misstatements` (`accounts_affected_json` — account names with DR/CR and amounts) and `analytical_expectations` (expected and actual values). Scope is Sprint 778; the policy contradiction this exposed was Sprint 783.

Order of work (detail in the worklist, sprints filed in `tasks/todo.md`):

| # | Item | Owner |
|---|------|-------|
| 01 | Read the `waitlist_signups` count — decides whether 03 is warm or cold | CEO |
| 02 | Send Terms + Privacy to counsel; Security Policy §12 phone | CEO — **blocks launch, longest lead** |
| 03 | 5–10 practising CPAs through demo + free tier on their own TB | CEO — **gates B-6…B-9** |
| 04 | **Sprint 779** — boundary-language + AS 1215 residue (liability) | Claude, ~1h |
| 05 | **Sprint 778** — build the `pg_dump` → R2 backup, verify Neon PITR retention, one restore drill per mechanism, fix the DR false-green | Claude + CEO console, ½d |
| 06 | **Sprint 780** — Stripe price-parity preflight + webhook coverage 59.9%→85% | Claude, ~1d |
| 07 | **Sprint 782** — design-system regression lint + external uptime monitor | Claude + CEO signup, ~2h |

Parked deliberately: B-6…B-9 (until 03 reports), Phase 4.1 live Stripe build (until pricing validated), 22-engine relocation, mypy baseline, dev-only npm advisories. **No longer parked:** the off-provider backup (ships pre-launch, Sprint 778) and the open-PR backlog (Sprint 785 — all nine real-work PRs now conflict, so leaving them costs more every day).

## Recent Git Context

```
cfaaf7b2  main HEAD
          └─ #167 launch readiness assessment      (docs)
          └─ #166 deploy-drift: compare trees      (docs/CI)
          └─ #145 qa_warden timeout 1700s          (tooling)
54f1963d  ← what production actually runs
          └─ #165 Sprint 774 outage recovery       (last backend change)
```

`main` is 3 merges ahead of the live deploy and all three touch nothing under `backend/`, so Render
correctly has not redeployed. The tree-based drift check from #166 reads this as PASS — which is the
exact false positive the original SHA comparison would have alarmed on every 15 minutes.
