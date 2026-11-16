# CEO Action Items

> **Single source of truth for every action required to launch Paciolus.**
> Top-to-bottom execution order. Each phase's exit criteria must be met before the next phase starts.

**Status as of 2026-10-20.** Your next actions are items 1–4 under "Remaining launch path" below, and the full sequencing lives in [`reports/next-actions-2026-10-20.md`](../reports/next-actions-2026-10-20.md) (readable: https://claude.ai/code/artifact/cdbdd9eb-3039-44cf-a97b-23bc5c598543).

**What changed between 2026-04-24 and now — read this before working the checklists below.**

- **The repo was dormant 2026-05-01 → 2026-10-19, and production was down for most of it.** Every backend endpoint returned HTTP 500 from roughly 2026-05 because two faults compounded: `AUDIT_CHAIN_SECRET_KEY` was never set on Render (so Sprint 768's deploy exited 1 at startup while Render kept serving the old image, hiding it), and the Upstash Redis host stopped resolving (500ing every rate-limited route, health probes included). Both fixed 2026-10-19; Redis moved to Render Key Value in the same region. Production is live and verified.
- **The lesson that cost five months: a failed Render deploy is invisible from outside.** After any merge, confirm the live deploy SHA equals `main`. `scripts/latest_live_deploy_sha.py` and `.github/workflows/uptime-check.yml` now automate it — the drift probe needs a `RENDER_API_KEY` repo secret, which does not exist yet (the repo has **no secrets at all**).
- **Two decisions are settled — do not re-open them.** (a) The review gate was removed from `main`; all 12 required status checks stay, so CI is now the real unbypassed gate. (b) The off-provider `pg_dump` → R2 backup **ships before launch** — Neon PITR alone is not sufficient, because the database does persist auditor workpaper content. See [`EXECUTIVE_BLOCKERS.md`](EXECUTIVE_BLOCKERS.md) → Resolved Decisions.
- **Order correction to Phase 4:** do **4.3 (custom domain) before 4.1 (Stripe)**, or point the Stripe webhook at the `onrender.com` URL. Phase 4.1 below tells you to configure the webhook at `https://api.paciolus.com/billing/webhook`, and that host currently 404s — a signing secret configured against a dead endpoint breaks every webhook silently.
- **The catalog is 18 tools, not 12.** Phase 3's checklist below still lists 12 with their old per-tool test counts; Sprint 784 corrects the count across the docs. Exercise all 18.

**Historical status (2026-04-24):** **Phases 1 and 2 complete.** Production live at https://paciolus.com on Render Standard + Neon Launch Postgres + Upstash Redis + Sentry + SendGrid Domain Authentication. Post-Phase-1 infra hardening has extended the foundation: `DB_TLS_OVERRIDE` cleared 2026-04-23 (Sprint 673), Neon password rotated 2026-04-22, orphan Render Postgres deleted 2026-04-22, SendGrid Single Sender revoked 2026-04-22, R2 buckets provisioned 2026-04-23 (unblocks Phase 4.4 backups and landed Sprint 611 ExportShare migration same day), Sprint 716 Loki log aggregation deployed 2026-04-24. Sentry integration verified by live traffic (Sprint 711 bugs surfaced in the process).

**Your next action (2026-10-20):** send Terms + Privacy to counsel — it is the longest lead item and a hard launch blocker — and get 5–10 practising CPAs through the demo and free tier (Sprint 781), which is what ranks the four remaining accounting gaps. Phase 3 self-validation continues in parallel against all **18** tools, 18 memo PDFs + 3 report PDFs, the engagement layer, export sharing, admin dashboard and bulk upload on https://paciolus.com. File bugs as you find them; I'm on standby.

**Ongoing monthly cost after launch:** ~$44/mo (Render Standard $25 + Neon Launch ~$19 + free tiers for Redis / Sentry / SendGrid). Stripe transaction fees on actual revenue.

---

## 📋 Remaining launch path

Three gates left between here and announcement. The code is launch-ready; the gating path is CEO calendar + legal sign-off.

0. **Start today, in parallel, because they have the longest lead and no engineering dependency:** send Terms + Privacy to counsel ([4.2](#42-legal--policy-placeholders)), add the Security Policy §12 phone, read the `waitlist_signups` count, and start Sprint 781 CPA validation. Nothing in the engineering tracks is waiting on them, and launch is.
1. **[Phase 3](#phase-3--functional-validation) — Functional Validation (CEO).** Full checklist below. Exit: no open P0/P1 bugs, memory headroom confirmed under bulk load.
2. **[Phase 4.1](#41-stripe-production-cutover) + [4.2](#42-legal--policy-placeholders) — Stripe live cutover + legal placeholders (CEO + counsel).** Stripe live keys on Render/Vercel, real-money smoke test, legal counsel sign-off on Terms + Privacy.
3. **[Phase 4.3](#43-custom-domain)–[4.5](#45-go-live-smoke-test) — Domain, backups, go-live (CEO provides creds, I run backups setup).** Custom domain + DNS, pg_dump cron to `paciolus-backups`, 24h go-live monitor, launch announcement.

**Website claims (2026-11-14):** when Sprint 863's counsel draft is ready, send it with the Terms + Privacy package above — it corrects "not written to disk", the 24 h / 48 h share-link split, "encrypted", summary retention and the preview-cache scope in the Privacy Policy, Terms and Security Policy. Nothing merges without counsel sign-off. See `tasks/todo.md` Sprint 863.

**DMARC tightening** (non-blocking): move `_dmarc.paciolus.com` from `p=none` to `p=quarantine` ~2 weeks after the first real-money Stripe transaction confirms deliverability holds. I'll flag.

---

## ⚖️ Claims review — decisions and actions (2026-10-24)

The legal-and-security claims review (https://claude.ai/artifact/MFTYHezjA4zakoiKwgnNb2; full detail in `reports/claims-review-2026-10-24.md`) is lined up as Sprints 840–845 in `tasks/todo.md`.

**Decided:** counsel reviews the Terms of Service, Privacy Policy and DPA once the website is finalized. Factual corrections to those pages happen now, without waiting.

**Your decisions (defaults in brackets are what the next session will use unless you say otherwise):**
1. Storage positioning — [Option B: plain description + "what we keep" list; drop "Zero-Storage" as a promise].
2. Refund policy — 30-day money-back, or no partial-period refunds? [ask — no default]
3. ~~Legal entity~~ — **DECIDED 2026-11-14: Paciolus LLC.** Live surfaces corrected (Terms, footer).
4. Repository visibility — private, or public with rewritten compliance docs? [ask; recommend private]
5. Product line — [“Diagnostic Intelligence for Financial Professionals”], “Audit Analytics”, or keep “Audit Intelligence”?
6. Support promise — [“Email support; we aim to reply within 1–2 business days” for every tier].
7. Verify ISA 315: does it prescribe the 4×4 inherent × control matrix the composite-risk tool attributes to “Appendix 1”? (Sprint 843 H12) — **Sprint 843 relabelled it as a Paciolus convention** (no matrix in ISA 315 as far as engineering can tell); confirm, or tell us the paragraph and we restore the citation.

**Verify in your consoles:** Neon region and PITR window; Render service region; an R2 lifecycle rule deleting `shares/` after ≤2 days; Sentry DSN set in production and its retention; whether Loki is enabled (Grafana Labs would be an unlisted processor); Render log retention; MFA on GitHub, Render, Vercel, Stripe, Sentry, Neon, Cloudflare and SendGrid; whether provider DPAs/SCCs were accepted; `JWT_EXPIRATION_MINUTES` on Render; after Sprint 851 deploys, set `TRUSTED_PROXY_IPS` to the range Render's proxy connects from (ask Render support) and never set `FORWARDED_ALLOW_IPS='*'` (the 851 code fix itself shipped without this); TLS minimum on Vercel/Render; whether help@, privacy@ and security@ mailboxes exist.

**Security review 2026-10-27 — decisions** (detail: Sprint 853 in `tasks/todo.md`; tracker: https://claude.ai/artifact/6A6odNhC1hZSS5BM1WbcdN):
1. ~~Do clients belong to the firm or the individual?~~ **Decided 2026-11-16: the firm** — a client whose creator belongs to a firm today becomes that firm's; one whose creator has no firm stays personal. (M7)
2. ~~When joining a firm, does a user choose whether to bring their existing clients?~~ **Decided 2026-11-16: no — joining or leaving a firm never moves records.** (M7)
3. ~~Should deleting and archiving be owner/admin-only, and removing an admin owner-only?~~ **Decided 2026-11-16: yes** (members still create and edit). (L12)
4. Logout window: add `sessions_revoked_at`, or accept up to 15 minutes of access-token life after logout? [recommend: add it] (L3, Sprint 847)

**At website-final:** one counsel review of the Terms, Privacy Policy and DPA as contracts (liability, arbitration, governing law, refunds, auto-renewal disclosure for your state), plus any founder-CPA marketing copy against your state board's rules.

## Phase 3 — Functional Validation

**Owner: you for exercising the app; me on standby for bug fixes.**

The goal is to catch anything broken in normal usage before you start charging real money.

- [ ] Run all **18 audit tools** against a realistic sample trial balance. File bugs for any abnormal output. Canonical list: [`backend/tools_registry.py`](../backend/tools_registry.py).
  - JE (19 tests), AP (14), Payroll (13), Revenue (18), AR Aging (12), Fixed Assets (11), Inventory (10), Bank Rec, Three-Way Match, Multi-Period TB, TB Diagnostics, Statistical Sampling, Segregation of Duties, Intercompany Elimination, W-2/W-3 Reconciliation, Form 1099 Preparation, Book-to-Tax Reconciliation, Cash Flow Projector
  - Multi-Currency Conversion is a side-car validation layer, **not** one of the 18 — exercise it, but it has no tool page of its own
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

> **Important context (added 2026-04-24):** Stripe **test mode** is currently at Pricing v2 (Sprint 439 — Solo $50/mo, single graduated seat add-on). The code is at Pricing v3 (Phase LXIX, Sprints 449–476 — Solo $100/mo, flat per-tier seat pricing). Phase 4.1 is therefore **a fresh build of live mode at v3**, not a mirror of test mode. After cutover, all test-mode prices can be archived as cleanup.

- [ ] **Customer Portal** (Stripe Dashboard → Settings → Billing → Customer Portal — works in live or test mode, settings carry over): enable payment-method updates, invoice history, cancel-at-period-end *(may already be configured from Sprint 439)*
- [ ] **Create live-mode products and prices at Pricing v3.** Build fresh — do not mirror test mode. **4 products, 10 prices, 2 coupons:**
  - **Paciolus Solo** — 2 prices: `$100/mo`, `$1,000/yr` (both flat)
  - **Paciolus Professional** *(Stripe currently labels this "Team" — rename when creating live)* — 2 prices: `$500/mo`, `$5,000/yr` (both flat)
  - **Paciolus Enterprise** *(Stripe currently labels this "Organization" — rename when creating live)* — 2 prices: `$1,000/mo`, `$10,000/yr` (both flat)
  - **Paciolus Professional Seat Add-On** — 2 prices: `$65/mo`, `$650/yr` (both flat — **not graduated**)
  - **Paciolus Enterprise Seat Add-On** — 2 prices: `$45/mo`, `$450/yr` (both flat — **not graduated**)
  - **2 coupons** mirroring test mode: `MONTHLY_20_3MO` (20% off first 3 months), `ANNUAL_10_1YR` (10% off first annual invoice)
- [ ] **Render env vars** → set the live secret key plus all 10 price IDs (see Appendix A Stripe table for full list):
  - `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` (live values)
  - 6 base plan price IDs: `STRIPE_PRICE_{SOLO,PROFESSIONAL,ENTERPRISE}_{MONTHLY,ANNUAL}`
  - 4 seat add-on price IDs: `STRIPE_SEAT_PRICE_{PRO,ENT}_{MONTHLY,ANNUAL}`
  - 2 coupon IDs: `STRIPE_COUPON_MONTHLY_20`, `STRIPE_COUPON_ANNUAL_10`
- [ ] **Vercel env vars** → set any `NEXT_PUBLIC_STRIPE_*` IDs the frontend reads directly (publishable key, etc.)
- [ ] Stripe Dashboard → Developers → Webhooks → configure endpoint → copy the signing secret into `STRIPE_WEBHOOK_SECRET`. **`api.paciolus.com` 404s as of 2026-10-20** (Phase 4.3 has not run), so either do 4.3 first and use `https://api.paciolus.com/billing/webhook`, or use `https://paciolus-api.onrender.com/billing/webhook` now and re-point the endpoint after the domain exists. Do not configure it against the custom domain before that domain resolves — the webhook will fail silently.
- [ ] **Run the Sprint 780 price-parity preflight FIRST**, as soon as the live price IDs are set on Render and before any real card is used.

  It reads the ten `STRIPE_PRICE_*` / `STRIPE_SEAT_PRICE_*` env vars, so it has to run **where those variables exist**. Setting them on Render does not put them in your local shell — run it locally with only the secret key exported and it will report every price ID as unset, and `--require-all` will then fail for the wrong reason.

  **Either** run it on the instance, where the live env is already present:
  ```
  ssh srv-d6ie9l56ubrc73c7eq2g@ssh.virginia.render.com
  cd /app && python ../scripts/stripe_price_parity_preflight.py --require-all
  ```
  **or** export the same ten values locally first (copy them from Render → paciolus-api → Environment), then:
  ```
  STRIPE_SECRET_KEY=sk_live_... python scripts/stripe_price_parity_preflight.py --require-all
  ```
  It retrieves every one of the ten Price objects and asserts the amount Stripe will charge equals the amount `billing/price_config.py` intends and the pricing page displays — plus currency, billing cadence, active state, and that no test-mode price is wired into live. **Exit 0 or do not continue.** Capture the output as launch-dossier evidence. This is the check that did not exist when test mode drifted to v2 prices while the page said v3.
- [ ] **Run the Sprint 719 preflight runner** second, before flipping live env vars, against **the same endpoint you configured above** — `scripts/stripe_live_preflight.sh https://api.paciolus.com/billing/webhook` once 4.3 has run, or `scripts/stripe_live_preflight.sh https://paciolus-api.onrender.com/billing/webhook` if you took the onrender path. The runner bails on the first non-200, so pointing it at the custom domain before that domain resolves fails the gate for a reason unrelated to Stripe. Fires every event type the webhook handler supports; bails on the first non-200. **Do NOT proceed if any event fails.** Capture the script output as evidence in the launch dossier.
- [ ] **Verify the production-mode Stripe-secret format guard**: after setting live env vars on Render, confirm Render boot logs do NOT contain `STRIPE_SECRET_KEY is a TEST-mode key` or any `_test_` rejection. Sprint 719 added a startup hard-fail for this misconfiguration; if the boot succeeds, the format check passed.
- [ ] Sign `tasks/archive/pricing-launch-readiness.md` Section 7 (Code Owner + CEO lines) → mark **GO**
- [ ] Manual test: click "Manage Billing" from `/settings/billing` → confirm it opens the Stripe Customer Portal
- [ ] Real-money smoke test: subscribe to **Solo monthly** (lowest tier — now $100) with a real card → confirm the subscription appears in Stripe Dashboard and in the admin dashboard → cancel → confirm webhook delivery → refund the charge
- [ ] Monitor Stripe Dashboard → Developers → Webhooks for 24 hours → confirm delivery ≥99%
- [ ] **Post-cutover cleanup** (after live mode is verified): bulk-archive all test-mode prices in Stripe Dashboard. Test mode is now decoupled from production.

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

> **Reclassified 2026-10-19: this is a pre-launch blocker, not belt-and-suspenders.** The first version of the decision deferred it on the premise that Zero-Storage meant no client financial data was persisted. That premise was wrong — `diagnostic_summaries` holds aggregate F/S totals, `uncorrected_misstatements` holds account names with DR/CR and amounts, and `analytical_expectations` holds expected and actual values. That is auditor workpaper content. Scope is **Sprint 778**; the `paciolus-backups` R2 bucket has been provisioned and empty since 2026-04-23.

- [ ] *(I set this up; you confirm the R2 token still works)* Daily `pg_dump` → R2 cron into `paciolus-backups`. Options: Render Cron Job (~$1/mo), GitHub Action (free), or Upstash Scheduled Functions.
- [ ] *(I do this)* Verify the **actual** Neon PITR retention window on the current plan, rather than the figure recorded in `DEPLOYMENT_ARCHITECTURE.md:724`
- [ ] *(I do this)* One real restore drill **per mechanism** — R2 dump and Neon PITR — with schema parity and row counts recorded as evidence. An untested backup is not a backup.
- [ ] *(I do this; needs `RENDER_API_KEY`)* Rewrite `verify_backup_integrity.py` and `dr-test-monthly.yml` against Neon + R2. Both currently query the Render Postgres API for a database deleted on 2026-04-22, and the monthly DR test reports workflow **success** while its own internal verdict is FAIL.
- [ ] **Add 7 GitHub Actions secrets (Sprint 778b code is built; nothing can run until these exist).** GitHub → Settings → Secrets and variables → Actions. Exact names, and where each value comes from (full detail: `docs/runbooks/backup-restore.md` §2):
  - `NEON_BACKUP_DATABASE_URL` — Neon Console → Connect → **Connection pooling OFF** → copy. The host must **not** contain `-pooler` (PgBouncer breaks `pg_dump`; the job refuses it).
  - `R2_BACKUPS_ENDPOINT` — copy from Render `paciolus-api` → Environment (`https://8fd7f43a3458f2ec09d400e0b7a7a5e8.r2.cloudflarestorage.com`).
  - `R2_BACKUPS_BUCKET` — `paciolus-backups`.
  - `R2_BACKUPS_ACCESS_KEY_ID` / `R2_BACKUPS_SECRET_ACCESS_KEY` — copy from Render, or mint a new Object R&W token scoped to `paciolus-backups` (Cloudflare → R2 → Manage R2 API Tokens).
  - `NEON_API_KEY` — Neon Console → Account settings → API keys → Create.
  - `NEON_PROJECT_ID` — Neon Console → project → Settings → General.
  - Then: Actions → *Backup — pg_dump to R2 (Daily)* → Run workflow; then *DR Test (Monthly)* → Run workflow. Until then every backup/DR workflow is red with "UNVERIFIED — missing secret …" — by design.
- [ ] **Heads up:** `backup-integrity-check` (now weekly) and `DR Test (Monthly)` stay red, with one open `dr-failure` issue naming the missing secrets, until the 7 secrets above exist. *(Sprint 778b replaced the misleading "RENDER_API_KEY is not set" reason.)*

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

Code reference: `backend/billing/price_config.py` (Pricing v3, Phase LXIX). 13 vars total.

| Variable | Maps to Stripe price | Notes |
|---|---|---|
| `STRIPE_SECRET_KEY` | n/a | Live secret key from Stripe Dashboard |
| `STRIPE_PUBLISHABLE_KEY` | n/a | Live publishable key |
| `STRIPE_WEBHOOK_SECRET` | n/a | From the webhook endpoint you configure in Stripe |
| `STRIPE_PRICE_SOLO_MONTHLY` | Solo $100/mo | flat |
| `STRIPE_PRICE_SOLO_ANNUAL` | Solo $1,000/yr | flat |
| `STRIPE_PRICE_PROFESSIONAL_MONTHLY` | Professional $500/mo | flat |
| `STRIPE_PRICE_PROFESSIONAL_ANNUAL` | Professional $5,000/yr | flat |
| `STRIPE_PRICE_ENTERPRISE_MONTHLY` | Enterprise $1,000/mo | flat |
| `STRIPE_PRICE_ENTERPRISE_ANNUAL` | Enterprise $10,000/yr | flat |
| `STRIPE_SEAT_PRICE_PRO_MONTHLY` | Professional Seat Add-On $65/mo | flat (was graduated in Sprint 439 — replaced in Phase LXIX) |
| `STRIPE_SEAT_PRICE_PRO_ANNUAL` | Professional Seat Add-On $650/yr | flat |
| `STRIPE_SEAT_PRICE_ENT_MONTHLY` | Enterprise Seat Add-On $45/mo | flat |
| `STRIPE_SEAT_PRICE_ENT_ANNUAL` | Enterprise Seat Add-On $450/yr | flat |
| `STRIPE_COUPON_MONTHLY_20` | n/a | 20%-off-first-3-months coupon ID |
| `STRIPE_COUPON_ANNUAL_10` | n/a | 10%-off-first-annual-invoice coupon ID |

### Leave alone unless you have a reason

`DEBUG`, `JWT_EXPIRATION_MINUTES`, `REFRESH_TOKEN_EXPIRATION_DAYS`, `TRUSTED_PROXY_IPS`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE`, `SENTRY_TRACES_SAMPLE_RATE`, `ENTITLEMENT_ENFORCEMENT`, `SEAT_ENFORCEMENT_MODE`, `DB_TLS_REQUIRED`, `DB_TLS_OVERRIDE`, format flags (`FORMAT_*_ENABLED`), cleanup scheduler intervals.

---

> Completed and decided sections (Phases 1–2, the 2026-10-24 methodology calls, the completed log) were moved verbatim to
> [`archive/ceo-actions-completed-2026-11-15.md`](archive/ceo-actions-completed-2026-11-15.md) on 2026-11-15.
