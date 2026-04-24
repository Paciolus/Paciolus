# Pricing Launch Readiness Report

**Date:** 2026-02-25
**Version:** v2.1.0
**Status:** PENDING SIGN-OFF

---

## 1. Executive Summary

**Recommendation:** GO / NO-GO (circle one)

The pricing launch validation matrix covers 7 backend test classes (~210 tests) and 2 frontend test suites (~55 tests), totaling ~265 new automated tests. Manual QA checklist covers 6 validation areas with ~100 checkpoints.

**Key metrics:**
- Backend tests: 188/188 passing
- Frontend tests: 48/48 passing
- Full regression suite: pending / ~4,650 backend + build-verified / ~1,190 frontend
- Manual QA areas: ___/6 (pending manual execution)

---

## 2. Validation Matrix Results

| # | Validation Area | Tests | Pass | Fail | Coverage |
|---|----------------|-------|------|------|----------|
| 1 | Marketing Pricing Correctness | 27 | 27 | 0 | Price table, seats, trials, promos |
| 2 | Checkout Path Correctness | 36 | 36 | 0 | Tier×interval×seat×promo matrix |
| 3 | Billing Lifecycle | 35 | 35 | 0 | State machine, webhooks, sync |
| 4 | Webhook Reconciliation | 28 | 28 | 0 | Tier resolution, dispatch, edges |
| 5 | Entitlement Enforcement | 35 | 35 | 0 | Limits, tools, formats, workspace |
| 6 | Promo Application Policy | 18 | 18 | 0 | Interval matching, case, stacking |
| 7 | Old Subscriber Regression | 13 | 13 | 0 | Professional tier backward compat |
| 8 | Frontend Checkout Page | 28 | 28 | 0 | Rendering, interaction, URL params |
| 9 | Frontend Billing Hook | 20 | 20 | 0 | API calls, state, errors |

**Total automated:** 236 tests (188 backend + 48 frontend), all passing

---

## 3. Known Limitations

These deficiencies are accepted for launch. Each has a documented mitigation.

| # | Limitation | Impact | Mitigation |
|---|-----------|--------|------------|
| 1 | ~~Professional tier deprecated but not removed from DB enum~~ CLEARED 2026-04-23 — Professional is a live paid tier under Pricing v3 (Sprints 449–476). `billing/price_config.py` wires $500/mo + $5,000/yr, seat add-ons, trial eligibility. Entitlements row has full mid-tier features. | n/a | n/a |
| 2 | Trial expiry email notifications deferred | Users won't receive email 3 days before trial ends | ~~Webhook event logged; manual monitoring~~ CLEARED 2026-04-10 per Sprint 690 — `send_trial_ending_email` wired, 3-day default window, graceful SendGrid outage handling. |
| 3 | ~~Team member counting is placeholder~~ CLEARED 2026-04-23 per Sprint 691 — `check_seat_limit_for_org` verified against 11-test matrix: member count + fresh pending invites counted; stale pending (`expires_at` lapsed), ACCEPTED, REVOKED, and status=EXPIRED invites excluded. | n/a | n/a |
| 4 | ~~Seat enforcement mode defaults to "soft"~~ CLEARED 2026-04-23 — `config.py:500` defaults `SEAT_ENFORCEMENT_MODE="hard"` and production hard-fails startup on "soft" per `config.py:502-506`. Hard mode returns HTTP 403 `TIER_LIMIT_EXCEEDED` with `upgrade_url=/pricing`. | n/a | n/a |
| 5 | No Stripe signature verification unit test | Relies on Stripe SDK internal logic | Stripe SDK handles signature verification |
| 6 | No idempotency key tests | Stripe handles server-side deduplication | Client retry logic uses unique session creation |
| 7 | Tax handling not implemented | No tax calculation in checkout | Recommend Stripe Tax for production |
| 8 | Multi-currency billing not supported | USD only | All prices are USD; currency conversion is for TB analysis, not billing |

---

