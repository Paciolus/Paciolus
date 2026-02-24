# Pricing V2 Rollback Runbook

**Phase LIX Sprint F** — Hybrid Pricing Model rollout control.

## Overview

The V2 pricing model (seat-based pricing, 7-day trials, promo codes) is gated behind the `PRICING_V2_ENABLED` feature flag. This runbook covers activation, monitoring, and rollback procedures.

## Feature Flag

| Variable | Default | Effect |
|----------|---------|--------|
| `PRICING_V2_ENABLED` | `false` | Gates seat checkout, promo codes, trial periods, add/remove seats endpoints |
| `SEAT_ENFORCEMENT_MODE` | `soft` | `soft` = log violations only; `hard` = block at seat limit |

## Activation Procedure

### Step 1: Pre-Flight Checks

- [ ] Stripe products and prices configured for all tiers (starter, team, enterprise)
- [ ] Stripe coupons created and IDs set in `STRIPE_COUPON_MONTHLY_20` / `STRIPE_COUPON_ANNUAL_10`
- [ ] `STRIPE_ENABLED=true` confirmed
- [ ] `SEAT_ENFORCEMENT_MODE=soft` confirmed (30-day grace period)
- [ ] Current test suite passing (`pytest` + `npm run build`)

### Step 2: Enable Feature Flag

```bash
# In .env or deployment config:
PRICING_V2_ENABLED=true
```

Restart the application. No database migration required.

### Step 3: Verify Activation

1. Check `/metrics` endpoint for `paciolus_pricing_v2_checkouts_total` metric presence
2. Attempt a checkout with `seat_count > 0` — should succeed
3. Attempt `POST /billing/add-seats` — should succeed (was 503 when flag off)
4. Verify promo code validation works on checkout

## Monitoring During Rollout

### Key Metrics

| Metric | Expected | Alert Threshold |
|--------|----------|-----------------|
| `paciolus_pricing_v2_checkouts_total` | Incrementing | N/A (informational) |
| HTTP 503 on `/billing/add-seats` | 0 (when enabled) | > 0 = flag may be off |
| HTTP 400 on `/billing/create-checkout-session` | Low | Spike = validation issue |

### Dashboard Queries (Prometheus)

```promql
# Checkout rate by tier
rate(paciolus_pricing_v2_checkouts_total[5m])

# Checkout by interval
sum by (interval) (paciolus_pricing_v2_checkouts_total)

# Error rate on billing endpoints
rate(http_requests_total{path=~"/billing/.*", status=~"4..|5.."}[5m])
```

## Rollback Procedure

### Immediate Rollback (< 5 minutes)

1. Set `PRICING_V2_ENABLED=false` in deployment config
2. Restart the application
3. Verify:
   - `POST /billing/add-seats` returns 503
   - `POST /billing/remove-seats` returns 503
   - Checkout ignores `seat_count` and `promo_code` fields
   - Existing subscriptions and seats are **not affected** (Stripe is source of truth)

### What Rollback Does NOT Affect

- Existing subscriptions remain active in Stripe
- Previously added seats remain on the Stripe subscription
- Trial periods already started continue in Stripe
- Applied promo codes remain active through their duration
- The `/billing/subscription`, `/billing/cancel`, `/billing/reactivate` endpoints continue working

### What Rollback DOES Affect

- New checkouts will not include trial periods, promo codes, or seat quantities
- Seat add/remove endpoints become unavailable (503)
- Prometheus checkout counter stops incrementing

## Soft → Hard Enforcement Cutover

### Timeline

| Day | Action |
|-----|--------|
| 0 | Launch with `SEAT_ENFORCEMENT_MODE=soft` |
| 7 | Review soft enforcement logs for false positives |
| 14 | Second review — confirm no edge cases |
| 30 | Switch to `SEAT_ENFORCEMENT_MODE=hard` |

### Cutover Steps

1. Review logs for `"Seat limit exceeded"` warnings from the soft period
2. Verify no legitimate users are being flagged incorrectly
3. Set `SEAT_ENFORCEMENT_MODE=hard` in deployment config
4. Restart the application
5. Monitor for 403 responses on seat-gated endpoints

### Rollback from Hard → Soft

If hard enforcement causes issues:

```bash
SEAT_ENFORCEMENT_MODE=soft
```

Restart. All seat violations become log-only warnings again.

## Escalation Matrix

| Severity | Condition | Action |
|----------|-----------|--------|
| P3 | Checkout errors < 5% | Monitor, investigate |
| P2 | Checkout errors > 5% or seat endpoints failing | Rollback feature flag |
| P1 | Payment processing failure or Stripe webhook errors | Rollback + notify on-call |

## Contact

- Stripe Dashboard: Check for failed payments, subscription issues
- Application logs: Filter by `billing` logger namespace
- Prometheus: `/metrics` endpoint for real-time counters
