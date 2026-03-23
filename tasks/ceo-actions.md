# CEO Action Items

> **Single source of truth for everything requiring your direct action.**
> Engineering delivers scaffolding; you complete execution.
> Check boxes (`[ ]` → `[x]`) as you complete items, then move to [Completed](#completed).

**Last synchronized:** 2026-03-23 — Sprints 447–570 audited. SOC 2 items deferred per CEO directive (2026-03-23).

---

## Priority Guide

| Symbol | Meaning |
|--------|---------|
| 🟡 | Milestone — major business action (billing launch, legal) |
| ⚪ | Setup — one-time infrastructure/admin tasks |
| 🔵 | Decision — blocks an engineering sprint |
| 🗄️ | Deferred — SOC 2 items, revisit when enterprise demand materializes |

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
