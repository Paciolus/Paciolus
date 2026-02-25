'use client'

/**
 * UpgradeModal — Sprint 373 + Phase LIX Sprint E.
 *
 * Tier selection modal with monthly/annual toggle.
 * Sprint E: seat selector for Team/Organization tiers.
 */

import { useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { MODAL_OVERLAY_VARIANTS, MODAL_CONTENT_VARIANTS } from '@/utils/themeUtils'

interface UpgradeModalProps {
  currentTier: string
  isOpen: boolean
  onClose: () => void
}

const TIERS = [
  {
    id: 'solo',
    name: 'Solo',
    monthly: '$50/mo',
    annual: '$500/yr',
    features: ['50 diagnostics/mo', '10 clients', '6 core tools', '7-day free trial'],
    hasSeats: false,
  },
  {
    id: 'team',
    name: 'Team',
    monthly: '$130/mo',
    annual: '$1,300/yr',
    features: ['Unlimited diagnostics', 'Unlimited clients', 'All 12+ tools', '3 seats included', '7-day free trial'],
    hasSeats: true,
  },
  {
    id: 'enterprise',
    name: 'Organization',
    monthly: '$400/mo',
    annual: '$4,000/yr',
    features: ['Everything in Team', '3 seats included', 'Priority support', '7-day free trial'],
    hasSeats: true,
  },
]

/** Per-seat pricing tiers, matching SEAT_PRICE_TIERS in price_config.py. */
const SEAT_PRICE_INFO = {
  monthly: { tier1: '$80/seat/mo', tier2: '$70/seat/mo' },
  annual: { tier1: '$800/seat/yr', tier2: '$700/seat/yr' },
} as const

/** Maximum additional seats available via self-serve checkout. */
const MAX_ADDITIONAL_SEATS = 22

export function UpgradeModal({ currentTier, isOpen, onClose }: UpgradeModalProps) {
  const [interval, setInterval] = useState<'monthly' | 'annual'>('monthly')
  const [additionalSeats, setAdditionalSeats] = useState(0)

  const tierOrder = ['free', 'solo', 'team', 'enterprise']
  const currentIndex = tierOrder.indexOf(currentTier)
  const isTrialEligible = currentTier === 'free'

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          <motion.div
            variants={MODAL_OVERLAY_VARIANTS}
            initial="hidden"
            animate="visible"
            exit="hidden"
            className="absolute inset-0 bg-obsidian-900/50 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            variants={MODAL_CONTENT_VARIANTS}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="relative bg-surface-card border border-theme rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          >
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-serif text-xl text-content-primary">Choose a Plan</h2>
          <button
            onClick={onClose}
            className="text-content-muted hover:text-content-secondary transition-colors"
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
                ? 'bg-sage-600 text-white'
                : 'bg-surface-input text-content-secondary hover:text-content-primary'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setInterval('annual')}
            className={`px-4 py-2 rounded-lg text-sm font-sans font-medium transition-colors ${
              interval === 'annual'
                ? 'bg-sage-600 text-white'
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
                      {interval === 'annual' ? tier.annual : tier.monthly}
                    </p>
                    <ul className="mt-3 space-y-1">
                      {tier.features.map((f) => (
                        <li key={f} className="text-sm text-content-secondary font-sans flex items-center gap-2">
                          <svg className="w-4 h-4 text-sage-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          {f}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="shrink-0 ml-4">
                    {isCurrent ? (
                      <span className="text-sm text-content-muted font-sans">Active</span>
                    ) : isDowngrade ? (
                      <span className="text-sm text-content-muted font-sans">—</span>
                    ) : (
                      <Link
                        href={`/checkout?plan=${tier.id}&interval=${interval}${tier.hasSeats && additionalSeats > 0 ? `&seats=${additionalSeats}` : ''}`}
                        className="inline-block px-4 py-2 bg-sage-600 text-white rounded-lg text-sm font-sans font-medium hover:bg-sage-700 transition-colors"
                        onClick={onClose}
                      >
                        {isTrialEligible ? 'Start Free Trial' : 'Upgrade'}
                      </Link>
                    )}
                  </div>
                </div>
                {/* Seat selector for multi-seat tiers */}
                {tier.hasSeats && !isCurrent && !isDowngrade && (
                  <div className="mt-3 pt-3 border-t border-theme">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-content-secondary font-sans">
                        Additional seats
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setAdditionalSeats(Math.max(0, additionalSeats - 1))}
                          disabled={additionalSeats === 0}
                          className="w-7 h-7 rounded border border-theme text-content-secondary hover:bg-surface-input transition-colors disabled:opacity-30 disabled:cursor-not-allowed text-sm font-sans"
                          aria-label="Remove seat"
                        >
                          &minus;
                        </button>
                        <span className="w-6 text-center font-mono text-sm text-content-primary">
                          {additionalSeats}
                        </span>
                        <button
                          onClick={() => setAdditionalSeats(Math.min(MAX_ADDITIONAL_SEATS, additionalSeats + 1))}
                          disabled={additionalSeats >= MAX_ADDITIONAL_SEATS}
                          className="w-7 h-7 rounded border border-theme text-content-secondary hover:bg-surface-input transition-colors disabled:opacity-30 disabled:cursor-not-allowed text-sm font-sans"
                          aria-label="Add seat"
                        >
                          +
                        </button>
                      </div>
                    </div>
                    {additionalSeats > 0 && (
                      <p className="text-xs text-content-tertiary font-sans mt-1">
                        {3 + additionalSeats} total seats (3 included + {additionalSeats} additional)
                      </p>
                    )}
                    <p className="text-xs text-content-muted font-sans mt-1">
                      Seats 4–10: {SEAT_PRICE_INFO[interval].tier1} · Seats 11–25: {SEAT_PRICE_INFO[interval].tier2}
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
