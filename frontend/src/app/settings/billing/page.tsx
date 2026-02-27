'use client'

/**
 * Billing Settings Page — Sprint 373.
 *
 * Subscription management: current plan, usage meters, upgrade/cancel actions,
 * Stripe portal link for payment method management.
 */

import { useEffect, useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { ProfileDropdown } from '@/components/auth/ProfileDropdown'
import { CancelModal } from '@/components/billing/CancelModal'
import { PlanCard } from '@/components/billing/PlanCard'
import { UpgradeModal } from '@/components/billing/UpgradeModal'
import { UsageMeter } from '@/components/shared/UsageMeter'
import { useBilling } from '@/hooks/useBilling'

export default function BillingSettingsPage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth()
  const {
    subscription,
    usage,
    isLoading,
    error,
    fetchSubscription,
    fetchUsage,
    cancelSubscription,
    reactivateSubscription,
    getPortalUrl,
    addSeats,
    removeSeats,
  } = useBilling()
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [showCancelModal, setShowCancelModal] = useState(false)
  const [portalLoading, setPortalLoading] = useState(false)
  const [reactivateLoading, setReactivateLoading] = useState(false)
  const [seatLoading, setSeatLoading] = useState(false)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) {
      fetchSubscription()
      fetchUsage()
    }
  }, [isAuthenticated, fetchSubscription, fetchUsage])

  const tier = subscription?.tier ?? user?.tier ?? 'free'
  const status = subscription?.status ?? (tier === 'free' ? 'active' : 'canceled')
  const isFree = tier === 'free'
  const isTrialing = status === 'trialing'
  const isPaid = !isFree && (status === 'active' || status === 'trialing')

  async function handlePortalClick() {
    setPortalLoading(true)
    const url = await getPortalUrl()
    if (url) {
      window.location.href = url
    }
    setPortalLoading(false)
  }

  async function handleReactivate() {
    setReactivateLoading(true)
    await reactivateSubscription()
    await fetchSubscription()
    setReactivateLoading(false)
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-surface-page flex flex-col items-center justify-center gap-4">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
        <span className="text-content-secondary font-sans text-sm">Loading billing...</span>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-surface-page">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-surface-card backdrop-blur-md border-b border-theme z-50">
        <div className="max-w-6xl mx-auto px-6 py-3 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3">
            <Image
              src="/PaciolusLogo_DarkBG.png"
              alt="Paciolus"
              width={370}
              height={510}
              className="h-10 w-auto max-h-10 object-contain"
              style={{ imageRendering: 'crisp-edges' }}
            />
            <span className="text-xl font-bold font-serif text-content-primary tracking-tight">
              Paciolus
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-content-secondary font-sans hidden sm:block">
              Billing
            </span>
            {user && <ProfileDropdown user={user} onLogout={logout} />}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-24 pb-16 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Breadcrumb + Header */}
          <div className="mb-8">
            <div className="flex items-center gap-2 text-content-tertiary text-sm font-sans mb-4">
              <Link href="/" className="hover:text-content-secondary transition-colors">Home</Link>
              <span>/</span>
              <Link href="/settings" className="hover:text-content-secondary transition-colors">Settings</Link>
              <span>/</span>
              <span className="text-content-secondary">Billing</span>
            </div>
            <h1 className="text-3xl font-serif font-bold text-content-primary mb-2">
              Billing & Subscription
            </h1>
            <p className="text-content-secondary font-sans">
              Manage your plan, view usage, and update payment details.
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="bg-clay-50 border border-clay-200 text-clay-700 rounded-lg p-3 mb-6 text-sm font-sans" role="alert">
              {error}
            </div>
          )}

          {/* Current Plan */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
              Current Plan
            </h2>
            {isLoading ? (
              <div className="bg-surface-card border border-theme rounded-lg p-6">
                <div className="animate-pulse space-y-3">
                  <div className="h-6 bg-oatmeal-200 rounded-sm w-1/3" />
                  <div className="h-4 bg-oatmeal-200 rounded-sm w-1/2" />
                </div>
              </div>
            ) : (
              <PlanCard
                tier={tier}
                status={status}
                interval={subscription?.billing_interval ?? null}
                periodEnd={subscription?.current_period_end ?? null}
                cancelAtPeriodEnd={subscription?.cancel_at_period_end ?? false}
              />
            )}

            {/* Plan Actions */}
            <div className="flex flex-wrap gap-3 mt-4">
              {isFree && (
                <button
                  onClick={() => setShowUpgradeModal(true)}
                  className="px-5 py-2.5 bg-sage-600 text-white rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors"
                >
                  Start Free Trial
                </button>
              )}
              {isPaid && !subscription?.cancel_at_period_end && (
                <>
                  {!isTrialing && (
                    <button
                      onClick={() => setShowUpgradeModal(true)}
                      className="px-5 py-2.5 bg-sage-600 text-white rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors"
                    >
                      Change Plan
                    </button>
                  )}
                  <button
                    onClick={() => setShowCancelModal(true)}
                    className="px-5 py-2.5 border border-theme rounded-lg font-sans font-medium text-content-secondary hover:bg-surface-input transition-colors"
                  >
                    {isTrialing ? 'Cancel Trial' : 'Cancel Subscription'}
                  </button>
                </>
              )}
              {isPaid && subscription?.cancel_at_period_end && (
                <button
                  onClick={handleReactivate}
                  disabled={reactivateLoading}
                  className="px-5 py-2.5 bg-sage-600 text-white rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {reactivateLoading ? 'Reactivating...' : 'Reactivate Subscription'}
                </button>
              )}
            </div>
          </motion.div>

          {/* Usage */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="theme-card p-6 mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
              Usage
            </h2>
            {isLoading ? (
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-oatmeal-200 rounded-sm w-full" />
                <div className="h-4 bg-oatmeal-200 rounded-sm w-full" />
              </div>
            ) : usage ? (
              <div className="space-y-5">
                <UsageMeter
                  label="Diagnostics this month"
                  used={usage.diagnostics_used}
                  limit={usage.diagnostics_limit}
                />
                <UsageMeter
                  label="Clients"
                  used={usage.clients_used}
                  limit={usage.clients_limit}
                />
              </div>
            ) : (
              <p className="text-sm text-content-muted font-sans">Usage data unavailable.</p>
            )}
          </motion.div>

          {/* Seat Management — only for multi-seat plans */}
          {isPaid && subscription && subscription.total_seats > 1 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="theme-card p-6 mb-6"
            >
              <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
                Seats
              </h2>
              <div className="flex items-baseline gap-2 mb-1">
                <span className="text-2xl font-mono font-semibold text-content-primary">
                  {subscription.total_seats}
                </span>
                <span className="text-sm text-content-secondary font-sans">
                  total seats
                </span>
              </div>
              <p className="text-sm text-content-tertiary font-sans mb-4">
                {subscription.seat_count} included &middot; {subscription.additional_seats} additional
              </p>
              {!subscription.cancel_at_period_end && (
                <div className="flex gap-3">
                  <button
                    onClick={async () => {
                      setSeatLoading(true)
                      await addSeats(1)
                      await fetchSubscription()
                      setSeatLoading(false)
                    }}
                    disabled={seatLoading}
                    className="px-4 py-2 bg-sage-600 text-white rounded-lg font-sans text-sm font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {seatLoading ? 'Updating...' : 'Add Seat'}
                  </button>
                  {subscription.additional_seats > 0 && (
                    <button
                      onClick={async () => {
                        setSeatLoading(true)
                        await removeSeats(1)
                        await fetchSubscription()
                        setSeatLoading(false)
                      }}
                      disabled={seatLoading}
                      className="px-4 py-2 border border-theme rounded-lg font-sans text-sm font-medium text-content-secondary hover:bg-surface-input transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Remove Seat
                    </button>
                  )}
                </div>
              )}
            </motion.div>
          )}

          {/* Payment Method */}
          {isPaid && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="theme-card p-6"
            >
              <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
                Payment Method
              </h2>
              <p className="text-content-secondary font-sans text-sm mb-4">
                Manage your payment method, view invoices, and update billing information through our secure payment partner.
              </p>
              <button
                onClick={handlePortalClick}
                disabled={portalLoading}
                className="px-5 py-2.5 bg-sage-600 text-white rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {portalLoading ? 'Opening...' : 'Manage Payment Details'}
              </button>
            </motion.div>
          )}
        </div>
      </div>

      {/* Modals */}
      <UpgradeModal
        currentTier={tier}
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
      />
      <CancelModal
        isOpen={showCancelModal}
        periodEnd={subscription?.current_period_end ?? null}
        status={subscription?.status}
        onConfirm={async () => {
          const ok = await cancelSubscription()
          if (ok) await fetchSubscription()
          return ok
        }}
        onClose={() => setShowCancelModal(false)}
      />
    </main>
  )
}
