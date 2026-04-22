# Sprint 691 Research Brief — Professional-tier DB enum + team-seat counting

> **Status:** underspecified. The one-line brief in `tasks/todo.md` ("Professional-tier DB enum + team-seat counting. Schema change; CEO migration review required before execution.") doesn't name a specific change. This brief establishes what the current state IS so the CEO can either close the sprint, pick one of the three interpretations below, or defer until a concrete requirement surfaces.
>
> **Bottom line:** the schema is already in its clean Pricing-v3 state (free / solo / professional / enterprise). No visible bug or obvious gap. If there's a specific change the CEO has in mind that prompted the Sprint 691 title, the brief needs a second sentence.
>
> **Date:** 2026-04-22.

---

## Executive summary

- **UserTier enum today:** `FREE → SOLO → PROFESSIONAL → ENTERPRISE` (string-based, 4 values, mirrored in the `subscription_tier` DB enum).
- **Seat configuration today:** Professional = 7 included / 20 max; Enterprise = 20 included / 100 max. Configured in `backend/shared/entitlements.py` and `backend/billing/price_config.py`; enforced via `add_seats()` / `remove_seats()` with optimistic locking.
- **History:** five alembic revisions reached this state, ending at `e3f4a5b6c7d8` (Pricing v3 restructure, 2026-03-02). The schema reflects CEO's current pricing decisions.
- **No obvious defect.** The research pass found no test failures, no hardcoded-but-stale tier string, and no known production bug tied to tier enum or seat counting.
- **Three interpretations** of what Sprint 691 might want (below); pick one or close the sprint.

---

## Three possible interpretations

### Interpretation A — Add a new tier between Professional and Enterprise
*(e.g., "Professional Plus" at ~$750/mo, 12 seats included)*

**What that would take:** 8 file categories + 1 alembic migration.

| File | Change |
|------|--------|
| `backend/models.py:26-40` | Add `PROFESSIONAL_PLUS = "professional_plus"` to the `UserTier` PyEnum |
| `backend/subscription_model.py:112-116` | Add to the inline `Enum()` string list |
| `backend/shared/entitlements.py:65-142` | New `UserTier.PROFESSIONAL_PLUS: TierEntitlements(...)` entry with upload caps, seat counts, feature flags |
| `backend/billing/price_config.py:27-45` | New `PRICE_TABLE["professional_plus"]` entry + env-var loader |
| `backend/billing/price_config.py:70-95` | Update `get_max_self_serve_seats()` / `calculate_additional_seats_cost()` |
| `backend/billing/webhook_handler.py:267, 365` | Add to the `if tier in (...)` tuple + `_TIER_RANK` dict |
| New alembic migration | PostgreSQL: `ALTER TYPE usertier ADD VALUE 'professional_plus'` + `ALTER TYPE subscription_tier ADD VALUE 'professional_plus'`. SQLite: no-op (columns are stored as string). |
| Tests (~6 files) | `test_pricing*.py`, `test_billing*.py`, `test_entitlements.py`, `test_seat_*.py` — update hardcoded tier assertions |

**Stripe side effects:** need new `STRIPE_PRICE_PROFESSIONAL_PLUS_MONTHLY`, `STRIPE_PRICE_PROFESSIONAL_PLUS_ANNUAL`, and `STRIPE_SEAT_PRICE_PRO_PLUS_MONTHLY` env vars + matching Stripe products/prices. Marketing surface (pricing page, plan-card tile, FindYourPlan recommendation logic) needs matching updates.

**Effort:** ~1 week including the Stripe + env var coordination. CEO migration review is appropriate here because the enum ordering affects `_TIER_RANK` upgrade/downgrade event routing on the billing webhook.

### Interpretation B — Rename an existing tier
*(e.g., "Professional" → "Firm" or "Team")*

**What that would take:** 6 file categories + 1 alembic data migration.

| File | Change |
|------|--------|
| `backend/models.py:26-40` | Rename PyEnum value (keep old alias for backwards compat during transition) |
| `backend/subscription_model.py:112-116` | Same — rename the inline Enum string |
| `backend/shared/entitlements.py` | Update dict key |
| `backend/billing/webhook_handler.py:267, 365` | Update `if tier in ("professional", ...)` → new name; same for `_TIER_RANK` |
| `backend/billing/price_config.py` | Update all hardcoded "professional" strings |
| New alembic migration | PostgreSQL: rename enum value (`ALTER TYPE usertier RENAME VALUE 'professional' TO 'firm'` is PG ≥10) + `UPDATE users SET tier = 'firm' WHERE tier = 'professional'` + same for subscriptions |
| Stripe env vars | Rename `STRIPE_PRICE_PROFESSIONAL_*` → `STRIPE_PRICE_FIRM_*` on Render + .env.example |
| Tests | All hardcoded "professional" strings in assertions |
| Marketing copy | Pricing page tier name, recommendation logic, plan-card display |

**Red flag:** `backend/billing/webhook_handler.py:267` auto-creates an Organization when `tier in ("professional", "enterprise")`. Renaming `professional` without updating that check silently disables org auto-creation for the renamed tier. Similarly `_TIER_RANK` dict at line 365.

