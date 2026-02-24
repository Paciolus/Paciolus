# Implementation Decision Record: Hybrid Pricing Model Overhaul

> **Date:** 2026-02-24
> **Status:** APPROVED — CEO decisions resolved 2026-02-24
> **Scope:** Billing tiers, Stripe integration, pricing UI, entitlement wiring
> **Supersedes:** Phase L pricing (5-tier flat model)

---

## Decision Summary

### Decision 1: Migration Strategy

**Chosen: Option A — Display-Name Migration Only**

Keep internal tier IDs (`free`, `starter`, `professional`, `team`, `enterprise`) unchanged across the entire stack. Map new public-facing plan names via a presentation layer.

| Internal ID | Current Display | New Display | Status |
|---|---|---|---|
| `free` | Free | Free | Active |
| `starter` | Starter | Solo | Active |
| `professional` | Professional | — | **REMOVED** (no existing customers) |
| `team` | Team | Team | Active |
| `enterprise` | Enterprise | Organization | Active |

**Rationale:**

1. **DB safety.** `UserTier` is a PostgreSQL `ENUM` type. Renaming enum values requires `ALTER TYPE ... RENAME VALUE`, which is irreversible without recreating the type. A display-name layer avoids this entirely.
2. **Stripe decoupling.** Existing Stripe subscriptions carry `metadata.paciolus_user_id` and price IDs. Changing internal tier strings would require a coordinated Stripe metadata migration with zero-downtime cutover — high risk for a naming change.
3. **Blast radius.** The `UserTier` enum is referenced in:
   - `models.py` (User.tier column + enum definition)
   - `subscription_model.py` (raw string enum in Subscription.tier column)
   - `shared/entitlements.py` (5-key dict keyed by UserTier)
   - `shared/entitlement_checks.py` (4 check functions)
   - `billing/price_config.py` (string-keyed price table)
   - `billing/webhook_handler.py` (tier resolution from Stripe price ID)
   - `billing/checkout.py` (customer creation)
   - `routes/billing.py` (checkout request validation)
   - `frontend/src/types/auth.ts` (User.tier literal union)
   - `frontend/src/components/shared/UpgradeGate.tsx` (TIER_TOOLS dict)
   - `frontend/src/components/billing/UpgradeModal.tsx` (tier list)
   - `frontend/src/app/(marketing)/pricing/page.tsx` (plan cards)
   - Alembic migrations (2 migration files with hardcoded enum values)
   - 6+ test files

   That is 15+ files. A hard rename touches all of them plus requires an Alembic migration to alter the PostgreSQL enum type. A display-name layer touches 3-4 frontend files and 1 backend config.

4. **Rollback.** Display-name changes are a config revert. Enum renames require a reverse migration and Stripe reconciliation.

**What Option B would require (rejected):**
- New Alembic migration: `ALTER TYPE usertier RENAME VALUE 'starter' TO 'solo'` (PostgreSQL 10+)
- Subscription table: separate migration for the inline enum
- Stripe: update all price metadata, customer records
- Frontend: update every string literal across ~8 files
- Risk of stale cache: any cached `user.tier` value becomes invalid during rollout
- No rollback without a reverse migration

### Decision 2: Launch Pricing Model — CONFIRMED

| Plan | Internal Tier | Monthly | Annual | Seats |
|---|---|---|---|---|
| Free | `free` | $0 | $0 | 1 |
| Solo | `starter` | $50 | $500 | 1 |
| Team | `team` | $130 | $1,300 | 3 (base) |
| Organization | `enterprise` | $400 | $4,000 | 3 (included) |

**Add-On Seat Pricing (Team & Organization only):**

| Range | Monthly/Seat | Annual/Seat |
|---|---|---|
| 4–10 | $80 | $800 |
| 11–25 | $70 | $700 |
| 26+ | Contact sales | Contact sales |

**Trial & Promo:**
- 7-day free trial on all paid plans (Stripe `trial_period_days: 7`)
- Annual billing available on all paid plans
- Promo: Monthly → 20% off first 3 months OR Annual → extra 10% off first year
- Best single discount only (no stacking)

