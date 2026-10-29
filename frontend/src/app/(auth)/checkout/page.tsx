'use client'

/**
 * Checkout page — Self-Serve Checkout.
 * Supports Solo/Team pricing with seat_count + promo_code passthrough.
 * Includes seat stepper, promo code input, and price breakdown.
 *
 * Shows plan summary with interactive seat/promo controls and redirects to Stripe Checkout.
 * URL params: ?plan=solo|professional|enterprise&interval=monthly|annual&seats=N
 */

import { Suspense, useEffect, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { useBilling } from '@/hooks/useBilling'
import { baseSeats, getTier, maxAdditionalSeats, seatPriceDollars, tierPriceDollars, TRIAL_DAYS, trialChargeDate } from '@/domain/pricing'

// Sprint 818: every price, seat count and seat limit comes from
// `@/domain/pricing` — the same source the pricing page renders.

/** Base plan price in cents, or undefined for an unknown plan or interval. */
function planPriceCents(plan: string, interval: string): number | undefined {
  if (interval !== 'monthly' && interval !== 'annual') return undefined
  const dollars = tierPriceDollars(plan, interval)
  return dollars === undefined ? undefined : dollars * 100
}

/** Whether a plan supports additional seats. */
function supportsSeats(plan: string): boolean {
  return maxAdditionalSeats(plan) > 0
}

/** Per-seat price in cents (flat rate per tier). */
function seatPriceCents(interval: string, plan: string): number {
  return seatPriceDollars(plan, interval === 'annual' ? 'annual' : 'monthly') * 100
}

/** Calculate total seat add-on cost in cents. */
function totalSeatCost(additionalSeats: number, interval: string, plan: string): number {
  if (additionalSeats <= 0) return 0
  return additionalSeats * seatPriceCents(interval, plan)
}

/** Format cents as a currency string. */
function formatCents(cents: number): string {
  const dollars = cents / 100
  return dollars.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

/** Format cents for per-unit display (e.g., $80/mo). */
function formatPerUnit(cents: number, interval: string): string {
  return `${formatCents(cents)}/${interval === 'annual' ? 'yr' : 'mo'}`
}

function CheckoutContent() {
  const searchParams = useSearchParams()
  const plan = searchParams.get('plan') ?? ''
  const interval = searchParams.get('interval') ?? 'monthly'
  const seatsParam = parseInt(searchParams.get('seats') ?? '0', 10)
  const initialSeats = Number.isFinite(seatsParam) && seatsParam > 0 ? Math.min(seatsParam, maxAdditionalSeats(plan)) : 0

  const [additionalSeats, setAdditionalSeats] = useState(initialSeats)
  const [promoCode, setPromoCode] = useState('')
  const [promoError, setPromoError] = useState<string | null>(null)
  const [promoApplied, setPromoApplied] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { createCheckoutSession, error, subscription, fetchSubscription } = useBilling()
  useEffect(() => {
    void fetchSubscription()
  }, [fetchSubscription])
  // PR #234 review: mirror backend/billing/checkout_orchestrator.py — only a
  // new subscription (none yet, or a cancelled one) gets the trial, so only
  // then may the disclosure promise "no charge today".
  const trialEligible = subscription === null ? null : !subscription.id || subscription.status === 'canceled'

  const offersDpa = plan === 'professional' || plan === 'enterprise'

  const planLabel = getTier(plan)?.name
  const basePriceCents = planPriceCents(plan, interval)

  if (!planLabel || basePriceCents === undefined) {
    return (
      <div className="min-h-screen bg-surface-page flex items-center justify-center px-6">
        <div className="bg-surface-card border border-theme rounded-lg p-8 max-w-md text-center">
          <h1 className="font-serif text-xl text-content-primary mb-4">Invalid Plan</h1>
          <p className="text-content-secondary mb-6">The selected plan is not available.</p>
          <Link href="/pricing" className="text-sage-600 font-sans font-medium hover:underline">
            View Plans
          </Link>
        </div>
      </div>
    )
  }

  const seatsCost = supportsSeats(plan) ? totalSeatCost(additionalSeats, interval, plan) : 0
  const subtotal = basePriceCents + seatsCost
  const includedSeats = baseSeats(plan)
  const totalSeats = includedSeats + (supportsSeats(plan) ? additionalSeats : 0)

  const planMaxSeats = maxAdditionalSeats(plan)

  function handleSeatChange(delta: number) {
    setAdditionalSeats(prev => Math.max(0, Math.min(planMaxSeats, prev + delta)))
  }

  function handleApplyPromo() {
    setPromoError(null)
    const code = promoCode.trim().toUpperCase()
    if (!code) {
      setPromoError('Enter a promo code.')
      return
    }

    // Client-side validation mirrors backend PROMO_CODES
    const promoIntervals: Record<string, string> = {
      MONTHLY20: 'monthly',
      ANNUAL10: 'annual',
    }
    const targetInterval = promoIntervals[code]
    if (!targetInterval) {
      setPromoError(`Unknown promo code: ${code}`)
      return
    }
    if (targetInterval !== interval) {
      setPromoError(`"${code}" is only valid for ${targetInterval} plans.`)
      return
    }
    setPromoApplied(true)
  }

  function handleClearPromo() {
    setPromoCode('')
    setPromoApplied(false)
    setPromoError(null)
  }

  async function handleCheckout() {
    setIsLoading(true)
    const url = await createCheckoutSession(
      plan,
      interval,
      supportsSeats(plan) && additionalSeats > 0 ? additionalSeats : undefined,
      promoApplied ? promoCode.trim().toUpperCase() : undefined,
      undefined,
    )
    if (url) {
      window.location.href = url
    }
    setIsLoading(false)
  }

  return (
    <div className="min-h-screen bg-surface-page flex items-center justify-center px-6 py-12">
      <div className="bg-surface-card border border-theme rounded-lg p-8 max-w-lg w-full">
        <h1 className="font-serif text-2xl text-content-primary mb-6">Confirm Your Plan</h1>

        {/* Plan Summary */}
        <div className="border border-theme rounded-lg p-5 mb-6">
          <div className="flex justify-between items-baseline mb-1">
            <span className="font-serif text-lg text-content-primary">{planLabel}</span>
            <span className="font-mono text-lg text-sage-600">
              {formatPerUnit(basePriceCents, interval)}
            </span>
          </div>
          <p className="text-sm text-content-secondary">
            {interval === 'annual' ? 'Billed annually' : 'Billed monthly'} from your start date until you cancel.
          </p>
          <p className="text-sm text-content-tertiary mt-1">
            {includedSeats} seat{includedSeats > 1 ? 's' : ''} included
          </p>
        </div>

        {/* Seat Stepper (team only) */}
        {supportsSeats(plan) && (
          <div className="border border-theme rounded-lg p-5 mb-6">
            <div className="flex items-center justify-between mb-3">
              <span className="font-sans text-sm font-medium text-content-primary">Additional Seats</span>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleSeatChange(-1)}
                  disabled={additionalSeats === 0}
                  className="w-8 h-8 rounded-sm border border-theme text-content-primary flex items-center justify-center hover:bg-oatmeal-200 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                  aria-label="Remove seat"
                >
                  -
                </button>
                <span className="font-mono text-lg text-content-primary w-8 text-center tabular-nums">
                  {additionalSeats}
                </span>
                <button
                  onClick={() => handleSeatChange(1)}
                  disabled={additionalSeats >= planMaxSeats}
                  className="w-8 h-8 rounded-sm border border-theme text-content-primary flex items-center justify-center hover:bg-oatmeal-200 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                  aria-label="Add seat"
                >
                  +
                </button>
              </div>
            </div>
            {additionalSeats > 0 && (
              <div className="text-sm text-content-secondary space-y-1">
                <p>
                  <span className="font-mono tabular-nums">{additionalSeats}</span> seat{additionalSeats > 1 ? 's' : ''} @ {formatPerUnit(seatPriceCents(interval, plan), interval)}
                </p>
                <p className="text-content-tertiary pt-1">
                  Total: <span className="font-mono tabular-nums">{totalSeats}</span> seats ({includedSeats} included + {additionalSeats} add-on)
                </p>
              </div>
            )}
          </div>
        )}

        {/* Promo Code */}
        <div className="border border-theme rounded-lg p-5 mb-6">
          <label htmlFor="promo-code" className="font-sans text-sm font-medium text-content-primary block mb-2">
            Promo Code
          </label>
          {promoApplied ? (
            <div className="flex items-center justify-between">
              <span className="text-sm text-sage-600 font-mono">{promoCode.trim().toUpperCase()}</span>
              <button
                onClick={handleClearPromo}
                className="text-sm text-content-tertiary hover:text-content-secondary transition-colors"
              >
                Remove
              </button>
            </div>
          ) : (
            <div className="flex gap-2">
              <input
                id="promo-code"
                type="text"
                value={promoCode}
                onChange={e => setPromoCode(e.target.value)}
                placeholder="Enter code"
                maxLength={50}
                className="flex-1 px-3 py-2 border border-theme rounded-sm bg-surface-page text-content-primary font-mono text-sm placeholder:text-content-tertiary focus:outline-hidden focus:ring-1 focus:ring-sage-500"
              />
              <button
                onClick={handleApplyPromo}
                disabled={!promoCode.trim()}
                className="px-4 py-2 border border-sage-600 text-sage-600 rounded-sm font-sans text-sm font-medium hover:bg-sage-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Apply
              </button>
            </div>
          )}
          {promoError && (
            <p className="text-sm text-clay-600 mt-2" role="alert">{promoError}</p>
          )}
        </div>

        {/* Price Breakdown */}
        <div className="border border-theme rounded-lg p-5 mb-6">
          <h2 className="font-serif text-base text-content-primary mb-3">Price Breakdown</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between text-content-secondary">
              <span>{planLabel} plan</span>
              <span className="font-mono tabular-nums">{formatPerUnit(basePriceCents, interval)}</span>
            </div>
            {supportsSeats(plan) && additionalSeats > 0 && (
              <div className="flex justify-between text-content-secondary">
                <span>{additionalSeats} additional seat{additionalSeats > 1 ? 's' : ''}</span>
                <span className="font-mono tabular-nums">{formatPerUnit(seatsCost, interval)}</span>
              </div>
            )}
            {promoApplied && (
              <div className="flex justify-between text-sage-600">
                <span>Promo: {promoCode.trim().toUpperCase()}</span>
                <span className="font-mono">Applied at checkout</span>
              </div>
            )}
            <div className="border-t border-theme pt-2 flex justify-between font-medium text-content-primary">
              <span>Total</span>
              <span className="font-mono tabular-nums text-sage-600">
                {formatPerUnit(subtotal, interval)}
              </span>
            </div>
          </div>
          {interval === 'annual' && (
            <p className="text-xs text-content-tertiary mt-2">
              Annual billing saves ~17% compared to monthly.
            </p>
          )}
        </div>

        {/* Sprint 844: the DPA checkbox linked to a page that called the DPA "planned". Removed until
            a counsel-reviewed DPA is published at a real URL; organizations can request one meanwhile. */}
        {offersDpa && (
          <p className="text-xs text-content-tertiary mb-6">
            Need a Data Processing Addendum for your organization?{' '}
            <Link href="/contact?inquiry_type=organization" className="text-sage-600 hover:underline">
              Request one
            </Link>
            .
          </p>
        )}

        {/* API Error */}
        {error && (
          <div className="bg-clay-50 border border-clay-200 text-clay-700 rounded-lg p-3 mb-4 text-sm" role="alert">
            {error}
          </div>
        )}

        {/* Checkout Button */}
        {/* Sprint 842: trial and auto-renewal terms, stated before the card is collected */}
        <div className="border border-theme rounded-lg p-5 mb-6" data-testid="trial-disclosure">
          <h2 className="font-serif text-base text-content-primary mb-2">{trialEligible === false ? 'Charge and renewal' : 'Trial and renewal'}</h2>
          {trialEligible === null && (
            <p className="text-sm text-content-secondary">Checking your billing terms…</p>
          )}
          {trialEligible === true && (
            <p className="text-sm text-content-secondary leading-relaxed">
              A card is required. This subscription starts with a {TRIAL_DAYS}-day free trial, so you
              won&apos;t be charged today. On{' '}
              <strong className="text-content-primary">{trialChargeDate(new Date()).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</strong>{' '}
              we will charge <strong className="font-mono text-content-primary">{formatCents(subtotal)}</strong>
              {promoApplied ? ' less your promo discount' : ''}, then{' '}
              <span className="font-mono">{formatCents(subtotal)}</span> every {interval === 'annual' ? 'year' : 'month'} until you cancel.
              Cancel before then and you won&apos;t be charged.
            </p>
          )}
          {trialEligible === false && (
            <p className="text-sm text-content-secondary leading-relaxed">
              You already have a subscription, so there is no free trial. The new price of{' '}
              <strong className="font-mono text-content-primary">{formatCents(subtotal)}</strong>
              {promoApplied ? ' (less your promo discount)' : ''} per {interval === 'annual' ? 'year' : 'month'} may be
              charged today, then every {interval === 'annual' ? 'year' : 'month'} until you cancel.
            </p>
          )}
          <p className="text-xs text-content-tertiary mt-2">
            You can cancel at any time in Settings &rarr; Billing.
          </p>
        </div>

        <button
          onClick={handleCheckout}
          disabled={isLoading}
          className="w-full py-3 bg-sage-600 text-oatmeal-50 rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Redirecting to payment...' : 'Continue to Checkout'}
        </button>

        <p className="text-xs text-content-tertiary text-center mt-4">
          You will be redirected to our secure payment partner, Stripe.
        </p>

        <div className="text-center mt-3">
          <Link href="/pricing" className="text-sm text-content-secondary hover:text-content-primary transition-colors">
            Back to Plans
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-surface-page flex items-center justify-center">
        <div className="text-content-secondary">Loading checkout...</div>
      </div>
    }>
      <CheckoutContent />
    </Suspense>
  )
}