## 4. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Webhook delivery failure | Low | High | Stripe retries 3x; subscription sync verifiable via portal |
| Price ID mismatch (env var error) | Medium | Critical | Startup validation (`validate_billing_config`) hard-fails in production |
| Trial abuse (repeated signups) | Low | Medium | Trial eligibility checks existing subscriptions |
| Promo code leakage | Low | Low | Only 2 codes; Stripe-side usage limits configurable |
| Seat pricing calculation error | Low | High | Covered by 15+ seat pricing unit tests |
| ~~Professional tier users lose access~~ | n/a | n/a | CLEARED 2026-04-23 — Professional is a live Pricing v3 tier with full entitlements; no Solo-parity mapping required. |
| Stripe webhook secret rotation | Low | High | Documented in runbook; CI validates config |
| Concurrent checkout race condition | Low | Medium | Stripe deduplicates by customer ID |

---

## 5. Automated Test Coverage Map

### Backend (`test_pricing_launch_validation.py`)
```
TestMarketingPricingCorrectness     — price_config.py, tier_display.py
TestCheckoutPathCorrectness         — checkout.py, routes/billing.py (schemas)
TestBillingLifecycle                 — subscription_manager.py, webhook_handler.py
TestWebhookReconciliation           — webhook_handler.py (_resolve_*, _find_*)
TestEntitlementEnforcement           — entitlements.py, entitlement_checks.py
TestPromoApplicationPolicy           — price_config.py (promo functions)
TestProfessionalTierValidation      — entitlements.py (live Pricing v3 Professional tier)
```

### Frontend
```
PricingLaunchCheckout.test.tsx       — checkout/page.tsx (render, interaction)
PricingLaunchBillingHook.test.ts     — hooks/useBilling.ts (API calls, state)
```

### Pre-existing Coverage (~230 tests across 13 files)
```
test_pricing_integration.py          — E2E flows, feature flags, Prometheus
test_billing_routes.py               — Route registration, line items, promos
test_tier_display.py                 — Display names, purchasable tiers
PricingPage.test.tsx                 — Marketing page rendering
BillingComponents.test.tsx           — PlanCard, CancelModal, UpgradeModal
```

---

## 6. Deployment Checklist

> **Pricing model drift caveat (added 2026-04-24):** This document was authored at Sprint 440 (Pricing v2 — Solo $50/mo, single graduated seat add-on). Phase LXIX (Sprints 449–476) shipped Pricing v3 in code: Solo $100/mo, flat per-tier seat add-ons ($65 Pro / $45 Ent). The env var checkboxes below reflect what was set at v2. **Stripe test mode is still at v2 prices and is treated as abandoned.** Phase 4.1 cutover will build live mode fresh at v3 — see `tasks/ceo-actions.md` Section 4.1 for the authoritative live-mode price/env-var list.

### Environment Variables (Required) — Set at v2 in test mode; **rebuild at v3 for live**
- [x] `STRIPE_SECRET_KEY` — `sk_test_...` configured
- [x] `STRIPE_WEBHOOK_SECRET` — `whsec_...` configured
- [x] `STRIPE_PRICE_SOLO_MONTHLY` — test-mode v2 price ($50); live v3 will be $100
- [x] `STRIPE_PRICE_SOLO_ANNUAL` — test-mode v2 price ($500); live v3 will be $1,000
- [x] `STRIPE_PRICE_PROFESSIONAL_MONTHLY` — test-mode v2 price; live v3 will be $500. **Note:** older env var name `STRIPE_PRICE_TEAM_MONTHLY` no longer read by code — Phase LXIX renamed `team` → `professional`
- [x] `STRIPE_PRICE_PROFESSIONAL_ANNUAL` — test-mode v2 price; live v3 will be $5,000
- [x] `STRIPE_PRICE_ENTERPRISE_MONTHLY` — test-mode v2 price; live v3 will be $1,000
- [x] `STRIPE_PRICE_ENTERPRISE_ANNUAL` — test-mode v2 price; live v3 will be $10,000

### Environment Variables (Recommended) — Set at v2 in test mode; **rebuild at v3 for live**
- [x] `STRIPE_SEAT_PRICE_PRO_MONTHLY` — Professional seat add-on $65/mo (was single-tier `STRIPE_SEAT_PRICE_MONTHLY` at v2; Phase LXIX split into per-tier vars)
- [x] `STRIPE_SEAT_PRICE_PRO_ANNUAL` — Professional seat add-on $650/yr
- [x] `STRIPE_SEAT_PRICE_ENT_MONTHLY` — Enterprise seat add-on $45/mo (new in v3 — must be created at Phase 4.1)
- [x] `STRIPE_SEAT_PRICE_ENT_ANNUAL` — Enterprise seat add-on $450/yr (new in v3 — must be created at Phase 4.1)
- [x] `STRIPE_COUPON_MONTHLY_20` — `Hqgmc0Yw` configured (test mode); live coupon at Phase 4.1
- [x] `STRIPE_COUPON_ANNUAL_10` — `x4WHgg5N` configured (test mode); live coupon at Phase 4.1
- [x] `PRICING_V2_ENABLED=true` — Still wired in `backend/config.py` and `backend/routes/billing.py`; gates the v2 checkout schema

