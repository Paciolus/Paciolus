# CEO Action Items

> **Single source of truth for everything requiring your direct action.**
> Engineering delivers scaffolding; you complete execution.
> Check boxes (`[ ]` → `[x]`) as you complete items, then move to [Completed](#completed).

**Last synchronized:** 2026-02-27 — Sprints 447–458 + all compliance docs audited.

---

## Priority Guide

| Symbol | Meaning |
|--------|---------|
| 🔴 | Hard deadline — missing this blocks SOC 2 or compliance |
| 🟠 | Active — needed for SOC 2 evidence trail, do ASAP |
| 🟡 | Milestone — major business action (billing launch, legal) |
| 🔵 | Decision — blocks an engineering sprint |
| ⚪ | Setup — one-time infrastructure/admin tasks |
| 📅 | Recurring — calendar reminders to set once |

---

## 🟠 SOC 2 Evidence — Complete ASAP

### GPG Commit Signing Setup (Sprint 458 — CC8.6)

**Do in this exact order to avoid locking yourself out of `main`:**

- [ ] Follow **`CONTRIBUTING.md §4 — GPG Commit Signing`** to generate your key and configure git:
  ```bash
  gpg --full-generate-key       # RSA 4096, no expiry, your GitHub email
  git config --global user.signingkey <KEYID>
  git config --global commit.gpgsign true
  gpg --armor --export <KEYID>  # copy output → GitHub → Settings → SSH and GPG keys → New GPG key
  ```
- [ ] Make a test commit and verify the green **Verified** badge appears on GitHub
- [ ] Add your fingerprint row to [`docs/08-internal/gpg-key-registry.md`](../docs/08-internal/gpg-key-registry.md)
- [ ] **Only after** all committers have registered and tested: enable **"Require signed commits"** in GitHub → repository → Settings → Branches → protection rule for `main`
- [ ] Update `SECURE_SDL_CHANGE_MANAGEMENT.md §10.3` table: change `⏳ Pending` to `✅ Enforced — [date]`

---

### Backup Integrity Check — First Run Setup (Sprint 457 — S1.5 / CC4.2)

- [ ] Add **3 GitHub Secrets** (repo → Settings → Secrets and variables → Actions → New repository secret):
  - `RENDER_API_KEY` — your Render personal API token (Settings → API Keys)
  - `RENDER_POSTGRES_ID` — your PostgreSQL service ID (found in Render dashboard URL, e.g. `postgres-abc123`)
  - `DATABASE_URL_READONLY` — optional: a read-only PostgreSQL connection string (skip if no read-only user configured)
- [ ] Trigger the first manual run: GitHub → Actions → **Backup Integrity Check (Monthly)** → **Run workflow**
- [ ] Download the artifact `backup-integrity-YYYYMM` from the workflow run
- [ ] Copy the report file to `docs/08-internal/soc2-evidence/s1/backup-integrity-YYYYMM.txt` and commit
- [ ] Add `dr-failure` label in GitHub Issues (Labels → New label → name: `dr-failure`, color: `#B60205`)

The workflow runs automatically on the 1st of each month after that.

---

### Data Deletion Procedure — End-to-End Test (Sprint 456 — PI4.3 / CC7.4)

### Data Deletion Procedure — End-to-End Test (Sprint 456 — PI4.3 / CC7.4)

- [ ] Provision a test account in a non-production environment (or use an existing staging account you control)
- [ ] Follow Steps 1–10 in [`docs/08-internal/data-deletion-procedure.md`](../docs/08-internal/data-deletion-procedure.md)
  - Use the tracker template (§7) to create `docs/08-internal/deletion-requests/deletion-YYYYMMDD-001.md`
  - Execute the SQL queries against the staging database (or note "test account in production" with care)
  - Verify all row counts return 0 (Step 8)
  - Send test confirmation email to yourself (Step 9)
- [ ] Sign off on the tracker entry
- [ ] Copy the completed tracker file to `docs/08-internal/soc2-evidence/pi4/deletion-YYYYMMDD-001.md`

---

## 🔴 Hard Deadlines

### By 2026-03-31

- [ ] **Q1 Access Review** — log in to all 7 dashboards in order: GitHub → Render → Vercel → PostgreSQL → Sentry → SendGrid → Stripe. Fill in every table row. Sign off.
  - Template: [`docs/08-internal/access-review-2026-Q1.md`](../docs/08-internal/access-review-2026-Q1.md)
  - After signing: copy to `docs/08-internal/soc2-evidence/cc6/access-review-2026-Q1.md`
  - Source sprint: 454 / Control: CC6.1

- [ ] **Q1 Risk Register review** — re-score all 12 risks, update residual ratings, confirm 0 High/Critical remain.
  - File: [`docs/08-internal/risk-register-2026-Q1.md`](../docs/08-internal/risk-register-2026-Q1.md)
  - Source sprint: 451 / Control: CC4.1

---

## 🟠 SOC 2 Evidence — Complete ASAP

### Encryption Verification Screenshots (Sprint 450 — CC7.2)

- [ ] Log into **Render dashboard** → PostgreSQL instance → confirm encryption-at-rest is enabled → screenshot
  - Save to: `docs/08-internal/soc2-evidence/cc7/render-postgres-encryption-202602.png`
- [ ] Log into **Vercel dashboard** → Settings → Storage → confirm no persistent storage attached → screenshot
  - Save to: `docs/08-internal/soc2-evidence/cc7/vercel-no-storage-202602.png`
- [ ] Fill in evidence table in [`docs/08-internal/encryption-at-rest-verification-202602.md`](../docs/08-internal/encryption-at-rest-verification-202602.md) with your name, date, and findings from both screenshots

### Security Training (Sprint 453 — CC2.2)

- [ ] Read all 5 modules in [`docs/08-internal/security-training-curriculum-2026.md`](../docs/08-internal/security-training-curriculum-2026.md) and answer attestation questions (M1–M5; engineers complete all 5, others complete M1/M3/M4/M5)
- [ ] Fill in your row(s) in [`docs/08-internal/security-training-log-2026.md`](../docs/08-internal/security-training-log-2026.md): name, role, module, date, delivery method, sign-off
- [ ] Have all other team members do the same (or fill in their rows yourself after confirming completion)
- [ ] Once all rows complete: copy log to `docs/08-internal/soc2-evidence/cc2/security-training-log-2026.md`

### Weekly Security Review — W09 (Sprint 455 — CC4.2 / C1.3)

- [ ] Run `python scripts/weekly_security_digest.py` (set `METRICS_URL=https://api.paciolus.com/metrics`) — paste output into Section 3 of the review file
- [ ] Log in to Sentry → your org → Issues → filter "Last 7 days" → fill in Section 2 of the review file
- [ ] Search Render logs for `login_failed`, `account_locked`, `csrf_blocked`, `refresh_token_reuse_detected` → fill in Section 4
- [ ] Search Render access logs for `429` responses → fill in Section 5
- [ ] Complete all `[CEO ACTION]` fields in [`docs/08-internal/security-review-2026-W09.md`](../docs/08-internal/security-review-2026-W09.md) and sign off
- [ ] Copy completed file to `docs/08-internal/soc2-evidence/c1/security-review-2026-W09.md`
- [ ] Set Monday 9am UTC recurring calendar reminder for W10 onward

**Due:** 2026-03-01 (end of W09)

---

### Backup Restore Test (Sprint 452 — S3.5)

- [ ] Provision an isolated PostgreSQL test instance (Render free tier or local Docker — **not production**)
- [ ] Follow the 10-step procedure in [`docs/08-internal/dr-test-2026-Q1.md`](../docs/08-internal/dr-test-2026-Q1.md) — all SQL queries are pre-written; fill in results as you go
- [ ] Tear down the test instance after completion (documented in Step 11)
- [ ] Copy the signed, completed report to `docs/08-internal/soc2-evidence/s3/dr-test-2026-Q1.md`

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

## ⚪ One-Time Infrastructure Setup

These are referenced in policy/IRP documents but not yet configured.

### PagerDuty / On-Call Rotation
> Referenced in: IRP §3.3, BCP/DR §9, ACCESS_CONTROL_POLICY §4.2, SECURE_SDL §13.3
- [ ] Create a PagerDuty account (or equivalent: OpsGenie, incident.io)
- [ ] Configure escalation policy: P0/P1 → phone + push; P2/P3 → Slack
- [ ] Set up on-call rotation schedule (at minimum: primary + secondary for P0/P1 escalation)
- [ ] Connect Sentry alerts → PagerDuty (P0/P1 thresholds)
- [ ] Connect Prometheus Alertmanager → PagerDuty (if Alertmanager is wired)
- [ ] Update `Phone: [To be established]` in SECURITY_POLICY.md §12 with PagerDuty phone number
- [ ] Update INCIDENT_RESPONSE_PLAN.md §12 contact table with actual on-call contact method

---

## 🔵 Decisions Required (Each Blocks a Sprint)

Engineering cannot begin these sprints until you pick an option. Read the sprint in `todo.md`, pick one, then the sprint starts.

- [ ] **Sprint 463 — SIEM approach**: A: Grafana Loki (lightweight, OSS), B: Elastic Stack (powerful, higher ops cost), C: Datadog (SaaS, Zero-Storage compliant setup needed), D: Defer — use Prometheus/Sentry correlation only
  - Decision: ___________

- [ ] **Sprint 464 — Cross-region DB replication tier**: Evaluate Render's options — read replica vs. cross-region standby vs. pgBackRest to S3. Check Render pricing first.
  - Decision: ___________

- [ ] **Sprint 466 — Secrets vault secondary backup location**: AWS Secrets Manager (separate account), encrypted offline store (e.g., encrypted USB in safe), or secondary cloud provider
  - Decision: ___________

- [ ] **Sprint 467 — Penetration test vendor**: Select a CREST/OSCP-certified firm. Get 3 quotes. Scope: auth flows, CSRF/CSP, rate limiting, API authorization, file upload, JWT, billing. Target: Q2 2026 per SECURITY_POLICY.md §7.2.
  - Decision: ___________

- [ ] **Sprint 468 — Bug bounty / VDP approach**: Public program (HackerOne/Bugcrowd — $$), private invite-only (moderate), enhanced VDP with `security.txt` only (minimal)
  - Decision: ___________

- [ ] **Sprint 469 — SOC 2 auditor + observation window**: Get quotes from 3 CPA firms with SaaS SOC 2 experience. Decide on auditor and observation window start date.
  - Decision: ___________

---

## 📅 Recurring Calendar — Set These Once

### Summary Table

| Reminder | Frequency | Next | Controls |
|----------|-----------|------|---------|
| Encryption at-rest verification (Render + Vercel screenshots) | Monthly — 1st of month | 2026-03-01 | CC7.2 |
| Risk register review (re-score all 12 risks) | Quarterly — last day of Mar/Jun/Sep/Dec | 2026-03-31 | CC4.1 |
| Quarterly access review (all 7 dashboards) | Quarterly — last day of Mar/Jun/Sep/Dec | 2026-03-31 | CC6.1 |
| Weekly security event review | Weekly — every Monday | 2026-03-02 | CC4.2 / C1.3 |
| Semi-annual backup restore test | Jun 30 + Dec 31 | 2026-06-30 | S3.5 |
| Semi-annual tabletop exercise (IRP walkthrough) | Jun 30 + Dec 31 | 2026-06-30 | CC9.1 |
| Annual security training renewal (all team members) | January 1 | 2027-01-01 | CC2.2 |
| Annual penetration test | Q2 each year | 2027-04-01 | CC4.3 |
| Secrets vault sync verification | Every 90 days (after Sprint 466) | After Sprint 466 | CC7.3 |

> **Tip:** Items in rows 2 and 3 (risk register + access review) share the same dates — create one quarterly calendar block for both.

### 2026 Calendar At-a-Glance

```
MARCH 2026
  01  🔁 Monthly: Encryption at-rest verification screenshots
  31  🔴 Q1 Risk Register review                          ← DEADLINE
  31  🔴 Q1 Access Review (all 7 dashboards)              ← DEADLINE

APRIL 2026
  01  🔁 Monthly: Encryption at-rest verification
  —   🔵 Sprint 467: Pen test vendor selected + engaged (Q2 target)

MAY 2026
  01  🔁 Monthly: Encryption at-rest verification

JUNE 2026
  01  🔁 Monthly: Encryption at-rest verification
  30  🔁 Q2 Risk Register review
  30  🔁 Q2 Access Review (all 7 dashboards)
  30  🔁 Semi-annual backup restore test (fill dr-test-2026-Q2.md)
  30  🔁 Semi-annual tabletop exercise (P0 scenario walkthrough with team)

JULY 2026
  01  🔁 Monthly: Encryption at-rest verification

AUGUST 2026
  01  🔁 Monthly: Encryption at-rest verification

SEPTEMBER 2026
  01  🔁 Monthly: Encryption at-rest verification
  30  🔁 Q3 Risk Register review
  30  🔁 Q3 Access Review (all 7 dashboards)

OCTOBER 2026
  01  🔁 Monthly: Encryption at-rest verification

NOVEMBER 2026
  01  🔁 Monthly: Encryption at-rest verification

DECEMBER 2026
  01  🔁 Monthly: Encryption at-rest verification
  31  🔁 Q4 Risk Register review
  31  🔁 Q4 Access Review (all 7 dashboards)
  31  🔁 Semi-annual backup restore test (fill dr-test-2026-Q4.md)
  31  🔁 Semi-annual tabletop exercise

JANUARY 2027
  01  🔁 Annual: Security training renewal — all team members complete M1–M5
  01  🔁 Create new security-training-log-2027.md
```

### Weekly (every Monday)
> Start this cadence once Sprint 455 (Weekly Security Event Review) is complete.
- Review Sentry error rate trends + any P0/P1 alerts
- Review Prometheus: rate limit spikes, login failure counts, CSRF failures
- Review auth events: lockouts, new accounts, password resets
- Sign weekly review file → `docs/08-internal/soc2-evidence/c1/security-review-YYYY-WNN.md`

---

## ✅ Completed

Move items here with date when done.

| # | Item | Completed |
|---|------|----------|
| — | *(none yet)* | |

---

## How This File Works

- **Engineering** adds new items at the end of each sprint (post-sprint checklist step)
- **You** work top-to-bottom: 🔴 → 🟠 → 🟡 → ⚪ → 🔵 → 📅
- When done: check the box, move to ✅ with the date
- This file is version-controlled — the action history is auditable
- **Next sync:** After Sprint 455 (Weekly Security Review) completes

---

*Synchronized with: `tasks/todo.md` active phase + `docs/04-compliance/` full audit*
*Sprints covered: 447–458 + legal docs + IRP + BCP/DR + SECURITY_POLICY*
