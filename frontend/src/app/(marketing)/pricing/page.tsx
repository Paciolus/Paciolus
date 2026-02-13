'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'

/* ────────────────────────────────────────────────
   Tier data
   ──────────────────────────────────────────────── */

interface TierFeature {
  text: string
}

interface Tier {
  name: string
  price: string
  priceSubtitle: string
  features: TierFeature[]
  cta: string
  ctaHref: string
  highlighted: boolean
  badge?: string
  ctaFilled: boolean
}

const tiers: Tier[] = [
  {
    name: 'Free',
    price: '$0',
    priceSubtitle: 'forever free',
    features: [
      { text: '5 uploads per month' },
      { text: 'TB Diagnostics (full suite)' },
      { text: 'PDF & Excel exports' },
      { text: 'Email support' },
    ],
    cta: 'Start Free',
    ctaHref: '/register',
    highlighted: false,
    ctaFilled: false,
  },
  {
    name: 'Professional',
    price: 'Contact Sales',
    priceSubtitle: 'for growing firms',
    features: [
      { text: 'Unlimited uploads' },
      { text: 'All 11 diagnostic tools' },
      { text: 'Diagnostic Workspace' },
      { text: 'Client metadata management' },
      { text: 'Priority support' },
    ],
    cta: 'Contact Sales',
    ctaHref: '/contact?inquiry=Enterprise',
    highlighted: true,
    badge: 'Most Popular',
    ctaFilled: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    priceSubtitle: 'Tailored to your firm',
    features: [
      { text: 'Everything in Professional' },
      { text: 'Team collaboration' },
      { text: 'SSO integration' },
      { text: 'Dedicated account manager' },
      { text: 'Custom SLA' },
    ],
    cta: 'Contact Sales',
    ctaHref: '/contact?inquiry=Enterprise',
    highlighted: false,
    ctaFilled: false,
  },
]

/* ────────────────────────────────────────────────
   Feature comparison table data
   ──────────────────────────────────────────────── */

type CellValue = true | false | string

interface ComparisonRow {
  feature: string
  free: CellValue
  professional: CellValue
  enterprise: CellValue
}

const comparisonRows: ComparisonRow[] = [
  { feature: 'Monthly uploads', free: '5', professional: 'Unlimited', enterprise: 'Unlimited' },
  { feature: 'TB Diagnostics', free: true, professional: true, enterprise: true },
  { feature: 'Testing Tools (11)', free: false, professional: true, enterprise: true },
  { feature: 'Diagnostic Workspace', free: false, professional: true, enterprise: true },
  { feature: 'Client Metadata', free: false, professional: true, enterprise: true },
  { feature: 'Team Collaboration', free: false, professional: false, enterprise: true },
  { feature: 'SSO', free: false, professional: false, enterprise: true },
  { feature: 'Support SLA', free: 'Email', professional: 'Priority', enterprise: 'Dedicated' },
]

/* ────────────────────────────────────────────────
   FAQ data
   ──────────────────────────────────────────────── */

interface FaqItem {
  question: string
  answer: string
}

const faqItems: FaqItem[] = [
  {
    question: 'How do I upgrade from Free to Professional?',
    answer: 'Contact our sales team and we\u0027ll set up your account within 24 hours.',
  },
  {
    question: 'What payment methods do you accept?',
    answer: 'We accept all major credit cards and can arrange invoicing for Enterprise accounts.',
  },
  {
    question: 'Is there a minimum contract length?',
    answer: 'No. Professional plans are month-to-month. Enterprise contracts are customized.',
  },
  {
    question: 'What happens if I exceed the free tier limits?',
    answer: 'You\u0027ll receive a notification. Your existing data and exports remain accessible. Upgrade anytime to continue uploading.',
  },
]

/* ────────────────────────────────────────────────
   Animation variants
   ──────────────────────────────────────────────── */

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15 },
  },
}

const cardVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring' as const, stiffness: 180, damping: 22 },
  },
}

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: 'easeOut' as const },
  },
}

/* ────────────────────────────────────────────────
   Cell renderer for comparison table
   ──────────────────────────────────────────────── */

function CellContent({ value }: { value: CellValue }) {
  if (value === true) {
    return (
      <svg className="w-5 h-5 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-label="Included">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
      </svg>
    )
  }
  if (value === false) {
    return <span className="text-oatmeal-600 font-sans text-sm">&mdash;</span>
  }
  return <span className="font-sans text-sm text-oatmeal-300">{value}</span>
}

/* ────────────────────────────────────────────────
   Page component
   ──────────────────────────────────────────────── */

