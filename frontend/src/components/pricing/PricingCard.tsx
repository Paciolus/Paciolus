// Individual tier card for the pricing grid.
// Sprint 818: this is the live design (Sprint 703/708 typography, brass
// "Most Popular" badge). It had fallen behind the page's inline copy, which
// is why the page never used it; the page now renders this component.
'use client'

import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { type Tier, type BillingInterval, formatPrice } from '@/domain/pricing'
import { trackEvent } from '@/utils/telemetry'

const cardVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring' as const, stiffness: 180, damping: 22 },
  },
} as const

export default function PricingCard({
  tier,
  interval,
}: {
  tier: Tier
  interval: BillingInterval
}) {
  const priceStr = formatPrice(tier, interval)
  const hasDollar = priceStr.startsWith('$') && priceStr !== '$0'

  const isHighlighted = Boolean(tier.badge)
  return (
    <motion.div
      variants={cardVariants}
      className={`relative rounded-2xl p-6 flex flex-col border transition-all duration-200 bg-sage-500/15 border-sage-500/40 shadow-lg shadow-sage-500/10 hover:shadow-xl hover:shadow-sage-500/15 hover:-translate-y-1 ${isHighlighted ? 'md:-translate-y-2 shadow-xl shadow-brass-400/10 ring-1 ring-brass-400/25' : ''}`}
    >
      {/* Sprint 708 — brass "Most Popular" foil badge.
          Rendered only when tier.badge is set; no tier
          currently sets one (Sprint 842 removed "Most Popular"), and the brass token is
          scarcity-scoped per tailwind.config. */}
      {tier.badge && (
        <span
          className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full font-sans text-[10px] font-semibold uppercase tracking-[0.18em] text-brass-400 bg-obsidian-800 border border-brass-400/50 shadow-md shadow-obsidian-900/60"
          style={{
            fontVariantNumeric: 'oldstyle-nums proportional-nums',
            backgroundImage: 'linear-gradient(180deg, rgba(176,141,87,0.08) 0%, rgba(176,141,87,0) 60%)',
          }}
        >
          {tier.badge}
        </span>
      )}

      {/* Tier Name — Sprint 703 display serif */}
      <h3 className="font-serif text-2xl text-oatmeal-100 mb-3">{tier.name}</h3>

      {/* Price */}
      <div className="mb-5">
        <AnimatePresence mode="wait">
          <motion.div
            key={`${tier.name}-${interval}`}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2, ease: 'easeOut' as const }}
          >
            {/* Sprint 703 / 708 — price in font-mono with oldstyle figures. */}
            <span
              className={`text-oatmeal-100 ${hasDollar ? 'type-num-xl' : 'font-serif text-2xl'}`}
              style={hasDollar ? { fontVariantNumeric: 'oldstyle-nums proportional-nums' } : undefined}
            >
              {priceStr}
            </span>
            {interval === 'annual' && hasDollar && (
              <span className="block type-num-xs text-oatmeal-500 mt-0.5 line-through">
                ${(tier.monthlyPrice * 12).toLocaleString()}/yr
              </span>
            )}
          </motion.div>
        </AnimatePresence>
        <p className="font-sans text-xs text-oatmeal-500 mt-1">
          {tier.priceSubtitle(interval)}
        </p>
      </div>

      {/* Features */}
      <ul className="space-y-2.5 mb-6 flex-1">
        {tier.features.map((feature) => (
          <li key={feature.text} className="flex items-start gap-2.5">
            <svg className="w-4 h-4 text-sage-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="font-sans text-sm text-oatmeal-300">{feature.text}</span>
          </li>
        ))}
      </ul>

      {/* CTA */}
      <Link
        href={tier.ctaHref(interval)}
        onClick={() => trackEvent('click_plan_cta', { plan: tier.name, interval: interval })}
        className={`block text-center py-2.5 rounded-xl font-sans font-medium text-sm transition-colors ${
          tier.ctaFilled
            ? 'bg-sage-500 text-oatmeal-50 hover:bg-sage-600'
            : 'bg-transparent border border-sage-500/40 text-sage-300 hover:bg-sage-500/10'
        }`}
      >
        {tier.cta}
      </Link>
    </motion.div>
  )
}
