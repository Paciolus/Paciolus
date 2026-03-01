'use client'

/**
 * Checkout page — Sprint 370 + Self-Serve Checkout.
 * Phase LIX Sprint A: updated for Solo/Team pricing.
 * Phase LIX Sprint E: seat_count + promo_code passthrough.
 * Self-Serve Checkout: seat stepper, promo code input, price breakdown.
 *
 * Shows plan summary with interactive seat/promo controls and redirects to Stripe Checkout.
 * URL params: ?plan=solo|team&interval=monthly|annual&seats=N
 */

import { Suspense, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { useBilling } from '@/hooks/useBilling'

const PLAN_LABELS: Record<string, string> = {
  solo: 'Solo',
  team: 'Team',
}

const PLAN_PRICES: Record<string, Record<string, number>> = {
  solo: { monthly: 5000, annual: 50000 },
  team: { monthly: 13000, annual: 130000 },
}

const BASE_SEATS: Record<string, number> = {
  solo: 1,
  team: 3,
}

const MAX_ADDITIONAL_SEATS = 22

/** Whether a plan supports additional seats. */
function supportsSeats(plan: string): boolean {
  return plan === 'team'
}

/** Calculate per-seat price in cents at the given seat position (1-indexed add-on). */
function seatPriceCents(seatIndex: number, interval: string): number {
  // Tiers match SEAT_PRICE_TIERS in price_config.py
  // Seats 4-10 (add-on index 1-7): $80/mo, $800/yr
  // Seats 11-25 (add-on index 8-22): $70/mo, $700/yr
  const seatNumber = 3 + seatIndex // seat 4 = add-on index 1
  if (seatNumber <= 10) {
    return interval === 'annual' ? 80000 : 8000
  }
  return interval === 'annual' ? 70000 : 7000
}

/** Calculate total seat add-on cost in cents. */
function totalSeatCost(additionalSeats: number, interval: string): number {
  let total = 0
  for (let i = 1; i <= additionalSeats; i++) {
    total += seatPriceCents(i, interval)
  }
  return total
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
  const initialSeats = Number.isFinite(seatsParam) && seatsParam > 0 ? Math.min(seatsParam, MAX_ADDITIONAL_SEATS) : 0

  const [additionalSeats, setAdditionalSeats] = useState(initialSeats)
  const [promoCode, setPromoCode] = useState('')
  const [promoError, setPromoError] = useState<string | null>(null)
  const [promoApplied, setPromoApplied] = useState(false)
  const [dpaAccepted, setDpaAccepted] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { createCheckoutSession, error } = useBilling()

  const requiresDpa = plan === 'team'

  const planLabel = PLAN_LABELS[plan]
  const basePriceCents = PLAN_PRICES[plan]?.[interval]

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

  const seatsCost = supportsSeats(plan) ? totalSeatCost(additionalSeats, interval) : 0
  const subtotal = basePriceCents + seatsCost
  const baseSeats = BASE_SEATS[plan] ?? 1
  const totalSeats = baseSeats + (supportsSeats(plan) ? additionalSeats : 0)

  function handleSeatChange(delta: number) {
    setAdditionalSeats(prev => Math.max(0, Math.min(MAX_ADDITIONAL_SEATS, prev + delta)))
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
    if (requiresDpa && !dpaAccepted) {
      return
    }
    setIsLoading(true)
    const url = await createCheckoutSession(
      plan,
      interval,
      supportsSeats(plan) && additionalSeats > 0 ? additionalSeats : undefined,
      promoApplied ? promoCode.trim().toUpperCase() : undefined,
      requiresDpa ? dpaAccepted : undefined,
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
            {interval === 'annual' ? 'Billed annually' : 'Billed monthly'}.
            {' '}Cancel anytime.
          </p>
          <p className="text-sm text-content-muted mt-1">
            {baseSeats} seat{baseSeats > 1 ? 's' : ''} included
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
                  disabled={additionalSeats >= MAX_ADDITIONAL_SEATS}
                  className="w-8 h-8 rounded-sm border border-theme text-content-primary flex items-center justify-center hover:bg-oatmeal-200 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                  aria-label="Add seat"
                >
                  +
                </button>
              </div>
            </div>
            {additionalSeats > 0 && (
              <div className="text-sm text-content-secondary space-y-1">
                {additionalSeats <= 7 && (
                  <p>
                    <span className="font-mono tabular-nums">{additionalSeats}</span> seat{additionalSeats > 1 ? 's' : ''} @ {formatPerUnit(seatPriceCents(1, interval), interval)}
                  </p>
                )}
                {additionalSeats > 7 && (
                  <>
                    <p>
                      <span className="font-mono tabular-nums">7</span> seats @ {formatPerUnit(seatPriceCents(1, interval), interval)}
                    </p>
                    <p>
                      <span className="font-mono tabular-nums">{additionalSeats - 7}</span> seat{additionalSeats - 7 > 1 ? 's' : ''} @ {formatPerUnit(seatPriceCents(8, interval), interval)}
                    </p>
                  </>
                )}
                <p className="text-content-muted pt-1">
                  Total: <span className="font-mono tabular-nums">{totalSeats}</span> seats ({baseSeats} included + {additionalSeats} add-on)
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
                className="text-sm text-content-muted hover:text-content-secondary transition-colors"
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
                className="flex-1 px-3 py-2 border border-theme rounded-sm bg-surface-page text-content-primary font-mono text-sm placeholder:text-content-muted focus:outline-hidden focus:ring-1 focus:ring-sage-500"
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
            <p className="text-xs text-content-muted mt-2">
              Annual billing saves ~17% compared to monthly.
            </p>
          )}
        </div>

        {/* DPA Acceptance (Team / Organization tiers) — Sprint 459 */}
        {requiresDpa && (
          <div className="border border-theme rounded-lg p-5 mb-6">
            <label className="flex items-start gap-3 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={dpaAccepted}
                onChange={e => setDpaAccepted(e.target.checked)}
                className="mt-0.5 h-4 w-4 shrink-0 accent-sage-600"
                aria-required="true"
              />
              <span className="text-sm text-content-secondary leading-relaxed">
                I accept the{' '}
                <Link
                  href="/trust"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sage-600 hover:underline"
                >
                  Data Processing Addendum
                </Link>
                {' '}(v1.0) on behalf of my organisation. This is required for the Team plan.
              </span>
            </label>
          </div>
        )}

        {/* API Error */}
        {error && (
          <div className="bg-clay-50 border border-clay-200 text-clay-700 rounded-lg p-3 mb-4 text-sm" role="alert">
            {error}
          </div>
        )}

        {/* Checkout Button */}
        <button
          onClick={handleCheckout}
          disabled={isLoading || (requiresDpa && !dpaAccepted)}
          className="w-full py-3 bg-sage-600 text-white rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Redirecting to payment...' : 'Continue to Checkout'}
        </button>

        <p className="text-xs text-content-muted text-center mt-4">
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