### Authentication Secrets — SET (Sprint 440)
- [x] `JWT_SECRET_KEY` — 64-char hex, stable across restarts
- [x] `CSRF_SECRET_KEY` — 64-char hex, differs from JWT secret

### Stripe Dashboard
- [x] 6 base prices created (3 tiers × 2 intervals) — Sprint 439 (v2; **rebuild at v3 in live mode**)
- [x] 2 seat add-on prices created (originally graduated; Phase LXIX flat per-tier model needs **4 seat prices in live mode** — Pro × 2 + Ent × 2)
- [x] 2 coupons created (MONTHLY_20_3MO, ANNUAL_10_1YR) — Sprint 439
- [x] Set business name in Dashboard — "Paciolus"
- [ ] Webhook endpoint configured with all 6 event types
- [x] Test mode E2E verified — 27/27 smoke tests passed at v2 (Sprint 440). **Re-run required against v3 live mode at Phase 4.1.**
- [x] Customer Portal configured (payment methods, invoices, cancellation) — verified 2026-04-24
- [ ] **Phase 4.1 cleanup** — bulk-archive all test-mode prices after live mode verified (test mode is abandoned at v2)
- [ ] **Phase 4.1 rename** — Stripe products are still labeled "Team" / "Organization" from Sprint 439; rename in live mode to "Professional" / "Enterprise" to match website

### Sprint 440 Smoke Test Results (2026-02-25) — 27/27 PASSED
| # | Test | Result | Detail |
|---|------|--------|--------|
| 1 | Solo monthly checkout | 201 | Real Stripe Checkout URL returned |
| 2 | Solo + MONTHLY20 promo | 201 | Promo applied to checkout session |
| 3 | ANNUAL10 rejected on monthly | 400 | Correct promo/interval validation |
| 4 | Team + 5 seats checkout | 201 | Dual line item (plan + seat add-on) |
| 5 | Seats rejected on Solo | 400 | Correct tier/seat validation |
| 6 | Enterprise annual checkout | 201 | Real Stripe Checkout URL returned |
| 7 | Stripe customer creation | PASS | cus_* ID returned |
| 8 | Stripe subscription creation | PASS | sub_* active (tok_visa test card) |
| 9 | Local subscription sync | PASS | DB record matches Stripe |
| 10 | GET /subscription | 200 | tier=solo, status=active |
| 11 | POST /cancel | 200 | Real Stripe sub modified |
| 12 | cancel_at_period_end | PASS | True after cancel |
| 13 | Cancel billing event | PASS | SUBSCRIPTION_CANCELED recorded |
| 14 | POST /reactivate | 200 | Real Stripe sub modified |
| 15 | cancel_at_period_end | PASS | False after reactivate |
| 16 | GET /portal-session | 200 | Real Stripe portal URL |
| 17 | GET /usage | 200 | Limits returned correctly |
| 18 | GET /weekly-review | 200 | Analytics metrics present |
| 19 | Billing events audit trail | PASS | Events recorded in DB |
| 20 | Stripe subscription cleanup | PASS | Canceled in Stripe |
| 21 | Stripe customer cleanup | PASS | Deleted from Stripe |
| 22 | Local DB cleanup | PASS | All test data removed |

**Code changes:** Added try/except → 502 on 6 Stripe-calling endpoints (checkout, cancel, reactivate, add-seats, remove-seats, portal)

---

## 7. Sign-Off

| Role | Name | Approved | Date |
|------|------|----------|------|
| Code Owner | ___________ | ☐ | ___________ |
| QA Lead | ___________ | ☐ | ___________ |
| CEO | ___________ | ☐ | ___________ |

### Final Decision

- [ ] **GO** — All validation areas pass, known limitations accepted
- [ ] **NO-GO** — Critical issues identified (list below)

**Critical Issues (if NO-GO):**
1.
2.
3.

---

*Generated by Pricing Launch Validation Matrix — Paciolus v2.1.0*
