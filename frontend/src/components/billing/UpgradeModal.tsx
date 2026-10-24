'use client'

/**
 * UpgradeModal
 *
 * Tier selection modal with monthly/annual toggle.
 * Includes seat selector for Team tier.
 */

import { useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { type BillingInterval, baseSeats, formatPrice, getTier, maxAdditionalSeats, seatPriceDollars } from '@/domain/pricing'
import { fadeScale } from '@/lib/motion'

interface UpgradeModalProps {
  currentTier: string
  isOpen: boolean
  onClose: () => void
}

// Sprint 818: prices, seat counts and seat rates come from `@/domain/pricing`;
// only these short feature blurbs are modal-specific copy.
const TIERS = [
  {
    id: 'solo',
    name: 'Solo',
    features: ['100 uploads/mo', 'Unlimited clients', 'All 18 tools', 'PDF, Excel & CSV exports', '7-day free trial'],
  },
  {
    id: 'professional',
    name: 'Professional',
    features: ['500 uploads/mo', 'Unlimited clients', 'All 18 tools', 'All exports', '7 seats (up to 20)', 'Export sharing', 'Admin dashboard', '7-day free trial'],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    features: ['Unlimited uploads', 'Unlimited clients', 'All 18 tools', 'All exports', '20 seats (up to 100)', 'Export sharing', 'Admin dashboard', 'Custom PDF branding', '7-day free trial'],
  },
]

function priceLabel(tierId: string, interval: BillingInterval): string {
  const tier = getTier(tierId)
  return tier ? `${formatPrice(tier, interval)}/${interval === 'annual' ? 'yr' : 'mo'}` : ''
}

export function UpgradeModal({ currentTier, isOpen, onClose }: UpgradeModalProps) {
  const [interval, setInterval] = useState<BillingInterval>('monthly')
  const [additionalSeats, setAdditionalSeats] = useState(0)

  const tierOrder = ['free', 'solo', 'professional', 'enterprise']
  const currentIndex = tierOrder.indexOf(currentTier)
  const isTrialEligible = currentTier === 'free'

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="absolute inset-0 bg-obsidian-900/50 backdrop-blur-xs"
            onClick={onClose}
          />
          <motion.div
            variants={fadeScale}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="relative bg-surface-card border border-theme rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          >
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-serif text-xl text-content-primary">Choose a Plan</h2>
          <button
            onClick={onClose}
            className="text-content-tertiary hover:text-content-secondary transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Billing Toggle */}
        <div className="flex items-center justify-center gap-3 mb-6">
          <button
            onClick={() => setInterval('monthly')}
            className={`px-4 py-2 rounded-lg text-sm font-sans font-medium transition-colors ${
              interval === 'monthly'
                ? 'bg-sage-600 text-oatmeal-50'
                : 'bg-surface-input text-content-secondary hover:text-content-primary'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setInterval('annual')}
            className={`px-4 py-2 rounded-lg text-sm font-sans font-medium transition-colors ${
              interval === 'annual'
                ? 'bg-sage-600 text-oatmeal-50'
                : 'bg-surface-input text-content-secondary hover:text-content-primary'
            }`}
          >
            Annual
            <span className="ml-1 text-xs opacity-75">Save ~17%</span>
          </button>
        </div>

        {/* Tier Cards */}
        <div className="space-y-4">
          {TIERS.map((tier) => {
            const tierIndex = tierOrder.indexOf(tier.id)
            const isCurrent = tier.id === currentTier
            const isDowngrade = tierIndex <= currentIndex

            return (
              <div
                key={tier.id}
                className={`border rounded-lg p-5 ${
                  isCurrent
                    ? 'border-sage-500 bg-sage-50/50'
                    : 'border-theme bg-surface-card'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-serif text-lg text-content-primary">{tier.name}</h3>
                      {isCurrent && (
                        <span className="text-xs font-sans font-medium px-2 py-0.5 rounded-full bg-sage-100 text-sage-700 border border-sage-200">
                          Current
                        </span>
                      )}
                    </div>
                    <p className="font-mono text-lg text-sage-600 mt-1">
                      {priceLabel(tier.id, interval)}
                    </p>
                    <ul className="mt-3 space-y-1">
                      {tier.features.map((f) => (
                        <li key={f} className="text-sm text-content-secondary font-sans flex items-center gap-2">
                          <svg className="w-4 h-4 text-theme-success-text shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          {f}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="shrink-0 ml-4">
                    {isCurrent ? (
                      <span className="text-sm text-content-tertiary font-sans">Active</span>
                    ) : isDowngrade ? (
                      <span className="text-sm text-content-tertiary font-sans">—</span>
                    ) : (
                      <Link
                        href={`/checkout?plan=${tier.id}&interval=${interval}${maxAdditionalSeats(tier.id) > 0 && additionalSeats > 0 ? `&seats=${additionalSeats}` : ''}`}
                        className="inline-block px-4 py-2 bg-sage-600 text-oatmeal-50 rounded-lg text-sm font-sans font-medium hover:bg-sage-700 transition-colors"
                        onClick={onClose}
                      >
                        {isTrialEligible ? 'Start Free Trial' : 'Upgrade'}
                      </Link>
                    )}
                  </div>
                </div>
                {/* Seat selector for multi-seat tiers */}
                {maxAdditionalSeats(tier.id) > 0 && !isCurrent && !isDowngrade && (
                  <div className="mt-3 pt-3 border-t border-theme">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-content-secondary font-sans">
                        Additional seats
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setAdditionalSeats(Math.max(0, additionalSeats - 1))}
                          disabled={additionalSeats === 0}
                          className="w-7 h-7 rounded-sm border border-theme text-content-secondary hover:bg-surface-input transition-colors disabled:opacity-30 disabled:cursor-not-allowed text-sm font-sans"
                          aria-label="Remove seat"
                        >
                          &minus;
                        </button>
                        <span className="w-6 text-center font-mono text-sm text-content-primary">
                          {additionalSeats}
                        </span>
                        <button
                          onClick={() => setAdditionalSeats(Math.min(maxAdditionalSeats(tier.id), additionalSeats + 1))}
                          disabled={additionalSeats >= maxAdditionalSeats(tier.id)}
                          className="w-7 h-7 rounded-sm border border-theme text-content-secondary hover:bg-surface-input transition-colors disabled:opacity-30 disabled:cursor-not-allowed text-sm font-sans"
                          aria-label="Add seat"
                        >
                          +
                        </button>
                      </div>
                    </div>
                    {additionalSeats > 0 && (
                      <p className="text-xs text-content-tertiary font-sans mt-1">
                        {baseSeats(tier.id) + additionalSeats} total seats ({baseSeats(tier.id)} included + {additionalSeats} additional)
                      </p>
                    )}
                    <p className="text-xs text-content-tertiary font-sans mt-1">
                      Additional seats: ${seatPriceDollars(tier.id, interval)}/seat/{interval === 'annual' ? 'yr' : 'mo'}
                    </p>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        <div className="mt-6 text-center">
          <Link href="/pricing" className="text-sm text-sage-600 hover:underline font-sans" onClick={onClose}>
            Compare all plans in detail
          </Link>
        </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
