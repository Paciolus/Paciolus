# Billing Launch Runbook

**Sprint:** Billing Launch Configuration
**Prerequisite:** Phase L (billing infrastructure) + Phase LIX (hybrid pricing) code-complete.

---

## 1. Stripe Object Setup Order

Create objects in this order in the Stripe Dashboard. Each step depends on the previous.

### Step 1: Products (3)

| Product Name | Description |
|-------------|-------------|
| Paciolus Solo | Solo practitioner plan |
| Paciolus Team | Team plan with seat add-ons |
| Paciolus Organization | Organization plan with seat add-ons |

### Step 2: Prices (6 base + 2 seat)

For each product, create **monthly** and **annual** recurring prices:

| Product | Interval | Amount | Env Var |
|---------|----------|--------|---------|
| Solo | Monthly | $50.00 | `STRIPE_PRICE_STARTER_MONTHLY` |
| Solo | Annual | $500.00 | `STRIPE_PRICE_STARTER_ANNUAL` |
| Team | Monthly | $130.00 | `STRIPE_PRICE_TEAM_MONTHLY` |
| Team | Annual | $1,300.00 | `STRIPE_PRICE_TEAM_ANNUAL` |
| Organization | Monthly | $400.00 | `STRIPE_PRICE_ENTERPRISE_MONTHLY` |
| Organization | Annual | $4,000.00 | `STRIPE_PRICE_ENTERPRISE_ANNUAL` |

For seat add-ons (V2 pricing only), create **graduated** prices:

| Price | Interval | Tiers | Env Var |
|-------|----------|-------|---------|
| Seat Add-On | Monthly | 1-7: $80, 8-22: $70 | `STRIPE_SEAT_PRICE_MONTHLY` |
| Seat Add-On | Annual | 1-7: $800, 8-22: $700 | `STRIPE_SEAT_PRICE_ANNUAL` |

### Step 3: Coupons (2, optional)

| Coupon | Type | Discount | Duration | Env Var |
|--------|------|----------|----------|---------|
| Monthly 20% | percent_off: 20 | 20% | repeating, 3 months | `STRIPE_COUPON_MONTHLY_20` |
| Annual 10% | percent_off: 10 | 10% | once | `STRIPE_COUPON_ANNUAL_10` |

### Step 4: Webhook Endpoint

1. In Stripe Dashboard > Developers > Webhooks, add endpoint:
   - URL: `https://<your-domain>/billing/webhook`
   - Events to listen for:
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `customer.subscription.trial_will_end`
     - `invoice.payment_failed`
     - `invoice.paid`
2. Copy the signing secret (`whsec_...`) to `STRIPE_WEBHOOK_SECRET`.

### Step 5: Customer Portal

1. In Stripe Dashboard > Settings > Customer portal, configure:
   - Allow customers to update payment methods
   - Allow customers to view invoices
   - Allow customers to cancel subscriptions
   - Set cancellation to "at end of billing period"
2. No env var needed (portal is auto-linked via customer ID).

---

## 2. Env Var Checklist

### Critical (Required when `STRIPE_ENABLED`)

Startup validation will **hard fail in production** if any are missing.

| Variable | Format | Description |
|----------|--------|-------------|
| `STRIPE_SECRET_KEY` | `sk_test_...` or `sk_live_...` | Stripe API secret key. Presence enables billing (`STRIPE_ENABLED=true`). |
| `STRIPE_PUBLISHABLE_KEY` | `pk_test_...` or `pk_live_...` | Passed to frontend for Stripe.js. |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | Webhook signature verification secret. |
| `STRIPE_PRICE_STARTER_MONTHLY` | `price_...` | Solo monthly Price ID. |
| `STRIPE_PRICE_STARTER_ANNUAL` | `price_...` | Solo annual Price ID. |
| `STRIPE_PRICE_TEAM_MONTHLY` | `price_...` | Team monthly Price ID. |
| `STRIPE_PRICE_TEAM_ANNUAL` | `price_...` | Team annual Price ID. |
| `STRIPE_PRICE_ENTERPRISE_MONTHLY` | `price_...` | Organization monthly Price ID. |
| `STRIPE_PRICE_ENTERPRISE_ANNUAL` | `price_...` | Organization annual Price ID. |

### Optional (Warnings only if missing)

| Variable | Default | Description |
|----------|---------|-------------|
| `STRIPE_SEAT_PRICE_MONTHLY` | (empty) | Seat add-on monthly Price ID. Required for V2 seat checkout. |
| `STRIPE_SEAT_PRICE_ANNUAL` | (empty) | Seat add-on annual Price ID. Required for V2 seat checkout. |
| `STRIPE_COUPON_MONTHLY_20` | (empty) | Monthly promo coupon ID. Promos disabled if missing. |
| `STRIPE_COUPON_ANNUAL_10` | (empty) | Annual promo coupon ID. Promos disabled if missing. |
| `PRICING_V2_ENABLED` | `false` | Gates seat checkout, trials, promo codes. |
| `SEAT_ENFORCEMENT_MODE` | `soft` | `soft` = log only, `hard` = block at limit. |
| `ENTITLEMENT_ENFORCEMENT` | `hard` | `hard` = block, `soft` = log only. |

---

## 3. Smoke Test Commands

After deployment, verify each billing endpoint. Replace `$TOKEN` with a valid JWT and `$BASE` with the API URL.

### Health Check

```bash
# Verify billing lines in config summary (check application logs)
# Look for: "Stripe Billing: enabled", "Pricing V2: enabled/disabled"
```

