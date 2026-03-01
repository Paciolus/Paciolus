# Pricing Guardrails & Decision Rubric

> Phase LX — Post-Launch Pricing Control System

## 1. 90-Day Price Freeze Policy

**Rule:** No list price changes for the first 90 days after launch unless a severe conversion failure is detected.

### What qualifies as "severe conversion failure"

All three conditions must be true:
1. Trial-to-paid rate < 5% after 30+ trials
2. Trend is declining week-over-week for 3 consecutive weeks
3. Qualitative signal confirms price (not product) is the barrier (e.g., cancel reasons cite "too expensive" at >50%)

### What does NOT justify breaking the freeze
- Low absolute numbers in the first 2 weeks (insufficient sample)
- A single bad week followed by recovery
- Competitor price changes (respond with positioning, not price)
- Feature requests ("we'd pay if you had X" is a product signal, not a price signal)

## 2. One Lever at a Time

**Rule:** Change only one pricing variable per adjustment cycle (minimum 4-week observation window).

### Pricing levers (ordered by impact)
| Lever | Example | Observation window |
|-------|---------|-------------------|
| Trial length | 7 days → 14 days | 4 weeks |
| Promotional discount | Launch 30-day 20% coupon | 4 weeks |
| Tier price | Solo $50 → $39/mo | 6 weeks |
| Tier bundling | Move tool X from Team to Solo | 4 weeks |
| Seat pricing | $80/seat → $60/seat | 4 weeks |
| Annual discount | 17% → 25% | 6 weeks |

### Why one at a time
Multiple simultaneous changes make attribution impossible. If you change the Solo price AND extend the trial period simultaneously, you cannot determine which change drove the result.

## 3. Decision Rubric: "When to Change Price"

### Weekly review checklist

Run every Monday morning. Takes 10 minutes.

1. **Pull `GET /billing/analytics/weekly-review`**
2. **Check the 5 metrics against thresholds below**
3. **If any threshold is breached, move to the action table**

### Metric thresholds

| Metric | Healthy | Watch | Act |
|--------|---------|-------|-----|
| Trial starts / week | >= 5 | 2–4 | < 2 (acquisition problem, not pricing) |
| Trial → paid rate | >= 20% | 10–19% | < 10% after 30+ trials |
| Cancellations / week | < 3 | 3–5 | > 5 sustained 2+ weeks |
| Cancel reason: "too expensive" | < 30% of cancels | 30–50% | > 50% of cancels |
| Payment failure rate | < 5% of active | 5–10% | > 10% (card/billing issue) |

### Action table

| Signal | Likely cause | First response | Escalation |
|--------|-------------|----------------|------------|
| Low trial starts | Awareness / positioning | Improve marketing copy, add case studies | Not a pricing issue |
| Low conversion, price not cited | Product gap | Review feature requests from trials | Not a pricing issue |
| Low conversion, price cited | Price too high for perceived value | Extend trial to 14 days OR add limited-time promo | If still low after 4 weeks: consider tier price reduction |
| High cancel "too expensive" | Price/value mismatch | Survey churned users for specific pain | After 4 weeks of data: evaluate tier restructuring |
| High cancel "missing feature" | Feature gap | Prioritize feature in roadmap | Not a pricing issue |
| Rising payment failures | Card/billing friction | Check Stripe retry settings, add dunning emails | Stripe support ticket |

## 4. Escalation Protocol

### Level 1: Automated monitoring (always on)
- Prometheus counters + Grafana alerts (if configured)
- `billing_events_total` by event_type/tier
- `active_trials` and `active_subscriptions` gauges

### Level 2: Weekly founder review
- `GET /billing/analytics/weekly-review` every Monday
- 5-minute scan against threshold table
- Log decision in `tasks/decisions/pricing-weekly-log.md`

### Level 3: Price change proposal
- Only triggered by Level 2 review finding "Act" threshold
- Document: what lever, why, expected impact, rollback plan
- Observe for full observation window before evaluating
- One lever at a time (see Section 2)

## 5. Rollback Protocol

If a price change produces negative results:

