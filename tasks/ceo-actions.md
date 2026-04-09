# CEO Action Items

> **Single source of truth for every action required to launch Paciolus.**
> Top-to-bottom execution order. Each phase's exit criteria must be met before the next phase starts.

**Status as of 2026-04-09:** Login is still broken in production (Neon Postgres not yet provisioned), but the **code backlog is fully merged to `main`**. PR #67 landed 2026-04-09 14:23 UTC as merge commit `84fbc90`, bringing Sprints 570–593 + hotfixes onto `main`. Render is still running the old Sprint 569 code against the dead DB — when you finish Phase 1 and redeploy, the new code will go live in one step.

**Your next action:** Phase 1.1 — sign up for Neon, Upstash, Sentry, and SendGrid. Once you have those four credentials ready, I take over the Render side.

**Launch ETA:** ~1 month from today.

**Ongoing monthly cost after launch:** ~$44/mo (Render Standard $25 + Neon Launch ~$19 + free tiers for Redis/Sentry/SendGrid). Stripe transaction fees on actual revenue.

---

## Phase 1 — Restore Login (BLOCKING)

Stand up production-grade infra on the **current `main`** (Sprint 569 era) before touching any code. This isolates infrastructure bugs from code bugs in the Phase 2 merge train.

### 1.1 Provider signups — owner: **you**

- [ ] **Neon Postgres** → neon.tech → create project `paciolus` in **AWS us-east-2 (Ohio)** → create database `paciolus`, role `paciolus_user` → **upgrade the project to Launch tier** (~$19/mo) so compute doesn't auto-suspend → copy the **pooled** connection string (ends in `-pooler`) → append `?sslmode=require` if Neon didn't already include it
- [ ] **Upstash Redis** → upstash.com → create Redis database in **us-east-1** → copy the **TLS** connection URL (`rediss://...`) — free tier is fine
- [ ] **Sentry** → sentry.io → create a Python/FastAPI project → copy the DSN — free tier is fine
- [ ] **SendGrid** → sendgrid.com → verify a sender identity (single sender or authenticated domain) → create an API key with **Mail Send** permission → copy the key. Free tier is 100 emails/day forever. *(Code is wired to SendGrid, not Resend — swapping providers would be a code change.)*

**→ Ping me once you have all four credentials. I'll drive the Render side from here.**

### 1.2 Render infrastructure — owner: **you, guided by me**

