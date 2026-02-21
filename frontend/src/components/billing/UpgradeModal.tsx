'use client'

/**
 * UpgradeModal — Sprint 373.
 *
 * Tier selection modal with monthly/annual toggle.
 */

import { useState } from 'react'
import Link from 'next/link'

interface UpgradeModalProps {
  currentTier: string
  isOpen: boolean
  onClose: () => void
}

const TIERS = [
  {
    id: 'starter',
    name: 'Starter',
    monthly: '$49/mo',
    annual: '$499/yr',
    features: ['50 diagnostics/mo', '10 clients', '6 core tools'],
  },
  {
    id: 'professional',
    name: 'Professional',
    monthly: '$129/mo',
    annual: '$1,309/yr',
    features: ['Unlimited diagnostics', 'Unlimited clients', 'All 12+ tools'],
  },
  {
    id: 'team',
    name: 'Team',
    monthly: '$399/mo',
    annual: '$3,999/yr',
    features: ['Everything in Professional', '3 seats included', 'Team workspace'],
  },
]

export function UpgradeModal({ currentTier, isOpen, onClose }: UpgradeModalProps) {
  const [interval, setInterval] = useState<'monthly' | 'annual'>('monthly')

  if (!isOpen) return null

  const tierOrder = ['free', 'starter', 'professional', 'team', 'enterprise']
  const currentIndex = tierOrder.indexOf(currentTier)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-obsidian-900/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-surface-card border border-theme rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
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
                        href={`/checkout?plan=${tier.id}&interval=${interval}`}
                        className="inline-block px-4 py-2 bg-sage-600 text-white rounded-lg text-sm font-sans font-medium hover:bg-sage-700 transition-colors"
                        onClick={onClose}
                      >
                        Upgrade
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        <div className="mt-6 text-center">
          <Link href="/pricing" className="text-sm text-sage-600 hover:underline font-sans" onClick={onClose}>
            Compare all plans in detail
          </Link>
        </div>
      </div>
    </div>
  )
}
