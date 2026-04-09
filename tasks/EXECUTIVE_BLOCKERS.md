# Executive Blockers

> Long-lived items requiring CEO, legal, or security decisions.
> These are not sprint work — separating them keeps the active work queue clean.
> See also: [`tasks/ceo-actions.md`](ceo-actions.md) for tactical CEO action items.

---

### Sprint 447 — Stripe Production Cutover

**Status:** PENDING (CEO action required)
**Goal:** Complete Stripe Dashboard configuration and cut over to live mode.
**Context:** Sprint 440 E2E smoke test passed (27/27). All billing code is production-ready.

#### Stripe Dashboard Configuration
- [ ] Confirm `STRIPE_SEAT_PRICE_MONTHLY` is graduated pricing: Tier 1 (qty 1–7) = $80, Tier 2 (qty 8–22) = $70
- [ ] Enable Customer Portal: payment method updates, invoice viewing, cancellation at period end
- [ ] Verify "Manage Billing" button opens portal from `/settings/billing`
- [ ] CEO signs `tasks/pricing-launch-readiness.md` → mark as GO

#### Production Cutover
- [ ] Create production Stripe products/prices/coupons (live secret key)
- [ ] Set production env vars + deploy with `alembic upgrade head`
- [ ] Smoke test with real card on lowest tier (Solo monthly)
- [ ] Monitor webhook delivery in Stripe Dashboard for 24h

---

### Pending Legal Sign-Off

- [ ] **Terms of Service v2.0** — legal owner sign-off with new effective date
- [ ] **Privacy Policy v2.0** — legal owner sign-off with new effective date

---

## 🗄️ Deferred — SOC 2 (Revisit When Needed)

> All items below deferred per CEO directive (2026-03-23). Not legally required for launch.
> Engineering scaffolding remains in codebase. Activate when enterprise demand materializes.

| Sprint | Item | Status |
|--------|------|--------|
| 463 | SIEM / Log Aggregation (Grafana Loki) | Decision made, sprint not yet scheduled |
| 464 | Cross-Region DB Replication (pgBackRest to S3) | Decision made, sprint not yet scheduled |
| 466 | Secrets Vault Backup (AWS Secrets Manager) | Decision made, sprint not yet scheduled |
| 467 | External Penetration Test | Deferred — budget not available |
| 468 | Bug Bounty Program | Deferred — existing VDP sufficient |
| 469 | SOC 2 Auditor + Observation Window | Deferred — not needed for launch |