**Key changes from current model:**
1. `professional` tier fully removed from all purchase/display paths (no existing customers — clean cut)
2. A/B price variant system (`PriceVariant` enum, `PRICE_VARIANT` config) retired — single price table
3. Seat quantity introduced (current model is flat per-plan, quantity=1)
4. Tiered seat pricing requires Stripe metered/tiered billing or multi-line-item checkout
5. Trial period added (current model has no trial)
6. Promo coupons replace A/B testing as the discounting mechanism
7. Seat enforcement starts in **soft mode** (log-only) for first 30 days, then switches to hard mode

---

## Risk Matrix

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| ~~R1~~ | ~~Existing `professional` subscribers orphaned~~ | — | — | **ELIMINATED** — No existing customers. Clean removal. |
| R2 | **Stripe quantity billing complexity** — current checkout creates 1 line item, quantity=1. Seat model needs quantity > 1 or metered billing. | HIGH | MEDIUM | Use Stripe `quantity` parameter on subscription items. Tiered pricing via Stripe's `tiers` mode on the Price object. Implement seat management API before enabling seat purchases. |
| R3 | **Tiered seat pricing calculation drift** — local price display vs Stripe invoice mismatch | MEDIUM | HIGH | Stripe is the source of truth for invoicing. Local display is advisory only. Add reconciliation check in webhook handler (compare expected vs actual invoice amount). |
| R4 | **Trial abuse** — users create multiple accounts for repeated 7-day trials | MEDIUM | LOW | Stripe handles trial per customer. Add disposable email blocking (already exists). Consider fingerprinting later if abuse detected. |
| R5 | **Promo coupon stacking** — user applies both monthly and annual discounts | LOW | MEDIUM | Stripe Coupons are mutually exclusive per subscription. Enforce single coupon in checkout session creation. |
| R6 | **Entitlement regression** — changing `TIER_ENTITLEMENTS` dict for new pricing accidentally restricts existing users | LOW | MEDIUM | No existing customers reduces this to a testing concern. Run entitlement diff tests comparing old vs new mappings. Feature flag still gates deployment. |
| R7 | **Frontend cache showing stale prices** — user sees old prices after deployment | LOW | LOW | Price data served from config, not cached API. Force cache-bust via Next.js build hash. |
| R8 | **Migration window downtime** — DB migration + Stripe sync + frontend deploy are not atomic | MEDIUM | MEDIUM | Deploy in phases: (1) backend display-name layer + seat model, (2) Stripe product/price creation, (3) frontend pricing page, (4) checkout flow update. Each phase independently deployable and reversible. |
| R9 | **`professional` enum value persists in PostgreSQL** — can't remove enum values without type recreation | LOW | LOW | Leave in UserTier Python enum with `# DEPRECATED` comment. Exclude from all display/purchase paths. Clean removal deferred to next major DB migration. |
| R10 | **Annual promo calculation error** — 10% extra discount on already-discounted annual price | LOW | MEDIUM | Stripe handles discount math. Define promo as Stripe Coupon with `percent_off: 10`, `duration: once`, applied to first invoice only. |

---

## Chosen Path: Sprint Plan with Acceptance Criteria

### Sprint A: Display-Name Layer + Config Overhaul + Professional Removal

**Scope:** Backend config, shared display mapping, professional tier removal from all paths, A/B variant retirement. No DB migration. No Stripe changes.

**Deliverables:**
1. `backend/shared/tier_display.py` — canonical mapping: `{internal_id: display_name}`, `get_display_name(tier) -> str`, `get_internal_id(display_name) -> str`
2. Update `billing/price_config.py`:
   - New `PRICE_TABLE` values: Solo=$50/$500, Team=$130/$1,300, Organization=$400/$4,000
   - Remove `PriceVariant` enum and A/B variant system (single price table, no "control"/"experiment")
   - Remove `professional` entries from price table
   - Remove `PRICE_VARIANT` config dependency
3. Update `shared/entitlements.py`:
   - Adjust `STARTER` entitlements to match "Solo" feature set
   - Adjust `ENTERPRISE` entitlements to match "Organization" feature set
   - Add `seats_included` field to `TierEntitlements` (Free=1, Solo=1, Team=3, Organization=3)
   - Mark `PROFESSIONAL` entitlements with `# DEPRECATED — no purchase path` comment
