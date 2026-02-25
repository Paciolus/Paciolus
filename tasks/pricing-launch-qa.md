# Pricing Launch — Manual QA Checklist

**Date:** ___________
**Tester:** ___________
**Environment:** ☐ Staging ☐ Production
**Stripe Mode:** ☐ Test ☐ Live

---

## 1. Marketing Page Visual QA

### Pricing Page (`/pricing`)
- [ ] Monthly/Annual billing toggle works
- [ ] Solo card shows $50/mo and $500/yr
- [ ] Team card shows $130/mo and $1,300/yr
- [ ] Organization card shows $400/mo and $4,000/yr
- [ ] Enterprise card shows "Custom" with "Contact Sales" CTA
- [ ] No "Free" tier card is displayed
- [ ] Each paid tier has "Start Free Trial" CTA
- [ ] CTA links include correct `?plan=` and `&interval=` params
- [ ] Annual toggle updates CTA links to `interval=annual`
- [ ] "7-day free trial" copy is present
- [ ] "~17% savings" copy shows on annual toggle
- [ ] Comparison table has 4 columns (Solo, Team, Organization, Enterprise)
- [ ] Seat pricing info visible: $80/seat/mo (4-10), $70/seat/mo (11-25)
- [ ] FAQ questions render correctly
- [ ] Plan estimator recommends Solo (not Free) for minimal inputs
- [ ] Mobile responsive: cards stack vertically
- [ ] Mobile responsive: comparison table scrolls horizontally

### Pricing Page Accessibility
- [ ] All buttons and links are keyboard navigable
- [ ] Toggle has visible focus indicator
- [ ] Screen reader announces tier names and prices

---

## 2. Checkout Flow QA

### Solo Checkout
- [ ] `/checkout?plan=solo&interval=monthly` renders Solo summary with $50/mo
- [ ] `/checkout?plan=solo&interval=annual` renders Solo summary with $500/yr
- [ ] Seat stepper is NOT visible on Solo plan
- [ ] "Continue to Checkout" redirects to Stripe
- [ ] Stripe checkout shows correct plan and price
- [ ] Success URL returns to app correctly
- [ ] Cancel URL returns to pricing page

### Team Checkout
- [ ] `/checkout?plan=team&interval=monthly` renders Team summary with $130/mo
- [ ] `/checkout?plan=team&interval=annual` renders Team summary with $1,300/yr
- [ ] Seat stepper is visible with "3 seats included" label
- [ ] Seat stepper increments/decrements correctly
- [ ] Seat stepper caps at 22 additional seats
- [ ] Price breakdown shows base + seat add-on costs
- [ ] Stripe checkout shows dual line items (base + seats) when seats > 0

### Organization (Enterprise) Checkout
- [ ] `/checkout?plan=enterprise&interval=monthly` renders Organization summary
- [ ] `/checkout?plan=enterprise&interval=annual` renders Organization summary
- [ ] Seat stepper visible and functional

### Promo Code
- [ ] MONTHLY20 accepted for monthly plans
- [ ] MONTHLY20 rejected for annual plans (error message shown)
- [ ] ANNUAL10 accepted for annual plans
- [ ] ANNUAL10 rejected for monthly plans (error message shown)
- [ ] Unknown promo code shows error
- [ ] Promo code can be removed after applying
- [ ] Applied promo shows in price breakdown as "Applied at checkout"
- [ ] Case insensitive: "monthly20" works

### Edge Cases
- [ ] Invalid plan param (e.g., `?plan=gold`) shows "Invalid Plan" message
- [ ] Missing plan param shows "Invalid Plan" message
- [ ] "Back to Plans" link returns to `/pricing`
- [ ] Annual plans show "~17% savings" note

---

## 3. Billing Dashboard QA

### Plan Card (`/settings/billing`)
- [ ] Free user sees "Free" tier with "Active" badge
- [ ] Solo user sees "Solo" tier with correct status badge
- [ ] Team user sees "Team" tier with correct status badge
- [ ] Enterprise user sees "Organization" tier with correct status badge
- [ ] Trialing user sees "Trialing" badge with trial conversion date
- [ ] Active user sees "Active" badge with next billing date
- [ ] Past Due user sees "Past Due" badge
- [ ] Cancel-at-period-end shows warning with end date

### Usage Meters
- [ ] Diagnostics used/limit displays correctly
- [ ] Clients used/limit displays correctly
- [ ] Unlimited shows correctly for Team/Enterprise

### Cancel/Reactivate
- [ ] Cancel button opens CancelModal
- [ ] CancelModal for active shows "Cancel Subscription" heading
- [ ] CancelModal for trialing shows "Cancel Trial" heading
- [ ] Cancel confirmation sets cancel_at_period_end
- [ ] Reactivate button appears when cancel_at_period_end is true
- [ ] Reactivate confirmation clears cancel_at_period_end

