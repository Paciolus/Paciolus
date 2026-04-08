# CEO Action Items

> **Single source of truth for everything requiring your direct action.**
> Engineering delivers scaffolding; you complete execution.
> Check boxes (`[ ]` → `[x]`) as you complete items, then move to [Completed](#completed).

**Last synchronized:** 2026-04-08 — Launch Infrastructure Restoration plan added after free-tier Postgres expiration outage. Sprints 447–593 in scope.

---

## Priority Guide

| Symbol | Meaning |
|--------|---------|
| 🟡 | Milestone — major business action (billing launch, legal) |
| ⚪ | Setup — one-time infrastructure/admin tasks |
| 🔵 | Decision — blocks an engineering sprint |
| 🗄️ | Deferred — SOC 2 items, revisit when enterprise demand materializes |

---

## 🟡 Launch Infrastructure Restoration (Plan B-Early)

> **Status as of 2026-04-08:** Free-tier Render Postgres `paciolus-db` (`dpg-d6iqlq5m5p6s73dude20-a`) expired 2026-04-01, was suspended by Render billing, and its DNS record was torn down. Every `/auth/login` request now hangs on `psycopg2.OperationalError: could not translate host name` until the frontend's 30s fetch timeout fires — from the user's perspective, login "times out." This is an infrastructure outage, not a code bug.
>
> **Plan:** Stand up production-grade infra on the **current `main`** code first (Sprint 565 era), verify login works end-to-end, then merge the Sprint 588–593 + hotfix backlog into the working environment in small batches, then complete launch-day items. Strict dependency order — no calendar buckets, run as fast as each step completes.
>
> **Target cost:** ~$44/mo (Render Standard $25 + Neon Launch ~$19 + Upstash Redis / Sentry / SendGrid on free tiers).
>
> **Why not cheaper "testing stack first":** A Neon free + Render Starter setup would save ~$37 total but gives you a flaky 512 MB box with no observability during the most bug-hunting-intensive phase of the project. Same deployment pipeline, same env-var work, but you'd need to re-test everything on the real stack before launch anyway. False economy at this scale. See chat history 2026-04-08 for full tradeoff analysis.
>
> **Task ownership:** `(CEO)` = you execute directly (billing, provider signup, secret values, DNS). `(Eng)` = engineering-side (code merges, deploys, log reading, smoke tests). Unmarked = either.
>
> **Audit findings uncovered 2026-04-08 during pre-flight check** (see chat history):
> 1. **Email provider is SendGrid, not Resend.** `backend/config.py:481` hard-fails production startup on missing `SENDGRID_API_KEY`. The `email_service.py` module imports and calls SendGrid's SDK directly. Adding Resend would be a code change (half-day of work). Plan updated to use SendGrid free tier (100 emails/day forever).
> 2. **Backlog is ~56 commits spanning Sprints 566–593 plus ~30 hotfixes**, not 5 sprints as originally stated. Covered sprints: 566, 567, 568, 569, 570, 571, 572, 573, 574, 576, 578, 579, 580, 581, 582–585, 586, 587, 588, 589–591, 592, 593. Merge plan section below has been rewritten to reflect the real scope in reviewable batches.
> 3. **Migration collision fixed locally, uncommitted.** Sprint 593 migration `b2c3d4e5f6a7_add_share_security_columns.py` collided with existing Sprint 345 `b2c3d4e5f6a7_add_soft_delete_columns.py` — both used the same revision ID. The new one has been renamed to `d1e2f3a4b5c6_add_share_security_columns.py` with the internal revision ID updated. File rename is staged via `git mv`. **Commit this with the Sprint 593 merge batch.**
> 4. **Alembic multi-head fixed locally, uncommitted.** The backlog introduced 3 parallel migration heads (`591a_dunning`, `c2d3e4f5a6b7`, `d1e2f3a4b5c6`) that would have caused `alembic upgrade head` to fail on deploy. A merge migration `a848ac91d39a_merge_sprint_590_591_593_heads.py` has been generated. It has empty `upgrade()`/`downgrade()` — purely a graph merge. **Commit this with the final hotfix batch of the merge train.** Single head confirmed after merge.
> 5. **Fresh-DB bootstrap verified safe.** Dockerfile `CMD` runs `alembic stamp head` (not `upgrade head`) when `alembic_version` table is missing; then FastAPI lifespan calls `init_db()` → `Base.metadata.create_all()` which builds all tables from current model definitions. Fresh Neon DB will boot clean.
> 6. **Frontend baseline green.** `npm test`: 1751/1751 passed, 167 suites, 64s. `npm run build`: clean. Both match the expectations in memory notes (1,357 Jest tests listed in memory is stale — real count is 1751).

### Provider signups (CEO)
- [ ] **Neon** (neon.tech) — create account → create project `paciolus` in **AWS US East 2 (Ohio)** region → create database `paciolus`, role `paciolus_user` → upgrade project to **Launch** tier (~$19/mo) so compute does not auto-suspend → copy the **pooled** connection string (ends in `-pooler`) → append `?sslmode=require` if not already present
- [ ] **Upstash Redis** (upstash.com) — create account → create Redis database in `us-east-1` → copy the **TLS** connection URL (`rediss://...`) — free tier is sufficient
- [ ] **Sentry** (sentry.io) — create account → create Python/FastAPI project → copy the DSN — free tier is sufficient
- [ ] **SendGrid** (sendgrid.com) — create account → verify a sender identity (single sender or authenticated domain) → create API key with **Mail Send** permission → record `SENDGRID_API_KEY`. Free tier is 100 emails/day forever. **Note:** the code is wired to SendGrid, not Resend — `backend/email_service.py` imports `sendgrid` directly and `backend/config.py:481` hard-fails production on missing `SENDGRID_API_KEY`. Swapping to Resend would be a code change, not a config change.

### Render infra stand-up
- [ ] **(CEO)** Render dashboard → `paciolus-api` → **upgrade plan to Standard** (2 GB RAM, 1 CPU, $25/mo)
- [ ] **(CEO)** Render dashboard → `paciolus-api` → **Environment** → set/update. The production `_hard_fail` list in `backend/config.py` is authoritative; every item below is either required or strongly recommended:
  - **Required (hard-fail if missing in production):**
    - `ENV_MODE` = `production`
    - `API_HOST` = `0.0.0.0`  *(should already be set; verify)*
    - `API_PORT` = `8000`  *(should already be set; verify)*
    - `CORS_ORIGINS` = comma-separated `https://` origins only — include the Vercel production URL + any custom domain you'll add later. **Any `http://` origin hard-fails in production.**
    - `JWT_SECRET_KEY` = 32+ char random hex (`python -c "import secrets; print(secrets.token_hex(32))"`)
    - `CSRF_SECRET_KEY` = 32+ char random hex, **must differ from `JWT_SECRET_KEY`**
    - `DATABASE_URL` = Neon pooled URL from signup step, **must include `?sslmode=require`** (pool-mode connection, not direct)
    - `SENDGRID_API_KEY` = key from SendGrid signup (hard-fails production startup if missing)
  - **Strongly recommended:**
    - `REDIS_URL` = Upstash `rediss://` URL (required if `RATE_LIMIT_STRICT_MODE=true`, which defaults to true in production — leaving Redis unset forces `RATE_LIMIT_STRICT_MODE=false` which degrades rate limits to per-worker and is a SOC 2 / AUDIT-07 regression)
    - `RATE_LIMIT_STRICT_MODE` = `true`  *(default in production, but set explicitly so it's visible in the env list)*
    - `SENTRY_DSN` = from Sentry (optional but you'll want it during the merge train for crash visibility)
    - `AUDIT_CHAIN_SECRET_KEY` = dedicated 32+ char hex key for audit-log HMAC chain integrity. **Falls back to `JWT_SECRET_KEY` if unset** (works fine, but logs a warning; set a dedicated key so JWT rotation doesn't break audit chains).
    - `SENDGRID_FROM_EMAIL`, `SENDGRID_FROM_NAME` (defaults: `noreply@paciolus.com` / `Paciolus`)
  - **Leave alone unless specifically needed:**
    - `FRONTEND_URL` (used for email verification links; default `http://localhost:3000` is dev-only — set to your Vercel URL before production)
    - `TRUSTED_PROXY_IPS`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE` — tunable, defaults are fine
    - `STRIPE_*` — handled by the existing Sprint 447 Stripe Cutover item below
- [ ] **(CEO)** Render dashboard → `paciolus-api` → **Manual Deploy** → `main` branch. This boots March-23 Sprint 565 code against the new infra so the first test isolates infra from code changes.
- [ ] **(Eng)** Tail Render logs during the deploy. Confirm Alembic migrations run clean (Dockerfile runs them on boot per Sprint 543-545). Confirm `Uvicorn running on ...`. Flag any startup errors before moving on.
- [ ] **(Eng)** `curl https://paciolus-api.onrender.com/health` → expect HTTP 200 within ~1s. Or run the full post-deploy smoke test: `scripts/smoke_test_render.sh` (exercises /health, /auth/csrf rejection, register, /auth/me, wrong-password rejection, logout, session revocation).
- [ ] Confirm Sentry receives a test event — use Sentry's "Verify Installation" flow or intentionally hit a broken endpoint and watch Issues populate.
- [ ] **(CEO)** Vercel dashboard → Project Settings → Environment Variables → verify `NEXT_PUBLIC_API_URL` = `https://paciolus-api.onrender.com` is enabled for **Production, Preview, and Development** contexts (this overlaps with the existing "Vercel Environment Variable" item below — resolves both).
- [ ] Smoke test Sprint 565 code: register a new account → verify email → login → `/dashboard` loads → upload smallest sample TB from `backend/tests/data/` → run one diagnostic tool → export one PDF memo. If anything 500s, stop and debug before the backlog merge.
- [ ] **(CEO)** Once the new DB is verified working, delete the old suspended `paciolus-db` from the Render dashboard to stop confusing yourself with a dead resource. *(Optional cleanup — do not do before smoke test passes.)*

### Sprint backlog merge (Eng-led, CEO approves each merge)
> **Real scope (audit 2026-04-08):** Branch `sprint-565-chrome-qa-remediation` is **56 commits** ahead of `main`, spanning **Sprints 566–593 plus ~30 hotfixes**, 17 days of divergence (2026-03-22 to 2026-04-07). Merge in the batches below — each batch is small enough to bisect if it breaks. Run the full smoke test between batches.
>
> **Pre-merge fixes already staged locally (uncommitted, included with the batches indicated below):**
> - Sprint 593 migration rename: `b2c3d4e5f6a7_add_share_security_columns.py` → `d1e2f3a4b5c6_add_share_security_columns.py` with internal `revision` string updated. Commit with Batch D (Sprint 593).
> - Alembic merge migration: `a848ac91d39a_merge_sprint_590_591_593_heads.py`. Commit with Batch E (final hotfix batch) so all three heads exist before the merge node.

- [ ] **(Eng)** Branch audit — ✅ completed 2026-04-08. Frontend baseline: 1751/1751 Jest tests pass in 64s, `npm run build` clean. Backend baseline: pytest run in progress at report time; see chat for final result. Record any pre-existing failures before the merge train starts so they're not mis-attributed to later merges.
- [ ] **(Eng) Batch A — Design + Mission Control (Sprints 566–571):** Includes Sprint 566 frontend design enrichment, Sprint 567 14-dep backend upgrade, theme contrast hotfix, Sprints 568/569 QA bug fixes, Sprint 570 DEC remediation, SOC 2 deferral, Sprint 571 launch readiness (8 items), archive-570/571 hotfix. ~10 commits. Deploy. Smoke test.
- [ ] **(Eng) Batch B — Precision + Pydantic + Errors (Sprints 572–578):** Password reset flow (572), Decimal arithmetic (573), TB response model reconciliation (574), Pydantic response models for org/admin/branding/export/bulk-upload (576), ingest string-dtype hotfix, backend error envelope standardization, synthetic generators (578), responsive hotfixes. ~9 commits. Deploy. Smoke test password reset flow specifically.
- [ ] **(Eng) Batch C — Mission Control + UX Polish (Sprints 579–587):** Mission Control dashboard (579), Portfolio/Workspaces merge (580), nightly report remediation (581), UX polish bundle — toast/onboarding/a11y/actionable errors (582–585), nightly remediation (586), dependency sentinel 2x (587). ~7 commits. Deploy. Smoke test dashboard + portfolio/workspace flows.
- [ ] **(Eng) Batch D — Chrome QA + Founder Ops + Sprint 592 + Sprint 593 (Sprints 588–593):** Sprint 588 Chrome QA (8 security fixes), dashboard activity hotfix, Sprint 589–591 Founder Ops (metrics API, admin console, dunning), audit baseline + full sweep hotfixes, archive 586–591, nightly remediation (11 failures fixed), dunning metrics timing race fix, Meridian framework (3 commits), dep sentinel calver, DEC remediation, dependency upgrades (14 packages), **infrastructure hardening** (introduces `RATE_LIMIT_STRICT_MODE` default true in prod and `DB_TLS_REQUIRED`), **Sprint 592 cookie-only auth**, nightly remediation hotfix, **Sprint 593 share-link hardening** (includes the renamed `d1e2f3a4b5c6` migration). ~23 commits. Largest batch — consider splitting D into D1 (588–591) and D2 (592–593) if you want finer bisect granularity.
  - **Highest-risk merge inside this batch is Sprint 592 (c58861a).** Extra regression test after deploy: fresh incognito → register → DevTools → confirm `paciolus_access` + `paciolus_refresh` HttpOnly cookies are set → close tab → reopen → confirm silent refresh works with no re-login → logout → confirm both cookies cleared. The frontend/backend auth contract changes cross-cut the whole app.
- [ ] **(Eng) Batch E — Terminal hotfixes (post-593):** Audit chain secret separation (`AUDIT_CHAIN_SECRET_KEY` from `JWT_SECRET_KEY`), uvicorn 0.44.0 + python-multipart 0.0.24 dependency patch, **and the alembic merge migration `a848ac91d39a`** that collapses the three-head state into a single head. ~3 commits. Deploy. Smoke test.
- [ ] **(Eng)** Full end-to-end smoke test on the latest code once all batches are in: `scripts/smoke_test_render.sh` + manual browser session covering dashboard, one testing tool, one PDF memo, admin dashboard.

### Full functional exercise
- [ ] Run all **12 testing tools** against a realistic sample TB: JE (19 tests), AP (13), Payroll (11), Revenue (16), AR Aging (11), Fixed Assets (9), Inventory (9), Bank Rec, Three-Way Match, Multi-Period TB, Statistical Sampling, Multi-Currency. Log any abnormal output as `fix:` entries in `tasks/todo.md`.
- [ ] Generate all **21 PDF memos** back-to-back on a single engagement. Watch Sentry for memory warnings and request duration spikes. If p99 > 10s, flag for investigation before launch.
- [ ] Exercise the **engagement layer** end-to-end: create engagement → set materiality → run diagnostics → add follow-up items → build workpaper index → export diagnostic package ZIP → hit completion gate.
- [ ] Exercise **export sharing** and **admin dashboard**: create a shared export link, access it from an incognito window, confirm expiration behavior, revoke it, confirm revocation is enforced.
- [ ] **(CEO)** Test **bulk upload** (Enterprise tier feature) with 5+ TBs to verify memory holds under sustained load.
- [ ] Fix any bugs found as `fix:` hotfixes committed to `main`. Redeploy. Re-test the affected flows.

### Launch-day items
- [ ] **(CEO)** Complete the **Stripe Production Cutover (Sprint 447)** section below — this is the existing blocker item and is unchanged. Set live Stripe secret keys on Render + Vercel, configure webhook → `https://paciolus-api.onrender.com/billing/webhook`, record `STRIPE_WEBHOOK_SECRET`, run `alembic upgrade head` if any new migrations landed during the backlog merge.
- [ ] **(CEO)** Complete the **Legal + Admin Placeholders** section below — TOS address/state/agent, Privacy address/EU rep/DPO, Security emergency contact. Legal counsel sign-off required on TOS and Privacy before launch.
- [ ] **(CEO)** Acquire custom domain if not already owned. Configure DNS:
  - Root + `www` → Vercel (frontend)
  - `api.paciolus.com` (or chosen subdomain) → Render `paciolus-api`
- [ ] **(CEO)** Render → `paciolus-api` → Settings → **Custom Domains** → add API subdomain, verify TLS certificate issues cleanly.
- [ ] **(CEO)** Vercel → Project → Settings → **Domains** → add root + www, verify.
- [ ] **(Eng)** Update `CORS_ORIGINS` env var on Render to include the new frontend custom domain. Redeploy `paciolus-api`.
- [ ] **(Eng)** Set up a daily `pg_dump` → S3/R2 cron as belt-and-suspenders on top of Neon PITR. Options: Render Cron Job (~$1/mo), GitHub Action (free), or a small script on a Render Background Worker. Rotate keys and test restore once before relying on it.
- [ ] Final smoke test from the custom domain on a clean incognito browser: register → verify email (confirm real delivery through SendGrid) → subscribe via Stripe **live** key with a real card → upload TB → generate memo → cancel subscription → confirm webhook delivered cleanly. Refund the test charge afterward through the Stripe dashboard.
- [ ] Monitor Sentry + Render logs + Stripe webhooks for **24 hours** after the final smoke test. No new errors and clean webhook delivery = green light.
- [ ] **(CEO)** Launch announcement.

---

## 🟡 Stripe Production Cutover (Sprint 447)

> All 27/27 E2E smoke tests passed. Code is production-ready. Blocked only on your `sk_live_` keys and sign-off.

- [ ] Stripe Dashboard → Products → confirm `STRIPE_SEAT_PRICE_MONTHLY` uses **graduated pricing**: Tier 1 (qty 1–7) = $80, Tier 2 (qty 8–22) = $70
- [ ] Stripe Dashboard → Settings → **Customer Portal** → enable: payment method updates, invoice history, cancel at period end
- [ ] Manual test: click "Manage Billing" from `/settings/billing` → confirm it opens the Stripe portal
- [ ] Sign [`tasks/pricing-launch-readiness.md`](pricing-launch-readiness.md) Section 7 (Code Owner + CEO lines) → mark **GO**
- [ ] Create production Stripe products/prices/coupons using `sk_live_` key — same structure as test mode (4 products, 8 prices, 2 coupons per Sprint 439)
- [ ] Set all `STRIPE_*` production env vars on Render + Vercel; deploy with `alembic upgrade head`
- [ ] Smoke test: place a real charge on Solo monthly (lowest tier) using a real card
- [ ] Monitor Stripe Dashboard → Developers → Webhooks for 24 hours; confirm delivery ≥99%

---

## 🟡 Legal + Admin Placeholders

These are live in public-facing documents and need to be filled in before launch.

### Terms of Service [`docs/04-compliance/TERMS_OF_SERVICE.md`](../docs/04-compliance/TERMS_OF_SERVICE.md)
- [ ] Replace `[Address to be added]` / `[City, State, ZIP]` with registered business address
- [ ] Replace `[City, State]` in the arbitration section with registered state
- [ ] Replace `[To be appointed]` (registered agent for legal service) with actual registered agent name/address
- [ ] Obtain legal counsel sign-off → add effective date + sign-off name to doc header

### Privacy Policy [`docs/04-compliance/PRIVACY_POLICY.md`](../docs/04-compliance/PRIVACY_POLICY.md)
- [ ] Replace `[Address to be added]` / `[City, State, ZIP]` with registered business address
- [ ] Replace `[To be appointed if EEA users exceed threshold]` (EU Representative, GDPR Art. 27) — either appoint or confirm EEA user count is below threshold and document the decision
- [ ] Replace `[To be appointed]` (DPO) — appoint a Data Protection Officer or document that one is not required (small company exemption under GDPR Art. 37)
- [ ] Obtain legal counsel sign-off → add effective date + sign-off name to doc header

### Security Policy [`docs/04-compliance/SECURITY_POLICY.md`](../docs/04-compliance/SECURITY_POLICY.md)
- [ ] Replace `Phone: [To be established]` in §12 with an actual emergency contact number for critical security incidents (can be a personal mobile or a VoIP number)

---

## ⚪ Vercel Environment Variable — Security Review 2026-03-24

> Pentest found the preview deployment at `paciolus-mvrbyh4ek-paciolus-projects.vercel.app` falls back to `http://localhost:8000` — all API calls fail. The `NEXT_PUBLIC_API_URL` env var is missing or scoped only to Production.

- [ ] Vercel Dashboard → Project Settings → Environment Variables → `NEXT_PUBLIC_API_URL` = `https://paciolus-api.onrender.com` → enable for **Production**, **Preview**, and **Development** contexts
- [ ] Redeploy latest commit to verify API calls work on preview URL

---

## ⚪ One-Time Infrastructure Setup

### GitHub Branch Protection — Sprint 496 (Engineering Process Hardening)
> CODEOWNERS and new CI jobs are deployed but require GitHub settings to enforce.
- [ ] Settings > Branches > `main` protection rule: Enable "Require review from Code Owners"
- [ ] Settings > Branches > `main` protection rule: Add required status checks: `secrets-scan`, `frontend-tests`, `mypy-check` (in addition to existing gates)
- [ ] Settings > Branches > `main` protection rule: Confirm all existing required checks still listed (backend-tests, frontend-build, backend-lint, lint-baseline-gate, pip-audit-blocking, npm-audit-blocking, bandit)
- [x] Replace `@paciolus/security-leads` in `.github/CODEOWNERS` with `@Paciolus`

---

## 🔵 Decisions Made (Ready for Engineering)

> These decisions were made 2026-03-23. Engineering can begin when prioritized.

- [x] **Sprint 463 — SIEM approach**: **Grafana Loki** (Grafana Cloud free tier)
- [x] **Sprint 464 — Cross-region DB replication**: **pgBackRest to S3** (~$5/mo)
- [x] **Sprint 466 — Secrets vault secondary backup**: **AWS Secrets Manager** (~$5/mo)

---

## 🗄️ Deferred — SOC 2 (Revisit When Needed)

> All items below are deferred per CEO directive (2026-03-23). SOC 2 is not legally
> required for launch. Revisit if/when enterprise customers require SOC 2 attestation.
> The engineering scaffolding (docs, templates, CI gates) remains in the codebase and
> can be activated when needed.

### Deferred Decisions
- [ ] **Sprint 467 — Penetration test vendor** ($5K-30K)
- [ ] **Sprint 468 — Bug bounty program** (existing VDP sufficient for now)
- [ ] **Sprint 469 — SOC 2 auditor + observation window** ($15K-50K)

### Deferred CEO Tasks (SOC 2 Evidence)
- [ ] Q1 Access Review (7 dashboards) — CC6.1
- [ ] Q1 Risk Register review (12 risks) — CC4.1
- [ ] DPA Acceptance — existing customer outreach — PI1.3 / C2.1
- [ ] GPG Commit Signing setup — CC8.6
- [ ] Backup Integrity Check — first run — S1.5 / CC4.2
- [ ] Data Deletion Procedure — end-to-end test — PI4.3 / CC7.4
- [ ] Encryption Verification Screenshots — CC7.2
- [ ] Security Training (5 modules) — CC2.2
- [ ] Weekly Security Review cadence — CC4.2 / C1.3
- [ ] Backup Restore Test — S3.5
- [ ] PagerDuty / On-Call Rotation setup

### Deferred Recurring Calendar (SOC 2)
> These recurring tasks are only needed once SOC 2 observation window begins.
> Not listed here in detail — full schedule preserved in git history.

---

## ✅ Completed

Move items here with date when done.

| # | Item | Completed |
|---|------|----------|
| — | *(none yet)* | |

---

## How This File Works

- **Engineering** adds new items at the end of each sprint (post-sprint checklist step)
- **You** work top-to-bottom: 🟡 → ⚪ → 🔵 → 🗄️ (only when needed)
- When done: check the box, move to ✅ with the date
- This file is version-controlled — the action history is auditable

---

*Synchronized with: `tasks/todo.md` active phase + `docs/04-compliance/` full audit*
*SOC 2 deferral: 2026-03-23 — all SOC 2 actions tabled until enterprise demand materializes*