4. Update `models.py` — add `# DEPRECATED` comment on `PROFESSIONAL` enum value
5. Remove `professional` from: `UpgradeGate` TIER_TOOLS, `UpgradeModal` tier list, checkout tier validation
6. Update `routes/billing.py` — reject `tier="professional"` in `CheckoutRequest` with 400

**Acceptance Criteria:**
- [ ] `get_display_name(UserTier.STARTER)` returns `"Solo"`
- [ ] `get_display_name(UserTier.ENTERPRISE)` returns `"Organization"`
- [ ] `get_display_name(UserTier.PROFESSIONAL)` returns `"Professional"` (deprecated, no "(Legacy)" needed — no customers)
- [ ] `PRICE_TABLE["starter"]["monthly"]` == 5000 (cents) — flat keys, no variant nesting
- [ ] `PRICE_TABLE["team"]["monthly"]` == 13000 (cents)
- [ ] `PRICE_TABLE["enterprise"]["monthly"]` == 40000 (cents)
- [ ] `PriceVariant` enum removed; `get_price_cents()` takes 2 args (tier, interval), not 3
- [ ] `TierEntitlements` has `seats_included: int` field
- [ ] Checkout for `tier="professional"` returns HTTP 400
- [ ] `professional` absent from UpgradeModal and UpgradeGate purchase paths
- [ ] All existing backend tests pass (update tests referencing A/B variants)
- [ ] No DB migration required

---

### Sprint B: Seat Model + Stripe Product Architecture

**Scope:** DB migration for seat tracking. Stripe product/price creation. No frontend changes.

**Deliverables:**
1. Alembic migration: add `seat_count` column to `subscriptions` table (default=1, nullable=False)
2. Alembic migration: add `additional_seats` column to `subscriptions` table (default=0)
3. Update `subscription_model.py` — new columns + `total_seats` property
4. Stripe product setup documentation — Price objects for base plans + per-seat add-on prices with tiered pricing
5. Update `billing/price_config.py` — add `SEAT_PRICE_TABLE` for tiered add-on pricing
6. Update `billing/webhook_handler.py` — extract seat quantity from Stripe subscription items, sync to local `seat_count`

**Acceptance Criteria:**
- [ ] `Subscription.seat_count` persisted and synced from Stripe webhook
- [ ] `Subscription.total_seats` returns `seats_included + additional_seats`
- [ ] Webhook handles `customer.subscription.updated` with quantity changes
- [ ] Alembic migration up/down works cleanly
- [ ] `SEAT_PRICE_TABLE` defines 3 tiers: 4–10 ($80), 11–25 ($70), 26+ (contact)
- [ ] Existing subscriptions default to `seat_count=1, additional_seats=0`
- [ ] `SEAT_ENFORCEMENT_MODE` config defaults to `"soft"` (log-only for first 30 days, then switch to `"hard"`)
- [ ] Soft mode: seat limit violations logged with `logger.warning()` but request proceeds
- [ ] Hard mode: seat limit violations return 403 TIER_LIMIT_EXCEEDED

---

### Sprint C: Trial + Promo Infrastructure

**Scope:** Stripe trial config. Coupon management. Backend promo logic.

**Deliverables:**
1. Update `billing/checkout.py` — add `trial_period_days=7` to Stripe checkout session for new subscriptions
2. Create Stripe Coupons: `MONTHLY_20_3MO` (20% off, 3 months) and `ANNUAL_10_1YR` (10% off, first invoice)
3. Update `billing/price_config.py` — add `PROMO_COUPONS` config with coupon IDs
4. Update `routes/billing.py` — `CheckoutRequest` gains optional `promo_code: str | None` field
5. Backend validation: only one promo per checkout, validate coupon against interval (monthly promo on monthly plan, annual promo on annual plan)
6. Update webhook handler — handle `customer.subscription.trial_will_end` event (3 days before trial ends)

**Acceptance Criteria:**
- [ ] New checkout sessions include 7-day trial
- [ ] `promo_code` in checkout request applies correct Stripe coupon
- [ ] Monthly promo rejected on annual plan and vice versa
- [ ] No coupon stacking — second coupon application returns 400
- [ ] Trial-to-paid transition fires `checkout.session.completed` and syncs correctly
- [ ] `trial_will_end` event logged (notification infrastructure deferred)

---

### Sprint D: Frontend Pricing Page Overhaul

**Scope:** Marketing pricing page rewrite. No checkout flow changes yet.