1. **Grandfather existing subscribers** at their current rate
2. **Revert list price** in Stripe Dashboard
3. **Update `price_config.py`** and environment variables
4. **Record decision** in `tasks/decisions/pricing-weekly-log.md`
5. **Wait minimum 4 weeks** before next change attempt

## 6. Event Taxonomy Reference

| Event Type | Trigger | Instrumented In |
|-----------|---------|-----------------|
| `trial_started` | Checkout completed with trialing status | `webhook_handler.handle_checkout_completed` |
| `trial_converted` | Subscription updated: trialing → active | `webhook_handler.handle_subscription_updated` |
| `trial_expired` | Stripe trial_will_end event (3 days before) | `webhook_handler.handle_subscription_trial_will_end` |
| `subscription_created` | Checkout completed (non-trial) | `webhook_handler.handle_checkout_completed` |
| `subscription_upgraded` | Subscription updated: lower → higher tier | `webhook_handler.handle_subscription_updated` |
| `subscription_downgraded` | Subscription updated: higher → lower tier | `webhook_handler.handle_subscription_updated` |
| `subscription_canceled` | User-initiated cancel (with optional reason) | `routes/billing.cancel_subscription_endpoint` |
| `subscription_churned` | Stripe subscription deleted | `webhook_handler.handle_subscription_deleted` |
| `payment_failed` | Invoice payment failed | `webhook_handler.handle_invoice_payment_failed` |
| `payment_recovered` | Past-due invoice paid | `webhook_handler.handle_invoice_paid` |

## 7. Dashboard Query Templates

### Prometheus / Grafana

```promql
# Trial starts per week
increase(paciolus_billing_events_total{event_type="trial_started"}[7d])

# Trial conversion rate (7-day window)
increase(paciolus_billing_events_total{event_type="trial_converted"}[7d])
/
increase(paciolus_billing_events_total{event_type="trial_started"}[7d])

# Cancellations by tier
increase(paciolus_billing_events_total{event_type="subscription_canceled"}[7d])

# Active subscriptions by tier
paciolus_active_subscriptions

# Payment failure rate
increase(paciolus_billing_events_total{event_type="payment_failed"}[7d])
/
paciolus_active_subscriptions
```

### Direct SQL (ad-hoc analysis)

```sql
-- Trial starts this week
SELECT COUNT(*) FROM billing_events
WHERE event_type = 'trial_started'
  AND created_at >= date_trunc('week', CURRENT_DATE);

-- Trial-to-paid conversion rate (last 30 days)
SELECT
  SUM(CASE WHEN event_type = 'trial_started' THEN 1 ELSE 0 END) AS starts,
  SUM(CASE WHEN event_type = 'trial_converted' THEN 1 ELSE 0 END) AS conversions,
  ROUND(
    SUM(CASE WHEN event_type = 'trial_converted' THEN 1 ELSE 0 END)::numeric /
    NULLIF(SUM(CASE WHEN event_type = 'trial_started' THEN 1 ELSE 0 END), 0),
    4
  ) AS rate
FROM billing_events
WHERE event_type IN ('trial_started', 'trial_converted')
  AND created_at >= CURRENT_DATE - INTERVAL '30 days';

-- Paid subscribers by plan (point-in-time)
SELECT tier, COUNT(*) FROM subscriptions
WHERE status IN ('active', 'trialing')
GROUP BY tier ORDER BY COUNT(*) DESC;

-- Average seats for Team
SELECT tier, AVG(seat_count + additional_seats) AS avg_seats
FROM subscriptions
WHERE status IN ('active', 'trialing') AND tier IN ('team')
GROUP BY tier;

-- Cancellation reasons (last 30 days)
SELECT
  metadata_json::json->>'reason' AS reason,
  COUNT(*) AS count
FROM billing_events
WHERE event_type = 'subscription_canceled'
  AND created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY reason ORDER BY count DESC;

-- Week-over-week trial starts (last 8 weeks)
SELECT
  date_trunc('week', created_at) AS week,
  COUNT(*) AS trial_starts
FROM billing_events
WHERE event_type = 'trial_started'
  AND created_at >= CURRENT_DATE - INTERVAL '8 weeks'
GROUP BY week ORDER BY week;
```
