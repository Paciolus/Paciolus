# CEO Action Items

> **This file is the single source of truth for everything that requires your direct action.**
> Engineering delivers the scaffolding; you complete the execution.
> Update status inline (`[ ]` → `[x]`) as you complete items.

**Last updated:** 2026-02-27

---

## 🔴 Hard Deadlines

Items with a compliance or business deadline. Missing these blocks SOC 2 evidence or billing launch.

| # | Action | Due | Sprint | Where to act |
|---|--------|-----|--------|-------------|
| 1 | **Execute Q1 Access Review** — log in to all 7 dashboards (GitHub → Render → Vercel → PostgreSQL → Sentry → SendGrid → Stripe) and fill in every table | 2026-03-31 | 454 | [`access-review-2026-Q1.md`](../docs/08-internal/access-review-2026-Q1.md) |
| 2 | Copy signed access review to evidence folder | 2026-03-31 | 454 | → `docs/08-internal/soc2-evidence/cc6/access-review-2026-Q1.md` |
| 3 | **Q1 Risk Register review** — re-score all 12 risks, update residuals | 2026-03-31 | 451 | [`risk-register-2026-Q1.md`](../docs/08-internal/risk-register-2026-Q1.md) |

- [ ] Item 1 complete
- [ ] Item 2 complete
- [ ] Item 3 complete

---

## 🟠 SOC 2 Evidence — Complete ASAP

These items generate evidence for the SOC 2 observation window. The sooner they're done, the longer the evidence trail before the audit.

### Evidence Screenshots (Sprint 450 — CC7.2 / S1.2)

