'use client'

/**
 * Checkout success page — Sprint 370.
 *
 * Shown after Stripe redirects back. The new plan arrives by Stripe webhook,
 * so this page does not assume it: it waits for the session to restore (the
 * in-memory access token is gone after the redirect) and polls
 * `/billing/subscription` until the subscription is trialing or active
 * (council 2026-11-25 D-2). Only then does it say the plan is active.
 */

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useBilling } from '@/hooks/useBilling'

/** Poll interval and attempt cap — about 30 seconds in all. */
const POLL_INTERVAL_MS = 2000
const MAX_POLL_ATTEMPTS = 15

const ACTIVE_STATUSES = new Set(['trialing', 'active'])

type Phase = 'checking' | 'confirmed' | 'pending' | 'signed-out'

export default function CheckoutSuccessPage() {
  const { token, isLoading: authLoading, refreshUser } = useAuthSession()
  const { fetchSubscription } = useBilling()
  const [phase, setPhase] = useState<Phase>('checking')
  const [attemptRound, setAttemptRound] = useState(0)
  const cancelled = useRef(false)

  useEffect(() => {
    cancelled.current = false
    if (authLoading) return
    if (!token) {
      setPhase('signed-out')
      return
    }
    setPhase('checking')

    let attempts = 0
    let timer: ReturnType<typeof setTimeout> | undefined
    const poll = async () => {
      attempts += 1
      const sub = await fetchSubscription()
      if (cancelled.current) return
      if (sub && sub.tier !== 'free' && ACTIVE_STATUSES.has(sub.status)) {
        await refreshUser()
        if (!cancelled.current) setPhase('confirmed')
        return
      }
      if (attempts >= MAX_POLL_ATTEMPTS) {
        setPhase('pending')
        return
      }
      timer = setTimeout(() => void poll(), POLL_INTERVAL_MS)
    }
    void poll()

    return () => {
      cancelled.current = true
      if (timer) clearTimeout(timer)
    }
  }, [authLoading, token, fetchSubscription, refreshUser, attemptRound])

  const heading =
    phase === 'confirmed' ? 'Welcome to Your New Plan' : phase === 'checking' ? 'Activating Your Subscription' : 'Payment Received'

  return (
    <div className="min-h-screen bg-surface-page flex items-center justify-center px-6">
      <div className="bg-surface-card border border-theme rounded-lg p-8 max-w-md text-center">
        {phase === 'confirmed' && (
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-sage-100 flex items-center justify-center">
            <svg className="w-8 h-8 text-sage-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        )}

        <h1 className="font-serif text-2xl text-content-primary mb-3">{heading}</h1>
        <p className="text-content-secondary mb-6" role="status" aria-live="polite" data-testid="checkout-status">
          {phase === 'checking' && 'Confirming your subscription with our payment provider…'}
          {phase === 'confirmed' && 'Your new plan is active. All of its features are now available.'}
          {phase === 'pending' &&
            'Stripe has not confirmed your subscription yet. This usually takes a minute — check again shortly.'}
          {phase === 'signed-out' && 'Sign in to see your subscription. Your payment is not affected.'}
        </p>

        {phase === 'confirmed' && (
          <Link
            href="/tools/trial-balance"
            className="inline-block px-6 py-3 bg-sage-600 text-oatmeal-50 rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors"
          >
            Start Using Your Tools
          </Link>
        )}
        {phase === 'pending' && (
          <button
            type="button"
            onClick={() => setAttemptRound(n => n + 1)}
            className="inline-block px-6 py-3 bg-sage-600 text-oatmeal-50 rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors"
          >
            Check Again
          </button>
        )}
        {phase === 'signed-out' && (
          <Link
            href="/login"
            onClick={() => sessionStorage.setItem('paciolus_redirect', '/checkout/success')}
            className="inline-block px-6 py-3 bg-sage-600 text-oatmeal-50 rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors"
          >
            Sign In
          </Link>
        )}

        <div className="mt-4">
          <Link href="/settings/billing" className="text-sm text-sage-400 hover:underline">
            View billing details
          </Link>
        </div>
      </div>
    </div>
  )
}