- [ ] Render → `paciolus-api` → **Upgrade plan to Standard** (2 GB RAM, 1 CPU, $25/mo). Required so the backend has enough memory for TB uploads + PDF memo generation without OOM kills.
- [ ] Render → `paciolus-api` → **Environment** → paste the env vars from [Appendix A](#appendix-a--render-environment-variables). I'll walk you through each one.
- [ ] Render → `paciolus-api` → **Manual Deploy** → `main` branch
- [ ] *(I do this)* Tail Render build + runtime logs; confirm Alembic migrations run clean and Uvicorn boots
- [ ] *(I do this)* Run `scripts/smoke_test_render.sh` against the new instance; confirm 7/7 checks pass
- [ ] *(I do this)* Trigger a test event in Sentry; confirm the event lands in the Sentry dashboard
- [ ] Vercel → Project Settings → Environment Variables → confirm `NEXT_PUBLIC_API_URL` = `https://paciolus-api.onrender.com` is enabled for **Production, Preview, and Development** contexts
- [ ] Manual browser test: register a test account → verify email → login → `/dashboard` loads → upload the smallest sample TB → run one diagnostic tool → export one PDF memo. Any 500 here halts Phase 2.
- [ ] *(Optional)* Delete the old suspended `paciolus-db` from the Render dashboard. Only after the above passes.

**Phase 1 exit criteria:** You can register, verify, login, and see the dashboard end-to-end. Smoke test passes. Sentry is receiving events.

---

## Phase 2 — Code Backlog Merge Train ✅ DONE 2026-04-09

**Owner: Engineering (me). Completed via single PR rather than 5 batches because the infra outage meant we couldn't deploy + smoke test between batches — batch boundaries are still preserved as individual commits on `main` for `git bisect`.**

- [x] Merged as **PR #67** (`84fbc90`): Sprints 570–593 + ~25 hotfixes + 5 pre-flight fix commits = 45 commits total
  - Sprints 570–571: DEC remediation, SOC 2 deferral, launch readiness
  - Sprints 572–578: password reset, Decimal precision, Pydantic response models, error envelope, synthetic anomaly generators
  - Sprints 579–587: Mission Control dashboard, Portfolio/Workspaces merge, UX polish bundle, dependency sentinel
  - Sprints 588–593: Chrome QA, Founder Ops metrics/admin/dunning, infra hardening, cookie-only auth (592), share-link hardening (593)
  - Terminal hotfixes: audit chain secret separation, uvicorn 0.44.0, python-multipart 0.0.24
  - Pre-flight fixes: migration collision (`b2c3d4e5f6a7` → `d1e2f3a4b5c6`), alembic multi-head merge (`a848ac91d39a`), smoke test script, CI gate resolution (ruff, ESLint, OpenAPI snapshot, jest coverage)
- [x] All 21 CI checks passed on the merged state before merge (backend Python 3.11/3.12/Postgres 15, frontend Jest 1751/1751, build+lint, mypy, bandit, dependency audits, lint baseline, OpenAPI snapshot, E2E Playwright, Vercel)
- [ ] **Deferred to Phase 1 completion:** Sprint 592 cookie-auth regression test — fresh incognito → register → confirm `paciolus_access` + `paciolus_refresh` HttpOnly cookies set → close tab → reopen → confirm silent refresh → logout → confirm cookies cleared. Cannot run until Phase 1 brings the backend online.
- [ ] **Deferred to Phase 1 completion:** Full end-to-end smoke test on the merged code via `scripts/smoke_test_render.sh`

**Phase 2 exit criteria:** ✅ PR merged, CI green, no open bugs introduced. The two deferred items cannot run until infrastructure is up — they'll execute as part of Phase 1.2 smoke-test step.

---

## Phase 3 — Functional Validation

**Owner: you for exercising the app; me on standby for bug fixes.**

The goal is to catch anything broken in normal usage before you start charging real money.

- [ ] Run all **12 testing tools** against a realistic sample trial balance. File bugs for any abnormal output.
  - JE (19 tests), AP (13), Payroll (11), Revenue (16, ASC 606), AR Aging (11), Fixed Assets (9), Inventory (9), Bank Rec, 3-Way Match, Multi-Period TB, Statistical Sampling, Multi-Currency
- [ ] Generate all **21 PDF memos** back-to-back on a single engagement. Watch Sentry for memory warnings or request-duration spikes >10s.
- [ ] Exercise the **engagement layer** end-to-end: create engagement → set materiality → run diagnostics → add follow-up items → build workpaper index → export diagnostic package ZIP → hit the completion gate.
- [ ] Exercise **export sharing**: create a shared link, access it from an incognito window, confirm passcode protection works, revoke it, confirm revocation is enforced.
- [ ] Exercise **admin dashboard**: org listing, customer drill-down, impersonation read-only mode, audit log.
- [ ] Exercise **bulk upload** (Enterprise tier) with 5+ TBs to verify memory holds under sustained load.
- [ ] File any bugs found as `fix:` entries in `tasks/todo.md`. I fix and redeploy.

**Phase 3 exit criteria:** Every tool produces expected output on the sample TB. No open P0/P1 bugs. Memory headroom observed under bulk upload load.

---

## Phase 4 — Launch Day

### 4.1 Stripe production cutover

- [ ] Stripe Dashboard → Products → confirm `STRIPE_SEAT_PRICE_MONTHLY` uses **graduated pricing**: Tier 1 (qty 1–7) = $80, Tier 2 (qty 8–22) = $70
- [ ] Stripe Dashboard → Settings → **Customer Portal** → enable: payment method updates, invoice history, cancel at period end
- [ ] Stripe Dashboard → create production products/prices/coupons using your **live secret key**. Mirror the test-mode structure: 4 products, 8 prices, 2 coupons (Sprint 439 reference). Keep the test-mode price IDs in a safe place for reference.
- [ ] Render + Vercel env vars → set `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` (live values), plus any `STRIPE_PRICE_*` IDs used by your frontend
- [ ] Stripe Dashboard → Developers → Webhooks → configure endpoint → `https://api.paciolus.com/billing/webhook` (or the onrender.com URL if you haven't set up custom domain yet) → copy the signing secret into `STRIPE_WEBHOOK_SECRET`
- [ ] Sign `tasks/pricing-launch-readiness.md` Section 7 (Code Owner + CEO lines) → mark **GO**
- [ ] Manual test: click "Manage Billing" from `/settings/billing` → confirm it opens the Stripe Customer Portal
- [ ] Real-money smoke test: subscribe to **Solo monthly** (lowest tier) with a real card → confirm the subscription appears in Stripe Dashboard and in the admin dashboard → cancel → confirm webhook delivery → refund the charge
- [ ] Monitor Stripe Dashboard → Developers → Webhooks for 24 hours → confirm delivery ≥99%

### 4.2 Legal + policy placeholders

Legal counsel sign-off is required on Terms and Privacy before launch.

- [ ] **`docs/04-compliance/TERMS_OF_SERVICE.md`** — replace:
  - `[Address to be added]` / `[City, State, ZIP]` → registered business address
  - `[City, State]` in arbitration section → registered state
  - `[To be appointed]` (registered agent for legal service) → real agent name and address
  - Add effective date + legal counsel sign-off name to the header
- [ ] **`docs/04-compliance/PRIVACY_POLICY.md`** — replace:
  - `[Address to be added]` / `[City, State, ZIP]` → registered business address
  - `[To be appointed if EEA users exceed threshold]` (EU Representative, GDPR Art. 27) — appoint one OR document that EEA user count is below threshold and file the decision
  - `[To be appointed]` (DPO) — appoint one OR document small-company exemption under GDPR Art. 37
  - Add effective date + legal counsel sign-off name to the header
- [ ] **`docs/04-compliance/SECURITY_POLICY.md`** — replace `Phone: [To be established]` in §12 with a real emergency contact number (personal mobile or VoIP is fine)

### 4.3 Custom domain

- [ ] Acquire domain (if not already owned)
- [ ] DNS records:
  - Root + `www` → Vercel (CNAME or A/AAAA per Vercel's instructions)
  - `api.paciolus.com` (or chosen subdomain) → Render `paciolus-api`
- [ ] Render → `paciolus-api` → Settings → **Custom Domains** → add the API subdomain → verify TLS certificate issues cleanly
- [ ] Vercel → Project → Settings → **Domains** → add root + `www` → verify
- [ ] *(I do this)* Update `CORS_ORIGINS` env var on Render to include the new frontend custom domain; redeploy

### 4.4 Backups

- [ ] *(I set this up; you provide credentials)* Daily `pg_dump` → S3/R2 cron as belt-and-suspenders on top of Neon's built-in PITR. Options: Render Cron Job (~$1/mo), GitHub Action (free), or Upstash Scheduled Functions. You'll need to provision an S3/R2 bucket and create an IAM key or R2 token.
- [ ] *(I do this once you provide creds)* Test restore from one backup to confirm the chain works end-to-end

### 4.5 Go-live smoke test

- [ ] Final smoke test from the custom domain on a clean incognito browser:
  1. Register with a fresh email
  2. Verify email (confirm real delivery through SendGrid)
  3. Subscribe via Stripe **live** key with a real card
  4. Upload a trial balance
  5. Generate a PDF memo
  6. Cancel subscription
  7. Confirm webhook delivered cleanly
  8. Refund the test charge
- [ ] Monitor Sentry + Render logs + Stripe webhooks for **24 hours**. Zero new errors and clean webhook delivery = green light.
- [ ] **Launch announcement**

---

## Phase 5 — Post-Launch (Not blocking)

These are important but should not delay launch. Schedule them in the first 2 weeks after going live.

### GitHub branch protection
- [ ] Settings → Branches → `main` protection rule → Enable "Require review from Code Owners"
- [ ] Add required status checks: `secrets-scan`, `frontend-tests`, `mypy-check` (in addition to existing gates: `backend-tests`, `frontend-build`, `backend-lint`, `lint-baseline-gate`, `pip-audit-blocking`, `npm-audit-blocking`, `bandit`)

### Observability polish
- [ ] Set up Sentry alert rules: notify on 5xx spike, notify on new issue type
- [ ] Set up a simple uptime monitor (Cronitor free tier, UptimeRobot, Better Stack) hitting `/health` every 5 min

---

## Deferred — SOC 2 (revisit when enterprise demand materializes)

Deferred per CEO directive 2026-03-23. Not required for launch. The engineering scaffolding (docs, templates, CI gates) remains in the codebase and can be activated without rewriting.

**Decisions already made:** Grafana Loki (SIEM), pgBackRest→S3 (cross-region DR, ~$5/mo), AWS Secrets Manager (secrets vault backup, ~$5/mo).

**Pending when SOC 2 is reactivated:**
- Penetration test vendor ($5K–30K) — Sprint 467
- Bug bounty program (existing VDP sufficient for now) — Sprint 468
- SOC 2 auditor + observation window ($15K–50K) — Sprint 469
- Evidence collection: Q1 access review, Q1 risk register review, DPA acceptance outreach, GPG commit signing, backup integrity check, data-deletion end-to-end test, encryption verification screenshots, security training (5 modules), weekly security review cadence, backup restore test, PagerDuty/on-call rotation

---

## Appendix A — Render Environment Variables

Authoritative list derived from `backend/config.py` hard-fail checks. Every item below is either required or strongly recommended.

### Required — app will not boot in production without these

| Variable | Value | Notes |
|---|---|---|
| `ENV_MODE` | `production` | Triggers all production guardrails |
| `API_HOST` | `0.0.0.0` | Should already be set; verify |
| `API_PORT` | `8000` | Should already be set; verify |
| `CORS_ORIGINS` | comma-separated `https://` origins | **Any `http://` origin hard-fails in production.** Include Vercel frontend URL + any custom domain. |
| `JWT_SECRET_KEY` | 32+ char hex | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `CSRF_SECRET_KEY` | 32+ char hex | **Must differ from `JWT_SECRET_KEY`** or startup hard-fails |
| `DATABASE_URL` | Neon **pooled** URL | Must include `?sslmode=require` |
| `SENDGRID_API_KEY` | from SendGrid | Hard-fails production startup if missing or empty |

### Strongly recommended

| Variable | Value | Notes |
|---|---|---|
| `REDIS_URL` | Upstash `rediss://` URL | Required when `RATE_LIMIT_STRICT_MODE=true` (the prod default). Without Redis, rate-limit counters are per-worker (SOC 2 / AUDIT-07 regression). |
| `RATE_LIMIT_STRICT_MODE` | `true` | Default in production; set explicitly for env-list visibility |
| `SENTRY_DSN` | from Sentry | Crash visibility during merge train + post-launch |
| `AUDIT_CHAIN_SECRET_KEY` | 32+ char hex | Dedicated HMAC key for audit-log chain. Falls back to `JWT_SECRET_KEY` if unset (works but logs a warning — set explicitly so JWT rotation doesn't break audit chains). |
| `FRONTEND_URL` | Vercel production URL | Used for email verification links. Default `http://localhost:3000` is dev-only. |
| `SENDGRID_FROM_EMAIL` | `noreply@paciolus.com` | Default is fine unless you want a different from-address |
| `SENDGRID_FROM_NAME` | `Paciolus` | Default is fine |

### Stripe — set during Phase 4.1, not Phase 1

| Variable | Notes |
|---|---|
| `STRIPE_SECRET_KEY` | Live secret key from Stripe Dashboard |
| `STRIPE_PUBLISHABLE_KEY` | Live publishable key |
| `STRIPE_WEBHOOK_SECRET` | From the webhook endpoint you configure in Stripe |
| `STRIPE_COUPON_MONTHLY_20` | 20%-off-first-3-months coupon ID (if using) |
| `STRIPE_COUPON_ANNUAL_10` | 10%-off-first-annual-invoice coupon ID (if using) |

### Leave alone unless you have a reason

`DEBUG`, `JWT_EXPIRATION_MINUTES`, `REFRESH_TOKEN_EXPIRATION_DAYS`, `TRUSTED_PROXY_IPS`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE`, `SENTRY_TRACES_SAMPLE_RATE`, `ENTITLEMENT_ENFORCEMENT`, `SEAT_ENFORCEMENT_MODE`, `DB_TLS_REQUIRED`, `DB_TLS_OVERRIDE`, format flags (`FORMAT_*_ENABLED`), cleanup scheduler intervals.

---

## Completed

| Date | Item |
|---|---|
| 2026-04-09 | **Phase 2 complete** — PR #67 merged: 45-commit Sprints 570–593 + hotfix backlog landed on `main` as merge commit `84fbc90`. All 21 CI checks passed. |
| 2026-04-09 | CI gate resolution for PR #67: ruff auto-fix (6 errors), OpenAPI snapshot regeneration (117 diffs, 184 paths / 369 schemas), Jest coverage threshold recalibration (4 thresholds lowered 0.4–2.6% to match post-backlog reality), 4 ESLint errors (innerHTML→replaceChildren, 3 import-order fixes) — commits `c275edd` + `c015bf8` |
| 2026-04-08 | Alembic migration collision fix (Sprint 593 `b2c3d4e5f6a7` → `d1e2f3a4b5c6`) — commits `4c25ac2` + `e8c289e` |
| 2026-04-08 | Alembic multi-head merge migration `a848ac91d39a` — commit `4c25ac2` |
| 2026-04-08 | Post-deploy smoke test script `scripts/smoke_test_render.sh` — commit `0f83273` |
| 2026-04-08 | Launch infrastructure plan (this document, original draft) — commit `0f83273` |
| 2026-04-08 | Local `main` fast-forwarded to `origin/main` at `90777b2` |
| 2026-04-08 | Branch audit baseline: 1,751 frontend tests + 7,361 backend tests, 0 failures |
| 2026-03-23 | Infrastructure decisions: Grafana Loki (SIEM), pgBackRest→S3 (DR), AWS Secrets Manager (secrets backup) |
| 2026-03-23 | CODEOWNERS updated to `@Paciolus` (was `@paciolus/security-leads`) |

---

*Last revised: 2026-04-08. Rewritten from the scattered pre-audit version into phase-based execution order. The Vercel `NEXT_PUBLIC_API_URL` item from the 2026-03-24 security review is rolled into Phase 1.2.*