| # | Action | File to produce |
|---|--------|----------------|
| 4 | Log into **Render dashboard** → confirm PostgreSQL instance shows encryption-at-rest enabled → take screenshot | `docs/08-internal/soc2-evidence/cc7/render-postgres-encryption-202602.png` |
| 5 | Log into **Vercel dashboard** → confirm no persisted storage exists (or confirm it's encrypted) → take screenshot | `docs/08-internal/soc2-evidence/cc7/vercel-no-storage-202602.png` |
| 6 | Update evidence table in [`encryption-at-rest-verification-202602.md`](../docs/08-internal/encryption-at-rest-verification-202602.md) with findings from screenshots | same file |

- [ ] Item 4 complete
- [ ] Item 5 complete
- [ ] Item 6 complete

### Security Training (Sprint 453 — CC2.2 / CC3.2)

| # | Action | File |
|---|--------|------|
| 7 | Read all 5 training modules + complete attestation questions (M1–M5) | [`security-training-curriculum-2026.md`](../docs/08-internal/security-training-curriculum-2026.md) |
| 8 | Fill in `security-training-log-2026.md` with your name, role, module, completion date, delivery method, sign-off for each module | [`security-training-log-2026.md`](../docs/08-internal/security-training-log-2026.md) |
| 9 | Do the same for every other team member (or have them fill in their own rows) | same file |
| 10 | Copy completed log to evidence folder | → `docs/08-internal/soc2-evidence/cc2/security-training-log-2026.md` |

- [ ] Item 7 complete
- [ ] Item 8 complete
- [ ] Item 9 complete
- [ ] Item 10 complete

### Backup Restore Test (Sprint 452 — S3.5 / CC4.2)

| # | Action | File |
|---|--------|------|
| 11 | Provision an isolated PostgreSQL test instance (Render free tier or local Docker) | See Step 1 in template |
| 12 | Execute the 10-step restore procedure (SQL queries pre-written) and fill in every field | [`dr-test-2026-Q1.md`](../docs/08-internal/dr-test-2026-Q1.md) |
| 13 | Tear down the test instance after completion | See Step 11 in template |
| 14 | Copy signed report to evidence folder | → `docs/08-internal/soc2-evidence/s3/dr-test-2026-Q1.md` |

- [ ] Item 11 complete
- [ ] Item 12 complete
- [ ] Item 13 complete
- [ ] Item 14 complete

---

## 🟡 Stripe Production Cutover (Sprint 447)

All code is production-ready (27/27 E2E tests passed). Requires your Stripe `sk_live_` keys.

| # | Action | Notes |
|---|--------|-------|
| 15 | Stripe Dashboard: confirm `STRIPE_SEAT_PRICE_MONTHLY` is **graduated pricing** — Tier 1 (qty 1–7) = $80, Tier 2 (qty 8–22) = $70 | Dashboard → Products |
| 16 | Stripe Dashboard: enable **Customer Portal** — payment method updates, invoice viewing, cancel at period end | Dashboard → Settings → Customer Portal |
| 17 | Verify "Manage Billing" button from `/settings/billing` opens Stripe portal | Manual test |
| 18 | Update [`pricing-launch-readiness.md`](pricing-launch-readiness.md): check off env vars + Stripe objects, sign as GO | This file |
| 19 | Create production Stripe products / prices / coupons using `sk_live_` key (same structure as test mode — 4 products, 8 prices, 2 coupons) | Stripe Dashboard |
| 20 | Set production env vars on Render + Vercel, then deploy with `alembic upgrade head` | Render dashboard |
| 21 | Smoke test: place a real charge on Solo monthly (lowest tier) | Use real card |
| 22 | Monitor Stripe webhook delivery dashboard for 24 hours | Dashboard → Developers → Webhooks |

- [ ] Item 15 complete
- [ ] Item 16 complete
- [ ] Item 17 complete
- [ ] Item 18 complete — **GO signed**
- [ ] Item 19 complete
- [ ] Item 20 complete
- [ ] Item 21 complete
- [ ] Item 22 complete

---

## 🟡 Legal Sign-Offs

| # | Action | File |
|---|--------|------|
| 23 | **Terms of Service v2.0** — obtain legal owner sign-off, add effective date | [`TERMS_OF_SERVICE.md`](../docs/04-compliance/TERMS_OF_SERVICE.md) |
| 24 | **Privacy Policy v2.0** — obtain legal owner sign-off, add effective date | [`PRIVACY_POLICY.md`](../docs/04-compliance/PRIVACY_POLICY.md) |

- [ ] Item 23 complete
- [ ] Item 24 complete

---

## 🔵 Decisions Required (Blocks Sprint Execution)

Engineering cannot start these sprints without your choice. Read the options in the linked sprint, pick one, then sprint starts.

| # | Decision needed | Sprint | Options |
|---|----------------|--------|---------|
| 25 | **SIEM / Log Aggregation approach** | 463 | A: Grafana Loki, B: Elastic Stack, C: Datadog, D: Defer (use Prometheus/Sentry only) |
| 26 | **Cross-Region Database Replication tier** | 464 | Read replica vs. cross-region standby vs. pgBackRest — evaluate Render options + cost |
| 27 | **Secrets Vault secondary backup location** | 466 | AWS Secrets Manager (separate account), encrypted offline store, or secondary cloud provider |
| 28 | **Bug Bounty / VDP approach** | 468 | Public (HackerOne/Bugcrowd), private invite-only, or enhanced VDP with `security.txt` only |
| 29 | **SOC 2 auditor selection + observation window start date** | 469 | Shortlist 3 CPA firms with SaaS/SOC 2 experience; get quotes; decide |

- [ ] Item 25 decided: ___________
- [ ] Item 26 decided: ___________
- [ ] Item 27 decided: ___________
- [ ] Item 28 decided: ___________
- [ ] Item 29 decided: ___________

---

## 📅 Calendar Reminders to Set

Set these once. After that, the recurring items handle themselves.

| # | Reminder | Frequency | Next occurrence | Purpose |
|---|---------|-----------|----------------|---------|
| 30 | Encryption at rest verification (Render + Vercel screenshots) | Monthly | 2026-03-27 | Sprint 450 / CC7.2 |
| 31 | Risk register quarterly review | Quarterly: Mar 31, Jun 30, Sep 30, Dec 31 | 2026-03-31 | Sprint 451 / CC4.1 |
| 32 | Quarterly access review | Quarterly: Mar 31, Jun 30, Sep 30, Dec 31 | 2026-03-31 | Sprint 454 / CC6.1 |
| 33 | Backup restore test | Semi-annual: Jun 30, Dec 31 | 2026-06-30 | Sprint 452 / S3.5 |
| 34 | Security training annual renewal | Annual: January 1 | 2027-01-01 | Sprint 453 / CC2.2 |
| 35 | Secrets vault sync verification | Every 90 days | After Sprint 466 completes | Sprint 466 / CC7.3 |

> **Note:** Items 31 and 32 share the same dates (Mar 31, Jun 30, Sep 30, Dec 31). Create one quarterly reminder block for both.

- [ ] Item 30 set
- [ ] Item 31 set
- [ ] Item 32 set (can share with Item 31)
- [ ] Item 33 set
- [ ] Item 34 set
- [ ] Item 35 set (after Sprint 466)

---

## ✅ Completed CEO Actions

Move items here (with date) once done.

| # | Action | Completed |
|---|--------|----------|
| — | *(none yet)* | |

---

## How This File Works

- **Engineering** adds items here when a sprint produces a CEO action
- **You** work through items in priority order (🔴 → 🟠 → 🟡 → 🔵 → 📅)
- When you complete an item: check the box + move it to the ✅ section with the date
- This file is committed to the repo so the action inventory is versioned
- Engineering reviews this file at the start of each sprint to see what's unblocked

---

*Last synchronized with `tasks/todo.md` on 2026-02-27. Sprints 449–454 and 463–469 captured.*
