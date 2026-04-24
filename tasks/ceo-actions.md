# CEO Action Items

> **Single source of truth for every action required to launch Paciolus.**
> Top-to-bottom execution order. Each phase's exit criteria must be met before the next phase starts.

**Status as of 2026-04-24:** **Phases 1 and 2 complete.** Production live at https://paciolus.com on Render Standard + Neon Launch Postgres + Upstash Redis + Sentry + SendGrid Domain Authentication. Post-Phase-1 infra hardening has extended the foundation: `DB_TLS_OVERRIDE` cleared 2026-04-23 (Sprint 673), Neon password rotated 2026-04-22, orphan Render Postgres deleted 2026-04-22, SendGrid Single Sender revoked 2026-04-22, R2 buckets provisioned 2026-04-23 (unblocks Phase 4.4 backups and landed Sprint 611 ExportShare migration same day), Sprint 716 Loki log aggregation deployed 2026-04-24. Sentry integration verified by live traffic (Sprint 711 bugs surfaced in the process).

**Your next action:** Phase 3 — Functional Validation. Exercise the 12 testing tools, 18 memo PDFs + 3 report PDFs, engagement layer, export sharing, admin dashboard, and bulk upload on https://paciolus.com. File bugs as you find them; I'm on standby.

**Ongoing monthly cost after launch:** ~$44/mo (Render Standard $25 + Neon Launch ~$19 + free tiers for Redis / Sentry / SendGrid). Stripe transaction fees on actual revenue.

---

## 📋 Remaining launch path

Three gates left between here and announcement. The code is launch-ready; the gating path is CEO calendar + legal sign-off.