### Checkout Session

```bash
curl -s -X POST "$BASE/billing/create-checkout-session" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $(curl -s -c - "$BASE/auth/csrf-token" -H "Authorization: Bearer $TOKEN" | grep csrf | awk '{print $NF}')" \
  -d '{"tier":"starter","interval":"monthly","success_url":"https://app.paciolus.com/settings/billing?success=true","cancel_url":"https://app.paciolus.com/settings/billing?canceled=true"}' \
  | python -m json.tool
# Expected: {"checkout_url": "https://checkout.stripe.com/..."}
```

### Subscription Status

```bash
curl -s "$BASE/billing/subscription" \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool
# Expected: {"tier":"free","status":"active",...}
```

### Usage

```bash
curl -s "$BASE/billing/usage" \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool
# Expected: {"diagnostics_used":0,"diagnostics_limit":5,"clients_used":0,"clients_limit":3,"tier":"free"}
```

### Portal Session

```bash
# Only works for users with an active Stripe subscription
curl -s "$BASE/billing/portal-session" \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool
# Expected: {"portal_url": "https://billing.stripe.com/..."}
```

### Webhook (test via Stripe CLI)

```bash
# Install Stripe CLI, then:
stripe listen --forward-to localhost:8000/billing/webhook
# In another terminal:
stripe trigger checkout.session.completed
# Check application logs for "checkout.session.completed: synced user..."
```

---

## 4. Failure Diagnostics

| Error | Cause | Fix |
|-------|-------|-----|
| Startup exits with "CRITICAL billing config" | Production mode + missing price IDs | Set all 6 `STRIPE_PRICE_*` vars + `STRIPE_WEBHOOK_SECRET` |
| `503 "Billing is not currently available"` | `STRIPE_SECRET_KEY` not set | Set `STRIPE_SECRET_KEY` in .env |
| `400 "No price configured for starter/monthly"` | `STRIPE_PRICE_STARTER_MONTHLY` not set or wrong | Verify Price ID exists in Stripe Dashboard |
| `400 "Invalid signature"` on webhook | `STRIPE_WEBHOOK_SECRET` wrong or stale | Re-copy signing secret from Stripe Dashboard |
| `400 "Missing stripe-signature header"` | Request not from Stripe (or proxy stripping headers) | Ensure reverse proxy forwards all headers |
| `400 "Seat pricing not configured"` | `STRIPE_SEAT_PRICE_*` not set (V2 only) | Set seat price IDs or disable V2 (`PRICING_V2_ENABLED=false`) |
| `503 "New pricing features are not yet enabled"` | `PRICING_V2_ENABLED=false` but hitting V2 endpoints | Set `PRICING_V2_ENABLED=true` or use legacy checkout |
| Webhook event ignored | Price ID in Stripe doesn't match any env var | Verify Price IDs match between Stripe Dashboard and env vars |
| User not upgraded after payment | Webhook not reaching server or `_resolve_tier_from_price` returning None | Check webhook logs, verify Price ID mapping |

---

## 5. Enterprise Handling Policy

### Self-Serve Organization Plan

The Organization tier ($400/mo or $4,000/yr, 3 base seats) is available through the standard self-serve checkout flow. Customers can add up to 22 additional seats (25 total) via the seat add-on mechanism.

### Custom Enterprise (26+ Seats)

Requests exceeding 25 seats are blocked at the API level (`MAX_SELF_SERVE_SEATS = 25`). These customers require a sales-assisted path:

1. **Intake:** Customer clicks "Contact Sales" on the pricing page (routed to `/contact`).
2. **Scoping:** Sales determines seat count, SLA requirements, volume discount eligibility.
3. **Stripe Setup:** Ops creates a custom Stripe subscription with:
   - Custom product/price for the agreed terms
   - Manual subscription creation via Stripe Dashboard or API
4. **Provisioning:** Manually set user tier to `enterprise` and seat allocation in the database.
5. **Ongoing:** Custom subscriptions are managed through the Stripe Dashboard, not the self-serve flow.

### Custom Terms Triggers

- 26+ seats
- Volume discount requests
- Custom SLA or support terms
- Annual contract with non-standard payment terms
- Multi-entity (holding company) licensing

---

## 6. Launch Sequence

### Pre-Launch (Day -1)

- [ ] All Stripe objects created (Products, Prices, Coupons, Webhook, Portal)
- [ ] All env vars set in deployment config
- [ ] `pytest` + `npm run build` pass
- [ ] Staging deployment verified with test keys (`sk_test_*`)

### Launch (Day 0)

- [ ] Deploy with production Stripe keys (`sk_live_*`)
- [ ] Verify startup logs show "Stripe Billing: enabled"
- [ ] Verify no "Billing config" warnings in logs
- [ ] Run smoke tests from Section 3
- [ ] Test end-to-end checkout with a real card on lowest tier

### Post-Launch (Day 1-7)

- [ ] Monitor webhook delivery in Stripe Dashboard (aim for 100% success)
- [ ] Monitor application logs for billing errors
- [ ] Review `/metrics` for checkout counters (if Prometheus enabled)
- [ ] Verify subscription status syncs correctly after payment

### V2 Pricing Activation (When Ready)

- [ ] Set `PRICING_V2_ENABLED=true`
- [ ] Set `SEAT_ENFORCEMENT_MODE=soft` (30-day grace)
- [ ] Follow the [Pricing V2 Rollback Runbook](pricing-rollback.md)
