'use client'

/**
 * Checkout page — Sprint 370.
 *
 * Shows plan summary and redirects to Stripe Checkout.
 * URL params: ?plan=starter|professional&interval=monthly|annual
 */

import { Suspense, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { useBilling } from '@/hooks/useBilling'

const PLAN_LABELS: Record<string, string> = {
  starter: 'Starter',
  professional: 'Professional',
}

const PRICES: Record<string, Record<string, string>> = {
  starter: { monthly: '$49/mo', annual: '$499/yr' },
  professional: { monthly: '$129/mo', annual: '$1,309/yr' },
}

function CheckoutContent() {
  const searchParams = useSearchParams()
  const plan = searchParams.get('plan') ?? ''
  const interval = searchParams.get('interval') ?? 'monthly'
  const [isLoading, setIsLoading] = useState(false)
  const { createCheckoutSession, error } = useBilling()

  const planLabel = PLAN_LABELS[plan]
  const price = PRICES[plan]?.[interval]

  if (!planLabel || !price) {
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

  async function handleCheckout() {
    setIsLoading(true)
    const url = await createCheckoutSession(
      plan,
      interval,
      `${window.location.origin}/checkout/success`,
      `${window.location.origin}/pricing`,
    )
    if (url) {
      window.location.href = url
    }
    setIsLoading(false)
  }

  return (
    <div className="min-h-screen bg-surface-page flex items-center justify-center px-6">
      <div className="bg-surface-card border border-theme rounded-lg p-8 max-w-md w-full">
        <h1 className="font-serif text-2xl text-content-primary mb-6">Confirm Your Plan</h1>

        <div className="border border-theme rounded-lg p-6 mb-6">
          <div className="flex justify-between items-baseline mb-2">
            <span className="font-serif text-lg text-content-primary">{planLabel}</span>
            <span className="font-mono text-lg text-sage-600">{price}</span>
          </div>
          <p className="text-sm text-content-secondary">
            {interval === 'annual' ? 'Billed annually' : 'Billed monthly'}.
            Cancel anytime.
          </p>
        </div>

        {error && (
          <div className="bg-clay-50 border border-clay-200 text-clay-700 rounded-lg p-3 mb-4 text-sm" role="alert">
            {error}
          </div>
        )}

        <button
          onClick={handleCheckout}
          disabled={isLoading}
          className="w-full py-3 bg-sage-600 text-white rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Redirecting to payment...' : 'Continue to Checkout'}
        </button>

        <p className="text-xs text-content-muted text-center mt-4">
          You will be redirected to our secure payment partner, Stripe.
        </p>
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
