# CEO Action Items

> **Single source of truth for every action required to launch Paciolus.**
> Top-to-bottom execution order. Each phase's exit criteria must be met before the next phase starts.

**Status as of 2026-04-09 (evening):** **Phases 1 and 2 are complete.** `paciolus-api` is running on Render Standard (2 GB / 1 CPU, $25/mo), serving the Sprint 593-era merged backlog at https://paciolus.com. Neon Launch Postgres (us-east-1 pooled) + Upstash Redis + Sentry + SendGrid Domain Authentication on paciolus.com all wired and verified. Register/login/logout/cookie auth and end-to-end email delivery all confirmed working. Full detail archived in `tasks/archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md`.

**Your next action:** Phase 3 — Functional Validation. Exercise the 12 testing tools, engagement layer, PDF memos, admin dashboard, and bulk upload on https://paciolus.com and file any bugs found. I'm on standby for bug fixes.

**Launch ETA:** ~3 weeks from today.

**Ongoing monthly cost after launch:** ~$44/mo (Render Standard $25 + Neon Launch ~$19 + free tiers for Redis / Sentry / SendGrid). Stripe transaction fees on actual revenue.

---

## 📋 This Week's Action Map — Council Review 2026-04-16

> **Council verdict:** Code is launch-ready. Gating path is your calendar, not engineering. Ship on ~3-week ETA (Path A). See conversation transcript for the 8-agent breakdown and tradeoff map.

**Recommended order — approximately three focused afternoons:**

