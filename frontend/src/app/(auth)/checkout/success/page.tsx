'use client'

/**
 * Checkout success page — Sprint 370.
 *
 * Shown after successful Stripe payment. Refreshes user data.
 */

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'

export default function CheckoutSuccessPage() {
  const { refreshUser } = useAuth()
  const [refreshed, setRefreshed] = useState(false)

  useEffect(() => {
    async function refresh() {
      await refreshUser()
      setRefreshed(true)
    }
    refresh()
  }, [refreshUser])

  return (
    <div className="min-h-screen bg-surface-page flex items-center justify-center px-6">
      <div className="bg-surface-card border border-theme rounded-lg p-8 max-w-md text-center">
        <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-sage-100 flex items-center justify-center">
          <svg className="w-8 h-8 text-sage-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <h1 className="font-serif text-2xl text-content-primary mb-3">
          Welcome to Your New Plan
        </h1>
        <p className="text-content-secondary mb-6">
          {refreshed
            ? 'Your account has been upgraded. All new features are now available.'
            : 'Activating your subscription...'}
        </p>

        <Link
          href="/tools/trial-balance"
          className="inline-block px-6 py-3 bg-sage-600 text-white rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors"
        >
          Start Using Your Tools
        </Link>

        <div className="mt-4">
          <Link href="/settings/billing" className="text-sm text-sage-600 hover:underline">
            View billing details
          </Link>
        </div>
      </div>
    </div>
  )
}