1. **[Phase 3](#phase-3--functional-validation) — Functional Validation (CEO).** Full checklist below. Exit: no open P0/P1 bugs, memory headroom confirmed under bulk load.
2. **[Phase 4.1](#41-stripe-production-cutover) + [4.2](#42-legal--policy-placeholders) — Stripe live cutover + legal placeholders (CEO + counsel).** Stripe live keys on Render/Vercel, real-money smoke test, legal counsel sign-off on Terms + Privacy.
3. **[Phase 4.3](#43-custom-domain)–[4.5](#45-go-live-smoke-test) — Domain, backups, go-live (CEO provides creds, I run backups setup).** Custom domain + DNS, pg_dump cron to `paciolus-backups`, 24h go-live monitor, launch announcement.

**DMARC tightening** (non-blocking): move `_dmarc.paciolus.com` from `p=none` to `p=quarantine` ~2 weeks after the first real-money Stripe transaction confirms deliverability holds. I'll flag.

---

## Phase 1 — Restore Login ✅ DONE 2026-04-09

Render Standard deploy live. Neon (us-east-1 pooled) + Upstash Redis + Sentry wired. SendGrid Domain Authentication for `paciolus.com` verified after an initial DMARC bounce on the `@gmail.com` sender — DNS records (SPF/DKIM/DMARC) added to Vercel, propagated in under 2 minutes, and verified by SendGrid. Email verification flow confirmed end-to-end in Gmail inbox. Smoke test green (health, CSRF, register with HttpOnly cookies, /auth/me, wrong-password, logout). First user landed in the fresh Neon DB.

**Full detail, operational learnings, and exact commands archived in [`tasks/archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md`](archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md).**

### Phase 1 open follow-ups

- [x] **DMARC tightened to `p=quarantine` 2026-04-24.** `_dmarc.paciolus.com` updated in Vercel DNS; verified propagated on both Google (8.8.8.8) and Cloudflare (1.1.1.1) resolvers within seconds (TTL 60). Next step: ~30 days of observation; if no deliverability complaints, escalate to `p=reject` around 2026-05-24. Optional: add `rua=mailto:dmarc@paciolus.com` once a reporting mailbox exists.

> Other Phase 1 follow-ups (DB_TLS_OVERRIDE removal, Sentry verification, SendGrid Single Sender cleanup, orphan Render Postgres deletion, Neon password rotation) all landed 2026-04-22/23 — see the Completed table below.

---

## Phase 2 — Code Backlog Merge Train ✅ DONE 2026-04-09

PR #67 merged as one consolidated batch (merge commit `84fbc90`) rather than 5 smaller PRs — the infra outage meant we couldn't deploy + smoke test between batches, so bisect-granularity via individual commits in `main` history is the fallback if a regression shows up later. Scope: 45 commits total spanning Sprints 570–593 plus ~25 hotfixes plus 5 pre-flight fix commits (migration collision, alembic multi-head merge, smoke test script, CI gate resolution, ceo-actions.md rewrite). All 21 CI checks green before merge.

**Full detail archived alongside Phase 1 in [`tasks/archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md`](archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md).**

---

## Phase 3 — Functional Validation

**Owner: you for exercising the app; me on standby for bug fixes.**

The goal is to catch anything broken in normal usage before you start charging real money.

- [ ] Run all **12 testing tools** against a realistic sample trial balance. File bugs for any abnormal output.
  - JE (19 tests), AP (13), Payroll (11), Revenue (16, ASC 606), AR Aging (11), Fixed Assets (9), Inventory (9), Bank Rec, 3-Way Match, Multi-Period TB, Statistical Sampling, Multi-Currency
- [ ] Generate all **18 memo PDFs + 3 report PDFs** back-to-back on a single engagement. Watch Sentry for memory warnings or request-duration spikes >10s.
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

## Backlog Blockers — provisioning gates

These items unblock backlog sprints that cannot proceed without infra you must
provision. Not launch-blocking, but each one is a sprint that's been started or
is queued and is held until the resource exists.

### Object store bucket (R2 or S3) — RESOLVED 2026-04-23

Cloudflare R2 provisioned with two scoped buckets (`paciolus-backups`, `paciolus-exports`), two Object R&W Account API tokens, and 8 env vars wired to Render `paciolus-api` (zero downtime across rolling deploy). Sprint 611 ExportShare migration landed same-day against `paciolus-exports` (route writes to `shares/<share_token_hash>`, cleanup scheduler deletes on expiry/revoke). **Only remaining consumer: [Phase 4.4](#44-backups) daily `pg_dump` cron against `paciolus-backups`.** Full provisioning record in the 2026-04-23 Completed entry; screenshot-leak lesson in `tasks/lessons.md`.

---

## Phase 5 — Post-Launch (Not blocking)

These are important but should not delay launch. Schedule them in the first 2 weeks after going live.

### GitHub branch protection
- [x] **Applied 2026-04-24** via `gh api` PUT on `repos/Paciolus/Paciolus/branches/main/protection`. Required Code Owner review (1 approval, dismiss stale on push). Required linear history. Force-push and deletion blocked. Required conversation resolution. `enforce_admins: false` preserved as admin break-glass. Required status checks (12, all matched against the actual job display names from the latest green main run): Secrets Scan, Backend Tests (Python 3.11 + 3.12 + PostgreSQL 15), Frontend Build + Lint, Frontend Tests (Jest), Backend Lint (ruff), Backend Type Check (mypy), Lint Baseline Gate, Python Dependency Audit (blocking), Node Dependency Audit (blocking), Security SAST (Bandit). Optional/deferred: OpenAPI Schema Drift, Documentation Consistency, Accounting Policy, Report Standards (all run + green on main but not added to required set per Phase 5 spec).

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

> One-line milestone record. Full Phase 1 & 2 detail lives in [`tasks/archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md`](archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md).

| Date | Milestone |
|---|---|
| 2026-04-24 | **Branch protection on `main` applied** (Phase 5) — `gh api` PUT with 12 required status checks (matched to actual job display names), required Code Owner review, linear history, force-push + deletion blocked, conversation resolution required, admin break-glass preserved (`enforce_admins: false`). Closed the gap where commit-msg hook + CODEOWNERS were both advisory at the remote |
| 2026-04-24 | **DMARC tightened to `p=quarantine`** — `_dmarc.paciolus.com` TXT record updated in Vercel DNS (TTL 60); propagation verified on Google + Cloudflare resolvers within seconds; 30-day observation window then escalate to `p=reject` |
| 2026-04-24 | **Sprint 716 complete** — Grafana Loki log aggregation (in-process handler) deployed to production; 40 ingested lines verified in Logs Explorer with correct labels; 6 saved queries authored; runbook `docs/runbooks/observability-loki.md` §4 LogQL corrected for actual ingest-layer indexing |
| 2026-04-23 | **R2 buckets provisioned + Sprint 611 ExportShare migration landed** — `paciolus-backups` and `paciolus-exports` on Cloudflare R2 (ENAM, private, per-bucket scoped tokens); 8 env vars wired to Render (19→27 vars, zero downtime across 9× /health 200 polls); Sprint 611 route now writes share bytes to `paciolus-exports` keyed by `shares/<share_token_hash>` |
| 2026-04-23 | **`DB_TLS_OVERRIDE` cleared** (Sprint 673) — pooler-aware `pg_stat_ssl` skip shipped 2026-04-22; CEO env-var delete 10:26 UTC went live 10:28 UTC; post-deploy logs show `tls=pooler-skip` with zero override warnings; 2026-05-09 fuse cleared |
| 2026-04-22 | **Neon password rotation** — `neondb_owner` rotated after plaintext DATABASE_URL rendered in a screenshot tool result during orphan-DB investigation; Render env var updated, deploy `937997a` green, paciolus.com login smoke-tested clean. Side effect: this redeploy also shipped PR #93 (Sprints 703–709 typography + design refresh) to prod for the first time |
| 2026-04-22 | **Orphan Render Postgres `paciolus-db` deleted** — was a Basic-1gb paid plan (~$7-19/mo) holding 85 MB of orphaned pre-Neon data, 0 open connections; verified `paciolus-api` DATABASE_URL points to Neon before deletion |
| 2026-04-22 | **SendGrid Single Sender Verification revoked** for `comcgee89@gmail.com` — Domain Authentication on `paciolus.com` is now the sole sending path |
| 2026-04-22 | **Sentry integration verified via live traffic** — 9+ unresolved prod issues already in dashboard (`cleanup_scheduler`, `/auth/verification-status`, `/audit/trial-balance`, `/audit/preflight`); no deliberate test event needed. Bonus: surfaced two P1 bugs (~670 events combined) captured as Sprint 711 |
| 2026-04-09 | **Phase 1 complete** — Render Standard deploy, full env-var set, smoke test green, email delivery verified end-to-end via SendGrid Domain Authentication on paciolus.com, first Neon user landed |
| 2026-04-09 | **Phase 2 complete** — PR #67 merged (45 commits, Sprints 570–593 + hotfixes + 5 pre-flight fixes), all 21 CI checks green, merge commit `84fbc90` |
| 2026-04-09 | SendGrid Domain Authentication for `paciolus.com` verified — 4 DNS records added to Vercel (em8369 CNAME, s1/s2 DKIM CNAMEs, _dmarc TXT with `p=none`), propagated in under 2 min, SendGrid verify succeeded on first click |
| 2026-04-09 | CI gate resolution on PR #67 — ruff auto-fix, OpenAPI snapshot regen, Jest coverage threshold recalibration, 4 ESLint errors resolved (commits `c275edd` + `c015bf8`) |
| 2026-04-09 | Alembic migration collision + multi-head merge fixes committed to working branch (commits `4c25ac2` + `e8c289e`) |
| 2026-04-09 | `DB_TLS_OVERRIDE=NEON-POOLER-PGSSL-BLINDSPOT:2026-05-09` set — temporary bypass for Neon pooled endpoint's `pg_stat_ssl` blind spot (proper fix tracked as open follow-up) |
| 2026-04-08 | Post-deploy smoke test script `scripts/smoke_test_render.sh` added (commit `0f83273`) |
| 2026-04-08 | Branch audit baseline captured: 1,751 frontend tests + 7,361 backend tests, 0 failures |
| 2026-04-08 | Launch infrastructure plan original draft — this document's phase-based rewrite |
| 2026-03-23 | Infrastructure decisions recorded: Grafana Loki (SIEM), pgBackRest→S3 (DR), AWS Secrets Manager (secrets backup) |
| 2026-03-23 | CODEOWNERS updated to `@Paciolus` (was `@paciolus/security-leads`) |

---

*Last revised: 2026-04-24. Stale action-map dates replaced with a compact "Remaining launch path" block. Phase 1 follow-ups collapsed to DMARC only (other five landed 2026-04-22/23 and are recorded in the Completed table). R2 Backlog Blocker collapsed to a resolved summary — only Phase 4.4 pg_dump remains as a consumer.*
