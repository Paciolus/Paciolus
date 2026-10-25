'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import PricingCard from '@/components/pricing/PricingCard'
import PricingComparison from '@/components/pricing/PricingComparison'
import PricingEstimator from '@/components/pricing/PricingEstimator'
import { type BillingInterval, faqItems, getPromoCopy, tiers } from '@/domain/pricing'
import { trackEvent } from '@/utils/telemetry'

// Sprint 818: tiers, seat pricing, the estimator, the FAQ and the promo copy
// all come from `@/domain/pricing`. This page used to redefine every one of
// them, and the copies had already drifted (the featured-plan badge existed
// only here), so tests of the domain module were testing code that never
// rendered.

/* ────────────────────────────────────────────────
   Billing toggle component
   ──────────────────────────────────────────────── */

function BillingToggle({
  interval,
  onChange,
}: {
  interval: BillingInterval
  onChange: (v: BillingInterval) => void
}) {
  return (
    <div className="flex items-center justify-center gap-3">
      <div className="inline-flex rounded-full border border-obsidian-500/30 bg-obsidian-800/60 p-1" role="radiogroup" aria-label="Billing interval">
        <button
          type="button"
          role="radio"
          aria-checked={interval === 'monthly'}
          onClick={() => onChange('monthly')}
          className={`relative px-5 py-2 rounded-full font-sans text-sm font-medium transition-colors ${
            interval === 'monthly'
              ? 'bg-sage-500 text-oatmeal-50'
              : 'text-oatmeal-400 hover:text-oatmeal-200'
          }`}
        >
          Monthly
        </button>
        <button
          type="button"
          role="radio"
          aria-checked={interval === 'annual'}
          onClick={() => onChange('annual')}
          className={`relative px-5 py-2 rounded-full font-sans text-sm font-medium transition-colors ${
            interval === 'annual'
              ? 'bg-sage-500 text-oatmeal-50'
              : 'text-oatmeal-400 hover:text-oatmeal-200'
          }`}
        >
          Annual
        </button>
      </div>
      {interval === 'annual' && (
        <motion.span
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.2, ease: 'easeOut' as const }}
          className="inline-flex items-center px-2.5 py-1 rounded-full bg-sage-500/20 border border-sage-500/40 text-sage-300 text-xs font-sans font-semibold"
        >
          Save ~16.7%
        </motion.span>
      )}
    </div>
  )
}

/* ────────────────────────────────────────────────
   Animation variants
   ──────────────────────────────────────────────── */

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
} as const

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: 'easeOut' as const },
  },
} as const

/* ────────────────────────────────────────────────
   Page component
   ──────────────────────────────────────────────── */