**Effort:** ~1 week. No known CEO ask for a rename, so this interpretation is speculative.

### Interpretation C — Change team-seat counting semantics
*(e.g., "Professional used to get 5 seats + 15 purchasable; CEO wants 7 + 13 — and the schema should enforce the new cap at DB level rather than app level")*

**What that would take:** 2 file categories + optional alembic migration.

| File | Change |
|------|--------|
| `backend/shared/entitlements.py:65-142` | Adjust `seats_included` / `max_team_seats` values for target tier |
| `backend/billing/price_config.py:70-95` | Update `get_max_self_serve_seats()` constants |
| Optional alembic migration | Add `CHECK (total_seats <= max_seats_for_tier)` constraint — DB-level enforcement. Would require a stored procedure or computed column since `max_seats` is per-tier. Complex; most systems enforce this at app level. |
| Tests | `test_seat_model.py`, `test_seat_management.py`, `test_entitlements.py` |

**This is the cheapest interpretation.** If the sprint is just "Professional's seat count is wrong, fix the number" — it's a one-line entitlements change + test update, no migration needed at all.

**Current values to verify against CEO intent:**

| Tier | `seats_included` | `max_team_seats` |
|------|------------------|------------------|
| FREE | 1 | 0 |
| SOLO | 1 | 0 |
| PROFESSIONAL | 7 | 20 |
| ENTERPRISE | 20 | 100 |

**Effort:** ~1 hour if just a number change. DB constraint would be ~1 day if that's actually wanted (and is overkill for this domain — app-level enforcement is standard).

---

## Evidence appendix

### Alembic history (5 revisions)

| Revision | Date | Title |
|----------|------|-------|
| `c4d5e6f7a8b9` | 2026-02-21 | Add starter + team to UserTier |
| `d9e0f1a2b3c4` | 2026-02-25 | Rename starter → solo |
| `c1d2e3f4a5b6` | 2026-03-01 | Remove enterprise tier (migrate enterprise→team) |
| `d2e3f4a5b6c7` | 2026-03-01 | Add organization tier |
| `e3f4a5b6c7d8` | 2026-03-02 | **Pricing v3 restructure — final state: free / solo / professional / enterprise** |

**The current schema reflects `e3f4a5b6c7d8`.** No obvious gap; the enum matches the pricing page + marketing copy.

### Seat logic call sites

- **Schema:** `backend/subscription_model.py:128-130` — `seat_count` (default 1), `additional_seats` (default 0), `total_seats` computed property.
- **Entitlements dict:** `backend/shared/entitlements.py:65-142` — per-tier `seats_included` + `max_team_seats` fields.
- **Price config:** `backend/billing/price_config.py:70-95` — `get_max_self_serve_seats(tier)` + `calculate_additional_seats_cost()`.
- **Subscription manager:** `backend/billing/subscription_manager.py:48-84` — `_extract_seat_quantity()` + `_extract_additional_seats()` read from Stripe webhook items.
- **Seat mutations:** `backend/billing/subscription_manager.py:*` — `add_seats()` / `remove_seats()` with optimistic locking via `seat_version` column (5-step protocol: snapshot → Stripe call → FOR UPDATE re-acquire → version check → commit).

### Tests exercising seat + tier behaviour

| File | Coverage |
|------|----------|
| `backend/tests/test_seat_model.py` | Seat-count defaults, `total_seats` property math, DB column existence |
| `backend/tests/test_entitlements.py` | Per-tier `seats_included` / `max_team_seats` assertions |
| `backend/tests/test_seat_management.py` | `add_seats()` cap enforcement, optimistic locking, Stripe idempotency |
| `backend/tests/test_subscription_model.py` | Seat extraction from Stripe webhooks, per-tier pricing math |
| `backend/tests/test_pricing_integration.py` | Tier rank ordering, upgrade/downgrade routing |

**No hardcoded tier strings in the entitlements dict (it's `UserTier`-keyed).** The risk surface is in `billing/webhook_handler.py` (two hardcoded tuples) and `billing/price_config.py` (if/elif chain on tier strings). A rename is the only interpretation with real blast radius.

---

## Recommended next action

1. **CEO — close the sprint or add a spec.** The current state is clean; there's no default migration to run. Three possible intents:
   - (A) add a new tier between Pro and Enterprise — ~1 week, full coordinated rollout.
   - (B) rename an existing tier — ~1 week, Stripe + env-var coordination required.
   - (C) adjust seat counts — ~1 hour, no migration.
2. **If none of these is the intent,** Sprint 691 can be closed as "superseded by Pricing v3 restructure (commit `e3f4a5b6c7d8`, 2026-03-02)" — the schema change Sprint 691 pre-dated has already happened.
3. **If the intent is something else entirely** (e.g., a team-seat *counting* bug I haven't found), I can re-run the research with the specific symptom in hand.

**My recommendation (pending CEO input):** close Sprint 691 as superseded. The schema is in the right shape; no visible bug prompts a new migration; the sprint title reads like pre-Pricing-v3 residue. Reopen as a specific sprint (691-A, 691-B, or 691-C) if a concrete change surfaces.