export default function PricingPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  function toggleFaq(index: number) {
    setOpenFaq((prev) => (prev === index ? null : index))
  }

  return (
    <main className="min-h-screen bg-gradient-obsidian">
      {/* ── Hero Section ──────────────────────── */}
      <section className="pt-32 pb-16 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' as const }}
          >
            <h1 className="font-serif text-4xl md:text-5xl text-oatmeal-100 mb-4 leading-tight">
              Simple, Transparent Pricing
            </h1>
            <p className="font-sans text-lg text-oatmeal-400 max-w-xl mx-auto leading-relaxed">
              Start free. Upgrade when you need more.
            </p>
          </motion.div>
        </div>
      </section>

      {/* ── Pricing Cards ─────────────────────── */}
      <section className="pb-20 px-6">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-60px' }}
          className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch"
        >
          {tiers.map((tier) => (
            <motion.div
              key={tier.name}
              variants={cardVariants}
              className={`relative rounded-2xl p-8 flex flex-col border ${
                tier.highlighted
                  ? 'bg-sage-500/10 border-sage-500/30'
                  : 'bg-obsidian-800 border-obsidian-600/30'
              }`}
            >
              {/* Badge */}
              {tier.badge && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="inline-block px-4 py-1 rounded-full bg-sage-500/20 border border-sage-500/40 text-sage-300 text-xs font-sans font-semibold tracking-wide">
                    {tier.badge}
                  </span>
                </div>
              )}

              {/* Tier Name */}
              <h3 className="font-serif text-xl text-oatmeal-200 mb-4">{tier.name}</h3>

              {/* Price */}
              <div className="mb-6">
                <span className={`font-serif text-3xl text-oatmeal-100 ${tier.price.startsWith('$') ? 'font-mono' : ''}`}>
                  {tier.price}
                </span>
                <p className="font-sans text-sm text-oatmeal-500 mt-1">{tier.priceSubtitle}</p>
              </div>

              {/* Features */}
              <ul className="space-y-3 mb-8 flex-1">
                {tier.features.map((feature) => (
                  <li key={feature.text} className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-sage-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="font-sans text-sm text-oatmeal-300 leading-relaxed">{feature.text}</span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <Link
                href={tier.ctaHref}
                className={`block text-center py-3 rounded-xl font-sans font-medium text-sm transition-colors ${
                  tier.ctaFilled
                    ? 'bg-sage-500 text-oatmeal-50 hover:bg-sage-600'
                    : 'bg-transparent border border-sage-500/40 text-sage-300 hover:bg-sage-500/10'
                }`}
              >
                {tier.cta}
              </Link>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── Feature Comparison Table ──────────── */}
      <section className="pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-40px' }}
          >
            <h2 className="font-serif text-2xl text-oatmeal-200 text-center mb-10">
              Feature Comparison
            </h2>

            <div className="overflow-x-auto rounded-2xl border border-obsidian-600/30">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-obsidian-600/30">
                    <th className="font-serif text-sm text-oatmeal-400 py-4 px-6 w-2/5">Feature</th>
                    <th className="font-serif text-sm text-oatmeal-400 py-4 px-4 text-center w-1/5">Free</th>
                    <th className="font-serif text-sm text-sage-400 py-4 px-4 text-center w-1/5">Professional</th>
                    <th className="font-serif text-sm text-oatmeal-400 py-4 px-4 text-center w-1/5">Enterprise</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonRows.map((row, idx) => (
                    <tr
                      key={row.feature}
                      className={`border-b border-obsidian-600/20 last:border-b-0 ${
                        idx % 2 === 0 ? 'bg-obsidian-800/60' : 'bg-obsidian-800/30'
                      }`}
                    >
                      <td className="font-sans text-sm text-oatmeal-300 py-3.5 px-6">{row.feature}</td>
                      <td className="py-3.5 px-4 text-center"><CellContent value={row.free} /></td>
                      <td className="py-3.5 px-4 text-center"><CellContent value={row.professional} /></td>
                      <td className="py-3.5 px-4 text-center"><CellContent value={row.enterprise} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── FAQ Section ───────────────────────── */}
      <section className="pb-24 px-6">
        <div className="max-w-3xl mx-auto">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-40px' }}
          >
            <h2 className="font-serif text-2xl text-oatmeal-200 text-center mb-10">
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
                        ? 'border-sage-500/30 bg-obsidian-800/70'
                        : 'border-obsidian-600/30 bg-obsidian-800/40'
                    }`}
                  >
                    <button
                      onClick={() => toggleFaq(idx)}
                      className="w-full flex items-center justify-between py-4 px-6 text-left group"
                      aria-expanded={isOpen}
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
                      <div className="px-6 pb-4">
                        <p className="font-sans text-sm text-oatmeal-400 leading-relaxed">
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