export default function PricingPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(null)
  const [billingInterval, setBillingInterval] = useState<BillingInterval>('monthly')

  useEffect(() => {
    trackEvent('view_pricing_page')
  }, [])

  function toggleFaq(index: number) {
    setOpenFaq((prev) => (prev === index ? null : index))
  }

  const promo = getPromoCopy(billingInterval)

  return (
    <main id="main-content" className="relative z-10 min-h-screen bg-gradient-obsidian">
      {/* -- Hero Section ----------------------- */}
      <section className="pt-32 pb-16 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' as const }}
          >
            <h1 className="type-display text-oatmeal-100 mb-4">
              Straightforward Pricing for Serious Work
            </h1>
            <p className="type-body text-oatmeal-400 max-w-xl mx-auto mb-3">
              Eighteen tools. Uploads not kept. One platform. Pick the plan that matches your practice.
            </p>
            <p className="font-sans text-sm text-sage-400">
              Every paid plan starts with a 7-day free trial. A card is required; you are not charged until the trial ends.
            </p>
          </motion.div>
        </div>
      </section>

      {/* -- Promo Banner ---------------------- */}
      <section className="pb-8 px-6">
        <div className="max-w-3xl mx-auto">
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, ease: 'easeOut' as const, delay: 0.3 }}
            className="rounded-xl border border-oatmeal-400/30 bg-oatmeal-200/8 px-6 py-4 text-center"
          >
            <p className="font-sans text-sm text-oatmeal-300">
              <span className="font-semibold text-oatmeal-100">{promo.prefix}</span> {promo.body}
            </p>
          </motion.div>
        </div>
      </section>

      {/* -- Billing Toggle -------------------- */}
      <section className="pb-12 px-6">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          animate="visible"
        >
          <BillingToggle interval={billingInterval} onChange={(v) => {
            setBillingInterval(v)
            trackEvent('toggle_billing_interval', { interval: v })
          }} />
        </motion.div>
      </section>

      {/* -- Pricing Cards --------------------- */}
      <section className="pb-12 px-6">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-5 items-stretch"
        >
          {tiers.map((tier) => (
            <PricingCard key={tier.name} tier={tier} interval={billingInterval} />
          ))}
        </motion.div>
      </section>

      {/* Sage divider */}
      <div className="max-w-xs mx-auto px-6 pb-12">
        <div className="h-px bg-gradient-to-r from-transparent via-sage-500/40 to-transparent" />
      </div>

      {/* -- Feature Comparison Table (shared <PricingComparison />, Sprint 650) -- */}
      <section className="pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <PricingComparison />
        </div>
      </section>

      {/* Oatmeal divider */}
      <div className="max-w-xs mx-auto px-6 pb-12">
        <div className="h-px bg-gradient-to-r from-transparent via-oatmeal-400/30 to-transparent" />
      </div>

      {/* -- Plan Your Cost (merged Estimator + Seat Calculator) -- */}
      <section className="relative pb-16 px-6 py-16 bg-oatmeal-200/4 overflow-hidden">
        {/* Background texture */}
        <div
          className="absolute inset-0 bg-cover bg-center opacity-[0.06] pointer-events-none"
          style={{ backgroundImage: "url('/backgrounds/background5.jpg')" }}
          aria-hidden="true"
        />
        <div className="max-w-6xl mx-auto relative z-10">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="visible"
          >
            <h2 className="type-headline-sm text-sage-300 text-center mb-3">
              Plan Your Cost
            </h2>
            <p className="font-sans text-sm text-oatmeal-400 text-center mb-10 max-w-lg mx-auto">
              Estimate your tier and calculate seat pricing — all in one place.
            </p>

            <PricingEstimator interval={billingInterval} />
          </motion.div>
        </div>
      </section>

      {/* Oatmeal divider */}
      <div className="max-w-xs mx-auto px-6 pb-12">
        <div className="h-px bg-gradient-to-r from-transparent via-oatmeal-400/30 to-transparent" />
      </div>

      {/* -- FAQ Section ----------------------- */}
      <section className="pb-24 px-6">
        <div className="max-w-3xl mx-auto">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="visible"
          >
            <h2 className="type-headline-sm text-oatmeal-200 text-center mb-10">
              Frequently Asked Questions
            </h2>

            <div className="space-y-3">
              {faqItems.map((item, idx) => {
                const isOpen = openFaq === idx
                return (
                  <div
                    key={idx}
                    className={`rounded-xl border transition-colors ${
                      isOpen
                        ? 'border-oatmeal-400/30 bg-oatmeal-200/5'
                        : 'border-obsidian-500/30 bg-obsidian-800/50'
                    }`}
                  >
                    <button
                      id={`faq-question-${idx}`}
                      onClick={() => toggleFaq(idx)}
                      className="w-full flex items-center justify-between py-4 px-6 text-left group"
                      aria-expanded={isOpen}
                      aria-controls={`faq-answer-${idx}`}
                    >
                      <span className="font-sans text-sm text-oatmeal-200 group-hover:text-oatmeal-100 transition-colors pr-4">
                        {item.question}
                      </span>
                      <svg
                        className={`w-5 h-5 text-oatmeal-500 shrink-0 transition-transform duration-200 ${
                          isOpen ? 'rotate-180' : ''
                        }`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        aria-hidden="true"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    {isOpen && (
                      <div id={`faq-answer-${idx}`} role="region" aria-labelledby={`faq-question-${idx}`} className="px-6 pb-4">
                        <p className="type-body-sm text-oatmeal-400">
                          {item.answer}
                        </p>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </motion.div>
        </div>
      </section>

    </main>
  )
}