### Afternoon 1 (tomorrow, 2026-04-17): Phase 3 — Functional Validation
Open [Phase 3](#phase-3--functional-validation) and work the checklist top-to-bottom on https://paciolus.com. Specifically:
- [ ] All 12 testing tools against one realistic sample TB (file bugs as you find them, I fix them)
- [ ] All 18 memo PDFs + 3 report PDFs back-to-back on a single engagement (watch Sentry for memory warnings)
- [ ] Engagement layer end-to-end (create → materiality → diagnostics → follow-ups → workpaper index → ZIP → completion gate)
- [ ] Export sharing flow (create share → incognito access → passcode → revoke → verify revocation)
- [ ] Admin dashboard (orgs, drill-down, impersonation read-only, audit log)
- [ ] Bulk upload with 5+ TBs (Enterprise tier — watch Render memory graph)
- [ ] Fire a deliberate broken endpoint to confirm a Sentry event actually lands in the dashboard *(Phase 1 follow-up, folds in here)*

**Exit:** No open P0/P1 bugs. Memory headroom observed under bulk load. Sentry event confirmed visible.

### Afternoon 2 (~next week): Phase 4.1 — Stripe Live Cutover + Legal Placeholders
- [ ] Generate/confirm Stripe live-mode secret key, publishable key, and webhook signing secret. Set on Render + Vercel env vars.
- [ ] Stripe Dashboard configuration per [Phase 4.1](#41-stripe-production-cutover) (graduated pricing confirmed, Customer Portal enabled, products/prices/coupons mirrored from test mode)
- [ ] Sign `tasks/pricing-launch-readiness.md` Section 7 → mark **GO**
- [ ] Real-money smoke test: Solo monthly with real card → subscribe → webhook delivered → cancel → refund
- [ ] Legal placeholders in [Phase 4.2](#42-legal--policy-placeholders) — fill business address, registered agent, DPO/EU-rep decision, effective dates, security emergency phone. Counsel sign-off on Terms + Privacy before go-live.

### Afternoon 3 (~week 3): Phase 4.3–4.5 — Domain, Backups, Go-Live
- [ ] Provision R2/S3 bucket (serves both Phase 4.4 pg_dump backups AND Sprint 611 ExportShare migration — [Backlog Blockers](#backlog-blockers--provisioning-gates))
- [ ] Custom domain + DNS per [Phase 4.3](#43-custom-domain)
- [ ] I run the pg_dump restore round-trip on your bucket ([Phase 4.4](#44-backups))
- [ ] Go-live smoke test from custom domain ([Phase 4.5](#45-go-live-smoke-test)) — 24h monitor of Sentry + Render logs + Stripe webhook delivery ≥99%
- [ ] **Launch announcement**

### Parallel Engineering Track (I own — no CEO action)
- **Sprint 673:** `DB_TLS_OVERRIDE` proper fix (pooler-aware `pg_stat_ssl` skip). 23-day fuse before 2026-05-09 override expiry. Lands before your Phase 4.3 work starts so it doesn't collide with launch week. Tracked in [`tasks/todo.md`](todo.md) Active Phase.
- **DMARC tightening:** I'll flag when to move `_dmarc.paciolus.com` from `p=none` to `p=quarantine` (~2 weeks after your first real-money transaction confirms deliverability holds).

### Guardian's Production-Behavior Verification Checklist
Already embedded in the phases above — listed here explicitly so nothing slips:
1. Stripe real-card E2E (Phase 4.1) ✅ in map
2. Sentry verify event lands in dashboard (Afternoon 1) ✅ in map
3. pg_dump restore round-trip (Phase 4.4) ✅ in map
4. Bulk upload 5+ TBs (Phase 3) ✅ in map
5. 24h webhook delivery ≥99% (Phase 4.5) ✅ in map

---

## Phase 1 — Restore Login ✅ DONE 2026-04-09

Render Standard deploy live. Neon (us-east-1 pooled) + Upstash Redis + Sentry wired. SendGrid Domain Authentication for `paciolus.com` verified after an initial DMARC bounce on the `@gmail.com` sender — DNS records (SPF/DKIM/DMARC) added to Vercel, propagated in under 2 minutes, and verified by SendGrid. Email verification flow confirmed end-to-end in Gmail inbox. Smoke test green (health, CSRF, register with HttpOnly cookies, /auth/me, wrong-password, logout). First user landed in the fresh Neon DB.

**Full detail, operational learnings, and exact commands archived in [`tasks/archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md`](archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md).**

### Phase 1 open follow-ups (non-blocking, scheduled during later phases)

- [x] **`DB_TLS_OVERRIDE` removed 2026-04-23.** Sprint 673 pooler-aware pg_stat_ssl skip shipped via the 2026-04-22 password-rotation redeploy; CEO-initiated env-var delete at 10:26 UTC 2026-04-23 went live at 10:28 UTC. Fresh worker startup logs on instance `csfxr` all show `tls=pooler-skip`; zero `DB_TLS_OVERRIDE` warnings in post-deploy logs; 2026-05-09 fuse cleared. Full chain of custody in Sprint 673 Review.
- [ ] **Upgrade DMARC policy** — currently `p=none` (monitoring only). After ~2 weeks of successful delivery to Gmail and other major providers, tighten to `p=quarantine` or eventually `p=reject` for stronger spoofing protection. Update the `_dmarc.paciolus.com` TXT record in Vercel DNS.
- [x] **Sentry test event** — verified 2026-04-22. Production was already capturing real events (9+ unresolved issues in dashboard from `cleanup_scheduler`, `/auth/verification-status`, `/audit/trial-balance`, `/audit/preflight`). No deliberate test event needed; the integration is fully validated by live traffic. **Bonus finding:** Two P1 bugs surfaced (verification-status datetime TypeError + cleanup_scheduler failures, ~670 events combined). Captured as Sprint 711 in `tasks/todo.md`.
- [x] **Revoke SendGrid Single Sender Verification for `comcgee89@gmail.com`** — done 2026-04-22. Domain Authentication on `paciolus.com` is now the sole sending path.
- [x] **Delete old Render Postgres `paciolus-db`** — done 2026-04-22. Was actually a Basic-1gb paid plan (not free tier as the original note claimed), holding 85 MB of orphaned pre-Neon data with 0 open connections and a separate `paciolus_user` credential. Verified `paciolus-api` `DATABASE_URL` points to Neon (`neondb_owner@ep-crimson-smoke-an4uy1gh-pooler...`) before deletion. Stops a ~$7-19/mo Basic-1gb bill that was burning on a DB the backend doesn't use.
- [x] **Neon DB password rotation** — done 2026-04-22. The DATABASE_URL plaintext rendered in a screenshot tool result during the orphan-DB investigation; rotated `neondb_owner` password in Neon, updated Render `DATABASE_URL` env var, deploy `937997a` went green at 4:49 PM, login on paciolus.com smoke-tested clean. (Side effect: this redeploy also shipped PR #93 — Sprints 703–709 typography + design refresh — to production for the first time, since "Environment updated" deploys always pull latest main.)

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

### Object store bucket (R2 or S3) — PROVISIONED 2026-04-23

- [x] **Provisioned 2026-04-23 on Cloudflare R2.** Two buckets (for least-privilege isolation between the two consumers), both ENAM (us-east-1-adjacent), Standard storage class, public access disabled:
  1. `paciolus-backups` — will back the **Phase 4.4** daily `pg_dump` target.
  2. `paciolus-exports` — will back the **Sprint 611 ExportShare object store migration** (removes up-to-50-MB blobs from `backend/export_share_model.py:43` / Neon Postgres).
- [x] **Two scoped Account API tokens, each Object Read & Write on exactly one bucket.** `paciolus-backups-rw` and `paciolus-exports-rw` (the latter rolled mid-provisioning after a screenshot-leak of its initial secret — see `tasks/lessons.md` for the pattern, fix, and prevention rule). The original secrets never reached Render's persistent store; only the rolled values saved.
- [x] **8 env vars wired to Render `paciolus-api` (deploy live 2026-04-23 12:11 UTC):** `R2_{BACKUPS,EXPORTS}_{BUCKET,ENDPOINT,ACCESS_KEY_ID,SECRET_ACCESS_KEY}`. Env var count 19 → 27. `/health` returned HTTP 200 in <300ms across 9 polls spanning the rolling deploy — zero service disruption. Shared S3 endpoint: `https://8fd7f43a3458f2ec09d400e0b7a7a5e8.r2.cloudflarestorage.com`.
- **Consumers (no code wired yet — vars sit unused until these land):** Sprint 611 ExportShare migration (unblocked), Phase 4.4 pg_dump cron (unblocked). Both can proceed without further CEO action on R2.

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

> One-line milestone record. Full Phase 1 & 2 detail lives in [`tasks/archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md`](archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md).

| Date | Milestone |
|---|---|
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

*Last revised: 2026-04-09 (evening). Phases 1 and 2 collapsed to brief summaries after full archival to `tasks/archive/ceo-phases-1-2-restore-login-and-backlog-merge-2026-04-09.md`. Phase 3 (Functional Validation) is now the active phase. Phase 1 open follow-ups (DB_TLS_OVERRIDE, DMARC tightening, Sentry test event, SendGrid single-sender cleanup, old Postgres delete) preserved inline for tracking.*