### Upgrade Modal
- [ ] Shows Solo, Team, Organization cards
- [ ] "Current" badge on current tier
- [ ] CTA links go to `/checkout` with correct params
- [ ] Billing toggle switches prices
- [ ] Downgrade tiers don't show upgrade links

### Portal Link
- [ ] "Manage Billing" button opens Stripe portal
- [ ] Portal session created successfully

---

## 4. Stripe Dashboard Reconciliation

### Price IDs
- [ ] STRIPE_PRICE_SOLO_MONTHLY matches Stripe Dashboard
- [ ] STRIPE_PRICE_SOLO_ANNUAL matches Stripe Dashboard
- [ ] STRIPE_PRICE_TEAM_MONTHLY matches Stripe Dashboard
- [ ] STRIPE_PRICE_TEAM_ANNUAL matches Stripe Dashboard
- [ ] STRIPE_PRICE_ENTERPRISE_MONTHLY matches Stripe Dashboard
- [ ] STRIPE_PRICE_ENTERPRISE_ANNUAL matches Stripe Dashboard
- [ ] STRIPE_SEAT_PRICE_MONTHLY matches Stripe Dashboard
- [ ] STRIPE_SEAT_PRICE_ANNUAL matches Stripe Dashboard

### Coupon IDs
- [ ] STRIPE_COUPON_MONTHLY_20 exists in Stripe (20% off, 3 months)
- [ ] STRIPE_COUPON_ANNUAL_10 exists in Stripe (10% off, first invoice)

### Webhook Configuration
- [ ] Webhook endpoint registered in Stripe: `POST /billing/webhook`
- [ ] Webhook secret matches STRIPE_WEBHOOK_SECRET env var
- [ ] Events selected: checkout.session.completed, customer.subscription.updated, customer.subscription.deleted, customer.subscription.trial_will_end, invoice.payment_failed, invoice.paid

### Mode Verification
- [ ] Test mode: all test payments use test card 4242424242424242
- [ ] Live mode: real card required, real charges
- [ ] Correct mode active for environment

---

## 5. Entitlement QA

### Free Tier
- [ ] Can access trial_balance tool
- [ ] Can access flux_analysis tool
- [ ] Cannot access journal_entry_testing (403 or upgrade prompt)
- [ ] Limited to 10 diagnostics/month
- [ ] Limited to 3 clients
- [ ] Cannot access workspace
- [ ] PDF export works, Excel/CSV export blocked

### Solo Tier
- [ ] Can access 9 tools (TB, flux, JE, multi-period, prior period, adjustments, AP, bank rec, revenue)
- [ ] Cannot access fixed_asset_testing, inventory_testing, statistical_sampling
- [ ] Limited to 20 diagnostics/month
- [ ] Limited to 10 clients
- [ ] Cannot access workspace
- [ ] All export types work (PDF, Excel, CSV)

### Team Tier
- [ ] Can access all 12 tools
- [ ] Unlimited diagnostics
- [ ] Unlimited clients
- [ ] Workspace access works
- [ ] All formats supported (including ODS)

### Enterprise Tier
- [ ] Same as Team tier access
- [ ] Workspace access works

### Format Access
- [ ] Free: CSV, XLSX, XLS, TSV, TXT only
- [ ] Solo: adds QBO, OFX, IIF, PDF
- [ ] Team/Enterprise: all formats including ODS

---

## 6. Edge Cases

### Trial Expiry
- [ ] Trial expires after 7 days → user prompted to subscribe
- [ ] Expired trial user → tier reverts to free access level

### Double-Click Prevention
- [ ] Double-clicking "Continue to Checkout" only creates one session
- [ ] Button disables during loading

### Browser Navigation
- [ ] Browser back from Stripe → returns to checkout page
- [ ] Browser forward after success → doesn't recreate session

### Concurrent Sessions
- [ ] Two tabs open on checkout → only one session created
- [ ] Login in one tab, checkout in another → auth works

### Payment Failure
- [ ] Use test card 4000000000000341 → payment fails gracefully
- [ ] User status shows "Past Due"
- [ ] Retry payment succeeds → status recovers to "Active"

---

## Sign-Off

| Area | Pass | Fail | Notes |
|------|------|------|-------|
| Marketing Page | ☐ | ☐ | |
| Checkout Flow | ☐ | ☐ | |
| Billing Dashboard | ☐ | ☐ | |
| Stripe Reconciliation | ☐ | ☐ | |
| Entitlement QA | ☐ | ☐ | |
| Edge Cases | ☐ | ☐ | |

**Overall:** ☐ PASS ☐ FAIL

**Tester Signature:** ___________
**Date:** ___________
