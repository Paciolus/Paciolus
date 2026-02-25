# Weekly Pricing Review Template

> Phase LX — Run every Monday. Takes ~10 minutes.

## How to Pull the Report

```bash
# API call (requires admin JWT)
curl -H "Authorization: Bearer $TOKEN" \
  https://api.paciolus.com/billing/analytics/weekly-review

# Or via the billing dashboard (when available)
```

## Review Template

### Week of: ____/____/____

| # | Metric | This Week | Last Week | Delta | Status |
|---|--------|-----------|-----------|-------|--------|
| 1 | Trial starts | | | | |
| 2 | Trial → paid rate | | | | |
| 3 | Paid by plan (Solo) | | | | |
| 4 | Paid by plan (Team) | | | | |
| 5 | Paid by plan (Enterprise) | | | | |
| 6 | Avg seats (Team) | | | | |
| 7 | Avg seats (Enterprise) | | | | |
| 8 | Cancellations (total) | | | | |
| 9 | Top cancel reason | | | | |
| 10 | Payment failures | | | | |

**Status key:** OK / WATCH / ACT (see thresholds in `pricing-guardrails.md`)

### Health Thresholds (quick reference)

| Metric | Healthy | Watch | Act |
|--------|---------|-------|-----|
| Trial starts / week | >= 5 | 2–4 | < 2 |
| Trial → paid rate | >= 20% | 10–19% | < 10% (30+ trials) |
| Cancellations / week | < 3 | 3–5 | > 5 (2+ weeks) |
| "Too expensive" cancels | < 30% | 30–50% | > 50% |
| Payment failure rate | < 5% | 5–10% | > 10% |

### Observations

_What stood out this week?_

-
-
-

### Decisions

_Any pricing levers to pull? If yes, which ONE lever and why?_

- [ ] No action needed
- [ ] Action: _____________ (document in `tasks/decisions/pricing-weekly-log.md`)

### Guardrail Check

- [ ] Still within 90-day price freeze? (Launch date: ____/____/____)
- [ ] Only one lever changed at a time?
- [ ] Previous lever change observation window complete?

---

## Metric Definitions

### 1. Trial Starts
New users who entered a free trial period. Source: `billing_events` where `event_type = 'trial_started'`.

### 2. Trial-to-Paid Rate
Percentage of trials that converted to a paid subscription. Formula: `trial_converted / trial_started`. Lagging indicator — a trial started this week may convert next week.

### 3. Paid by Plan
Point-in-time count of active paid subscriptions grouped by tier (Solo, Team, Enterprise). Source: `subscriptions` table where `status IN ('active', 'trialing')`.

### 4. Average Seats
Average `seat_count + additional_seats` for Team and Enterprise plans. Indicates expansion revenue potential. Only meaningful with 3+ subscribers per tier.

### 5. Cancellations by Reason
Count of `subscription_canceled` events grouped by the `reason` field from the cancel request body. Common reasons: `too_expensive`, `missing_feature`, `switched_competitor`, `no_longer_needed`, `unspecified`.

### 6. Payment Failures
Count of `payment_failed` events. High rates suggest card/billing friction, not pricing issues. Check Stripe retry settings and dunning configuration.

---

## Cadence

| Frequency | Action |
|-----------|--------|
| Weekly (Monday) | Pull report, fill template, log observations |
| Monthly | Review 4-week trend, decide if any lever needs pulling |
| Quarterly | Full pricing review against competitive landscape |
| 90-day mark | Price freeze expires, full strategy review |