**Deliverables:**
1. Rewrite `pricing/page.tsx` — 3 plan cards (Solo, Team, Organization) + Free tier callout
2. Seat calculator widget — interactive slider/input for Team and Organization, shows tiered pricing
3. Annual/monthly toggle with savings display
4. Promo banner — "20% off first 3 months" / "Extra 10% off annual"
5. Feature comparison table updated for 4 tiers (Free, Solo, Team, Organization)
6. Plan estimator updated for new tier names
7. Organization 26+ seats CTA routes to existing `/contact` page (contact form backend already exists from Phase XIV)

**Acceptance Criteria:**
- [ ] Page displays "Solo", "Team", "Organization" (never internal tier IDs)
- [ ] Seat calculator correctly computes tiered pricing (4–10 @ $80, 11–25 @ $70)
- [ ] Annual toggle shows correct savings percentage
- [ ] Promo banners render conditionally based on config
- [ ] `npm run build` passes
- [ ] Oat & Obsidian design compliance (sage/clay/obsidian/oatmeal tokens only)
- [ ] WCAG AA contrast on all new elements

---

### Sprint E: Checkout Flow + Seat Management

**Scope:** Multi-line-item checkout. Seat add/remove API. Billing page updates.

**Deliverables:**
1. Update `billing/checkout.py` — support `quantity` parameter for seat-based plans
2. New endpoint: `POST /billing/add-seats` — creates Stripe subscription item update
3. New endpoint: `POST /billing/remove-seats` — reduces quantity (minimum = `seats_included`)
4. Update `routes/billing.py` — `CheckoutRequest` gains `seat_count: int` field (default=0)
5. Update `UpgradeModal.tsx` — seat selector for Team/Organization plans
6. Update billing settings page — current seat count display, add/remove seat buttons
7. Update `useBilling` hook — expose seat count and seat management functions

