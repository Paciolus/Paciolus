# Executive Blockers

> Long-lived items requiring CEO, legal, or security decisions.
> These are not sprint work — separating them keeps the active work queue clean.
> See also: [`tasks/ceo-actions.md`](ceo-actions.md) for tactical CEO action items.

---

## Active (CEO-gated, in launch path)

These items are **tracked in [`ceo-actions.md`](ceo-actions.md)** — this file keeps a one-line pointer so they're visible in the executive-blockers view without duplicating checklists that would drift.

| Item | Canonical location |
|------|---------------------|
| **Sprint 447 — Stripe Production Cutover** | [`ceo-actions.md` Phase 4.1](ceo-actions.md#41-stripe-production-cutover) (also in "This Week's Action Map" → Afternoon 2) |
| **Terms of Service v2.0 — legal sign-off** | [`ceo-actions.md` Phase 4.2](ceo-actions.md#42-legal--policy-placeholders) |
| **Privacy Policy v2.0 — legal sign-off** | [`ceo-actions.md` Phase 4.2](ceo-actions.md#42-legal--policy-placeholders) |
| **Security Policy §12 — emergency contact phone** | [`ceo-actions.md` Phase 4.2](ceo-actions.md#42-legal--policy-placeholders) |

---

## 🗄️ Deferred — SOC 2 (Revisit When Needed)

> All items below deferred per CEO directive (2026-03-23). Not legally required for launch.
> Engineering scaffolding remains in codebase. Activate when enterprise demand materializes.

| Sprint | Item | Status |
|--------|------|--------|
| 463 | SIEM / Log Aggregation (Grafana Loki) | **Scheduled 2026-04-24 as Sprint 716** — reframed from SOC 2 SIEM to free-tier ops tooling on Grafana Cloud Free. Tracked in [`tasks/todo.md`](todo.md) Active Phase. CEO blocker: Grafana Cloud signup. |
| 464 | Cross-Region DB Replication (pgBackRest to S3) | Decision made, sprint not yet scheduled. Note: Phase 4.4's daily `pg_dump` → S3 already covers launch-grade DR; pgBackRest is continuous WAL streaming for enterprise cross-region requirements. |
| 466 | Secrets Vault Backup (AWS Secrets Manager) | Decision made, sprint not yet scheduled |
| 467 | External Penetration Test | Deferred — budget not available. **Revisit trigger:** ~Month 2–3 post-launch once subscription revenue establishes the $5K–30K budget line. Council Review 2026-04-16 flagged this as the highest-value SOC 2 precursor once it becomes financeable. |
| 468 | Bug Bounty Program | Deferred — existing VDP sufficient |
| 469 | SOC 2 Auditor + Observation Window | Deferred — not needed for launch. Activate when a qualifying enterprise prospect asks for the report. |

---

*Last revised: 2026-04-24 — Sprint 463 (Grafana Loki) reclassified and scheduled as Sprint 716 per CEO directive (defer SOC 2 + paid items, do anything free). 464/466/467/468/469 remain deferred.*
