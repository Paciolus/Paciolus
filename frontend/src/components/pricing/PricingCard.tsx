// Individual tier card component for the pricing grid.
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

  return (
    <motion.div
      variants={cardVariants}
      className="relative rounded-2xl p-6 flex flex-col border transition-all duration-200 bg-sage-500/15 border-sage-500/40 shadow-lg shadow-sage-500/10 hover:shadow-xl hover:shadow-sage-500/15 hover:-translate-y-1"
    >
      {/* Tier Name */}
      <h3 className="font-serif text-lg text-oatmeal-200 mb-3">{tier.name}</h3>

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
            <span className={`text-oatmeal-100 ${hasDollar ? 'type-num-xl' : 'font-serif text-2xl'}`}>
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
        onClick={() => trackEvent('click_plan_cta', { plan: tier.name, interval })}
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