**Acceptance Criteria:**
- [ ] Checkout creates subscription with correct quantity
- [ ] Add-seat endpoint prorates correctly (Stripe handles proration)
- [ ] Remove-seat endpoint enforces minimum (can't go below `seats_included`)
- [ ] Billing page shows "3 of 5 seats used" style display
- [ ] Webhook correctly syncs seat count changes
- [ ] Entitlement checks respect `total_seats` for team features

---

### Sprint F: Integration Testing + Feature Flag Rollout

**Scope:** End-to-end testing. Feature flag gating. Soft enforcement activation.

**Deliverables:**
1. Feature flag: `PRICING_V2_ENABLED` — gates new pricing display and checkout flow
2. Integration tests: full checkout→trial→conversion→seat-add→cancel flow
3. Webhook simulation tests for all seat/trial/promo scenarios
4. Monitoring: Prometheus counter for `pricing_v2_checkouts_total`
5. Runbook: pricing rollback procedure
6. Soft→hard enforcement cutover plan: `SEAT_ENFORCEMENT_MODE` starts `"soft"`, scheduled switch to `"hard"` at day 30

**Acceptance Criteria:**
- [ ] Feature flag toggles entire pricing experience atomically
- [ ] Integration test covers: free→Solo, free→Team(5 seats), trial→paid, add 3 seats, cancel
- [ ] Webhook tests cover: trial_will_end, quantity change, coupon applied, subscription deleted
- [ ] Prometheus metrics incrementing correctly
- [ ] Runbook reviewed and approved
- [ ] `SEAT_ENFORCEMENT_MODE=soft` confirmed in deployment config

---

## Rollback Plan

### Tier 1: Instant Rollback (< 5 minutes)
**Trigger:** Checkout failures, incorrect pricing display, entitlement regression.
**Action:** Set `PRICING_V2_ENABLED=false`. This immediately:
- Reverts pricing page to old 5-tier display
- Reverts checkout flow to old tier selection
- Keeps backend seat columns (harmless, default=1)
- Keeps display-name layer (only consumed when flag=on)

**No data loss. No DB migration needed. No Stripe changes needed.**

### Tier 2: Stripe Product Rollback (< 1 hour)
**Trigger:** Incorrect Stripe pricing, coupon misconfiguration, trial period bugs.
**Action:**
1. Archive new Stripe Price objects (don't delete — preserves invoice history)
2. Revert `STRIPE_PRICE_IDS` env vars to old values
3. Set `PRICING_V2_ENABLED=false`
4. Existing v2 subscribers continue on their Stripe plan (Stripe doesn't retroactively change)
5. New signups use old pricing

### Tier 3: Full Revert (< 1 day)
**Trigger:** Fundamental model flaw discovered post-launch (e.g., seat billing breaks entitlements).
**Action:**
1. Tier 1 + Tier 2 actions
2. Run Alembic downgrade to remove `seat_count` / `additional_seats` columns
3. Revert `TIER_ENTITLEMENTS` dict to pre-v2 values
4. Notify affected v2 subscribers via email (manual process)
5. Stripe: cancel v2 subscriptions, offer manual re-subscription on old plans

**Risk:** Users who signed up under v2 pricing need manual handling. This is acceptable for a small launch cohort.

### Rollback Decision Matrix

| Symptom | Tier | Decision Maker |
|---|---|---|
| Wrong price displayed on marketing page | 1 | Any engineer |
| Checkout 500 error | 1 | Any engineer |
| Entitlement regression (user lost access) | 1 | Any engineer |
| Stripe invoice amount mismatch | 2 | Engineering lead |
| Trial not converting to paid | 2 | Engineering lead |
| Seat addition creates duplicate charges | 2 | Engineering lead |
| Fundamental billing model broken | 3 | CEO |

---

## Resolved Decisions (CEO, 2026-02-24)

| # | Question | Decision | Impact |
|---|---|---|---|
| Q1 | Professional → Solo mapping | **No grandfathering needed — zero existing customers.** Remove `professional` from all purchase/display paths in Sprint A. | Eliminates Sprint F entirely. No migration script needed. |
| Q2 | A/B variant retirement | **Retire completely.** Single price table, no control/experiment split. | Simplifies `price_config.py` — remove `PriceVariant` enum, flatten PRICE_TABLE keys. |
| Q3 | Seat enforcement timeline | **Soft mode for 30 days**, then hard. Config-driven via `SEAT_ENFORCEMENT_MODE`. | Added to Sprint B acceptance criteria. |
| Q4 | 26+ seats CTA | **Contact form** — routes to existing `/contact` page (Phase XIV backend). | No new infrastructure needed. |

---

## Appendix: File Impact Analysis

| File | Sprint | Change Type |
|---|---|---|
| `backend/shared/tier_display.py` | A | **NEW** — display name mapping |
| `backend/shared/entitlements.py` | A | MODIFY — seats_included, professional removal from purchase paths |
| `backend/billing/price_config.py` | A, B, C | MODIFY — flatten price table (remove A/B), new prices, seat prices, promos |
| `backend/models.py` | A | MODIFY — `# DEPRECATED` comment on PROFESSIONAL enum value |
| `backend/routes/billing.py` | A, C, E | MODIFY — reject professional checkout, promo field, seat endpoints |
| `backend/subscription_model.py` | B | MODIFY — seat_count, additional_seats columns |
| `backend/billing/checkout.py` | C, E | MODIFY — trial, quantity, promo |
| `backend/billing/webhook_handler.py` | B, C | MODIFY — seat sync, trial events |
| `backend/shared/entitlement_checks.py` | B | MODIFY — seat enforcement (soft/hard mode) |
| `frontend/src/app/(marketing)/pricing/page.tsx` | D | REWRITE — 3-plan layout, seat calculator |
| `frontend/src/components/billing/UpgradeModal.tsx` | A, E | MODIFY — remove professional, add seat selector |
| `frontend/src/components/billing/PlanCard.tsx` | D | MODIFY — display names, seat count |
| `frontend/src/components/shared/UpgradeGate.tsx` | A | MODIFY — remove professional from TIER_TOOLS |
| `frontend/src/hooks/useBilling.ts` | E | MODIFY — seat management |
| `frontend/src/types/auth.ts` | — | NO CHANGE (tier union stays same) |
| Alembic migration (new) | B | **NEW** — seat columns |
| `backend/tests/test_tier_display.py` | A | **NEW** |
| `backend/tests/test_billing_seats.py` | B, E | **NEW** |
| `backend/tests/test_billing_promos.py` | C | **NEW** |

**Total: ~19 files touched across 6 sprints. 0 DB enum changes. 0 Stripe metadata migrations. 0 customer migrations.**
