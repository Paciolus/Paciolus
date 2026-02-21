'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { trackEvent } from '@/utils/telemetry'

/* ────────────────────────────────────────────────
   Estimator types & logic
   ──────────────────────────────────────────────── */

type Uploads = '1-5' | '6-20' | '21-50' | '50+'
type Tools = 'tb-only' | '3-5' | 'all-12'
type TeamSize = 'solo' | '2-5' | '6-20' | '20+'
type PersonaKey = 'solo' | 'mid-size' | 'enterprise'
type TierName = 'Free' | 'Starter' | 'Professional' | 'Team' | 'Enterprise'
type BillingInterval = 'monthly' | 'annual'

interface Persona {
  key: PersonaKey
  label: string
  description: string
  icon: 'calculator' | 'building' | 'users'
  defaults: { uploads: Uploads; tools: Tools; teamSize: TeamSize }
}

const personas: Persona[] = [
  {
    key: 'solo',
    label: 'Solo Practitioner',
    description: 'Independent CPA or consultant',
    icon: 'calculator',
    defaults: { uploads: '1-5', tools: 'tb-only', teamSize: 'solo' },
  },
  {
    key: 'mid-size',
    label: 'Mid-Size Firm',
    description: 'Growing practice, 2-20 staff',
    icon: 'building',
    defaults: { uploads: '21-50', tools: '3-5', teamSize: '2-5' },
  },
  {
    key: 'enterprise',
    label: 'Enterprise',
    description: 'Large firm or corporate department',
    icon: 'users',
    defaults: { uploads: '50+', tools: 'all-12', teamSize: '20+' },
  },
]

const uploadOptions: { value: Uploads; label: string }[] = [
  { value: '1-5', label: '1-5' },
  { value: '6-20', label: '6-20' },
  { value: '21-50', label: '21-50' },
  { value: '50+', label: '50+' },
]

const toolOptions: { value: Tools; label: string }[] = [
  { value: 'tb-only', label: 'TB Diagnostics only' },
  { value: '3-5', label: '3-5 tools' },
  { value: 'all-12', label: 'All 12 tools' },
]

const teamOptions: { value: TeamSize; label: string }[] = [
  { value: 'solo', label: 'Just me' },
  { value: '2-5', label: '2-5 people' },
  { value: '6-20', label: '6-20 people' },
  { value: '20+', label: '20+ people' },
]

function getRecommendedTier(uploads: Uploads, tools: Tools, teamSize: TeamSize): TierName {
  if (teamSize === '20+') return 'Enterprise'
  if (teamSize === '6-20') return 'Team'
  if (tools === 'all-12' && uploads === '50+') return 'Team'
  if (tools === 'all-12') return 'Professional'
  if (uploads === '50+') return 'Professional'
  if (uploads === '21-50') return 'Professional'
  if (tools === '3-5') return 'Starter'
  if (uploads === '6-20') return 'Starter'
  if (teamSize === '2-5') return 'Starter'
  return 'Free'
}

/* ────────────────────────────────────────────────
   Persona icon SVGs
   ──────────────────────────────────────────────── */

function PersonaIcon({ icon, className }: { icon: Persona['icon']; className?: string }) {
  const cls = className ?? 'w-5 h-5'
  switch (icon) {
    case 'calculator':
      return (
        <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 15.75V18m-7.5-6.75h.008v.008H8.25v-.008zm0 2.25h.008v.008H8.25v-.008zm0 2.25h.008v.008H8.25v-.008zm0 2.25h.008v.008H8.25v-.008zm2.25-4.5h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008v-.008zm2.25-4.5h.008v.008H12.75v-.008zm0 2.25h.008v.008H12.75v-.008zm2.25-6.75h.008v.008H15v-.008zm0 2.25h.008v.008H15v-.008zm-2.25 0h.008v.008H12.75v-.008zM6 6.75A.75.75 0 016.75 6h10.5a.75.75 0 01.75.75v10.5a.75.75 0 01-.75.75H6.75a.75.75 0 01-.75-.75V6.75z" />
        </svg>
      )
    case 'building':
      return (
        <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
        </svg>
      )
    case 'users':
      return (
        <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
        </svg>
      )
  }
}

/* ────────────────────────────────────────────────
   Segmented selector
   ──────────────────────────────────────────────── */

function SegmentedSelector<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string
  options: { value: T; label: string }[]
  value: T
  onChange: (v: T) => void
}) {
  return (
    <div>
      <p className="font-sans text-sm text-oatmeal-400 mb-2">{label}</p>
      <div className="flex rounded-xl border border-obsidian-500/30 overflow-hidden">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={`flex-1 py-2 px-3 text-xs font-sans transition-colors ${
              value === opt.value
                ? 'bg-sage-500/20 text-sage-300 border-sage-500/30'
                : 'bg-obsidian-800/50 text-oatmeal-500 hover:text-oatmeal-300'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  )
}

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
      <div className="inline-flex rounded-full border border-obsidian-500/30 bg-obsidian-800/60 p-1">
        <button
          type="button"
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
          Save ~17%
        </motion.span>
      )}
    </div>
  )
}

/* ────────────────────────────────────────────────
   Tier data
   ──────────────────────────────────────────────── */

interface TierFeature {
  text: string
}

interface Tier {
  name: TierName
  monthlyPrice: number | null
  annualPrice: number | null
  priceLabel: string | null
  priceSubtitle: (interval: BillingInterval) => string
  features: TierFeature[]
  cta: string
  ctaHref: (interval: BillingInterval) => string
  badge?: string
  ctaFilled: boolean
}

const tiers: Tier[] = [
  {
    name: 'Free',
    monthlyPrice: 0,
    annualPrice: 0,
    priceLabel: null,
    priceSubtitle: () => 'forever free',
    features: [
      { text: '5 uploads per month' },
      { text: 'TB Diagnostics (full suite)' },
      { text: 'PDF & Excel exports' },
      { text: 'Email support' },
    ],
    cta: 'Start Free',
    ctaHref: () => '/register',
    ctaFilled: false,
  },
  {
    name: 'Starter',
    monthlyPrice: 49,
    annualPrice: 499,
    priceLabel: null,
    priceSubtitle: (interval) => interval === 'annual' ? 'per year' : 'per month',
    features: [
      { text: '20 uploads per month' },
      { text: 'TB Diagnostics + 5 testing tools' },
      { text: 'Client metadata management' },
      { text: 'PDF & Excel exports' },
      { text: 'Priority email support' },
    ],
    cta: 'Get Started',
    ctaHref: (interval) => `/register?plan=starter&interval=${interval}`,
    ctaFilled: false,
  },
  {
    name: 'Professional',
    monthlyPrice: 129,
    annualPrice: 1309,
    priceLabel: null,
    priceSubtitle: (interval) => interval === 'annual' ? 'per year' : 'per month',
    features: [
      { text: 'Unlimited uploads' },
      { text: 'All 12 diagnostic tools' },
      { text: 'Diagnostic Workspace' },
      { text: 'Statistical Sampling (ISA 530)' },
      { text: 'Multi-Currency Conversion' },
      { text: 'Priority support' },
    ],
    cta: 'Go Professional',
    ctaHref: (interval) => `/register?plan=professional&interval=${interval}`,
    badge: 'Most Popular',
    ctaFilled: true,
  },
  {
    name: 'Team',
    monthlyPrice: 399,
    annualPrice: 3999,
    priceLabel: null,
    priceSubtitle: (interval) => interval === 'annual' ? 'per year, 3 seats included' : 'per month, 3 seats included',
    features: [
      { text: 'Everything in Professional' },
      { text: '3 seats included (add more)' },
      { text: 'Team collaboration' },
      { text: 'Engagement Completion Gate' },
      { text: 'Workpaper index & sign-off' },
      { text: 'Dedicated onboarding' },
    ],
    cta: 'Contact for Team',
    ctaHref: () => '/contact?inquiry=Team',
    ctaFilled: false,
  },
  {
    name: 'Enterprise',
    monthlyPrice: null,
    annualPrice: null,
    priceLabel: 'Custom',
    priceSubtitle: () => 'tailored to your firm',
    features: [
      { text: 'Everything in Team' },
      { text: 'Unlimited seats' },
      { text: 'SSO integration' },
      { text: 'Dedicated account manager' },
      { text: 'Custom SLA & terms' },
      { text: 'On-premise deployment option' },
    ],
    cta: 'Contact Sales',
    ctaHref: () => '/contact?inquiry=Enterprise',
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
  starter: CellValue
  professional: CellValue
  team: CellValue
  enterprise: CellValue
}

const comparisonRows: ComparisonRow[] = [
  { feature: 'Monthly uploads', free: '5', starter: '20', professional: 'Unlimited', team: 'Unlimited', enterprise: 'Unlimited' },
  { feature: 'TB Diagnostics', free: true, starter: true, professional: true, team: true, enterprise: true },
  { feature: 'Testing Tools', free: false, starter: '5 tools', professional: 'All 12', team: 'All 12', enterprise: 'All 12' },
  { feature: 'Diagnostic Workspace', free: false, starter: false, professional: true, team: true, enterprise: true },
  { feature: 'Statistical Sampling', free: false, starter: false, professional: true, team: true, enterprise: true },
  { feature: 'Multi-Currency', free: false, starter: false, professional: true, team: true, enterprise: true },
  { feature: 'Client Metadata', free: false, starter: true, professional: true, team: true, enterprise: true },
  { feature: 'Team Seats', free: '1', starter: '1', professional: '1', team: '3 (expandable)', enterprise: 'Unlimited' },
  { feature: 'Team Collaboration', free: false, starter: false, professional: false, team: true, enterprise: true },
  { feature: 'Engagement Gate', free: false, starter: false, professional: false, team: true, enterprise: true },
  { feature: 'SSO', free: false, starter: false, professional: false, team: false, enterprise: true },
  { feature: 'Support SLA', free: 'Email', starter: 'Priority email', professional: 'Priority', team: 'Dedicated', enterprise: 'Custom SLA' },
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
    question: 'What is the difference between monthly and annual billing?',
    answer: 'Annual billing saves you approximately 17% compared to paying month-to-month. Annual plans are billed as a single payment at the start of each billing year. Monthly plans are billed at the start of each calendar month.',
  },
  {
    question: 'What is the difference between Starter and Professional?',
    answer: 'Starter includes TB Diagnostics plus 5 testing tools, ideal for practitioners who need core audit support. Professional unlocks all 12 tools, the Diagnostic Workspace, Statistical Sampling, and Multi-Currency Conversion for firms running full diagnostic engagements.',
  },
  {
    question: 'How do Team seats work?',
    answer: 'The Team plan includes 3 seats by default. Each seat allows one team member to log in, upload data, and collaborate on engagements. Additional seats can be added at a per-seat rate. Contact us for volume pricing.',
  },
  {
    question: 'Can I downgrade my plan?',
    answer: 'Yes. You can downgrade at any time. When downgrading, your current plan remains active until the end of the billing period. After that, your account transitions to the lower tier. Existing exports and metadata remain accessible; upload limits adjust to the new tier.',
  },
  {
    question: 'What happens if I exceed the free tier limits?',
    answer: 'You will receive a notification. Your existing data and exports remain accessible. Upgrade anytime to continue uploading.',
  },
  {
    question: 'What payment methods do you accept?',
    answer: 'We accept all major credit cards. Annual plans and Team/Enterprise accounts can also be invoiced. Enterprise contracts support custom payment terms.',
  },
  {
    question: 'Is there a minimum contract length?',
    answer: 'No. Monthly plans are month-to-month with no lock-in. Annual plans commit to a 12-month billing cycle. Enterprise contracts are customized to your firm.',
  },
]

/* ────────────────────────────────────────────────
   Animation variants
   ──────────────────────────────────────────────── */

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
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
   Price display helper
   ──────────────────────────────────────────────── */

function formatPrice(tier: Tier, interval: BillingInterval): string {
  if (tier.priceLabel) return tier.priceLabel
  const amount = interval === 'annual' ? tier.annualPrice : tier.monthlyPrice
  if (amount === null) return 'Custom'
  if (amount === 0) return '$0'
  return `$${amount.toLocaleString()}`
}

/* ────────────────────────────────────────────────
   Page component
   ──────────────────────────────────────────────── */

export default function PricingPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(null)
  const [uploads, setUploads] = useState<Uploads>('1-5')
  const [tools, setTools] = useState<Tools>('tb-only')
  const [teamSize, setTeamSize] = useState<TeamSize>('solo')
  const [activePersona, setActivePersona] = useState<PersonaKey | null>(null)
  const [billingInterval, setBillingInterval] = useState<BillingInterval>('monthly')

  const recommendedTier = getRecommendedTier(uploads, tools, teamSize)

  useEffect(() => {
    trackEvent('view_pricing_page')
  }, [])

  function toggleFaq(index: number) {
    setOpenFaq((prev) => (prev === index ? null : index))
  }

  function selectPersona(persona: Persona) {
    setActivePersona(persona.key)
    setUploads(persona.defaults.uploads)
    setTools(persona.defaults.tools)
    setTeamSize(persona.defaults.teamSize)
  }

  function handleUploads(v: Uploads) {
    setUploads(v)
    setActivePersona(null)
  }

  function handleTools(v: Tools) {
    setTools(v)
    setActivePersona(null)
  }

  function handleTeamSize(v: TeamSize) {
    setTeamSize(v)
    setActivePersona(null)
  }

  return (
    <main className="min-h-screen bg-gradient-obsidian">
      {/* -- Hero Section ----------------------- */}
      <section className="pt-32 pb-16 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' as const }}
          >
            <h1 className="type-display text-oatmeal-100 mb-4">
              Simple, Transparent Pricing
            </h1>
            <p className="type-body text-oatmeal-400 max-w-xl mx-auto">
              Start free. Scale as your practice grows.
            </p>
          </motion.div>
        </div>
      </section>

      {/* -- Plan Estimator -------------------- */}
      <section className="pb-16 px-6">
        <div className="max-w-3xl mx-auto">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-40px' }}
          >
            <h2 className="type-headline-sm text-oatmeal-200 text-center mb-8">
              Find Your Plan
            </h2>

            {/* Persona toggles */}
            <div className="flex flex-wrap justify-center gap-3 mb-8">
              {personas.map((persona) => (
                <button
                  key={persona.key}
                  type="button"
                  onClick={() => selectPersona(persona)}
                  className={`flex items-center gap-2.5 px-5 py-2.5 rounded-xl border font-sans text-sm transition-colors ${
                    activePersona === persona.key
                      ? 'border-sage-500/50 bg-sage-500/15 text-sage-300'
                      : 'border-obsidian-500/30 bg-obsidian-800/50 text-oatmeal-400 hover:text-oatmeal-200 hover:border-obsidian-400/40'
                  }`}
                >
                  <PersonaIcon icon={persona.icon} className="w-5 h-5" />
                  <span>{persona.label}</span>
                </button>
              ))}
            </div>

            {/* Input selectors */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <SegmentedSelector
                label="Monthly Uploads"
                options={uploadOptions}
                value={uploads}
                onChange={handleUploads}
              />
              <SegmentedSelector
                label="Tools Needed"
                options={toolOptions}
                value={tools}
                onChange={handleTools}
              />
              <SegmentedSelector
                label="Team Size"
                options={teamOptions}
                value={teamSize}
                onChange={handleTeamSize}
              />
            </div>

            {/* Recommendation line */}
            <div className="mt-8 text-center">
              <AnimatePresence mode="wait">
                <motion.p
                  key={recommendedTier}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.2, ease: 'easeOut' as const }}
                  className="font-sans text-sm text-oatmeal-300"
                >
                  Based on your needs, we recommend{' '}
                  <span className="text-sage-400 font-semibold">{recommendedTier}</span>.
                </motion.p>
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
      </section>

      {/* -- Billing Toggle -------------------- */}
      <section className="pb-12 px-6">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-40px' }}
        >
          <BillingToggle interval={billingInterval} onChange={(v) => {
            setBillingInterval(v)
            trackEvent('toggle_billing_interval', { interval: v })
          }} />
        </motion.div>
      </section>

      {/* -- Pricing Cards --------------------- */}
      <section className="pb-20 px-6">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-60px' }}
          className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-5 items-stretch"
        >
          {tiers.map((tier) => {
            const isRecommended = tier.name === recommendedTier
            const badge = isRecommended
              ? 'Best Fit for You'
              : tier.badge && tier.name !== recommendedTier
                ? tier.badge
                : undefined
            const priceStr = formatPrice(tier, billingInterval)
            const hasDollar = priceStr.startsWith('$') && priceStr !== '$0'

            return (
              <motion.div
                key={tier.name}
                variants={cardVariants}
                className={`relative rounded-2xl p-6 flex flex-col border ${
                  isRecommended
                    ? 'bg-sage-500/15 border-sage-500/40 shadow-lg shadow-sage-500/10'
                    : 'bg-obsidian-800 border-obsidian-500/30'
                }`}
              >
                {/* Badge */}
                {badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="inline-block px-4 py-1 rounded-full bg-sage-500/25 border border-sage-500/50 text-sage-300 text-xs font-sans font-semibold tracking-wide whitespace-nowrap">
                      {badge}
                    </span>
                  </div>
                )}

                {/* Tier Name */}
                <h3 className="font-serif text-lg text-oatmeal-200 mb-3">{tier.name}</h3>

                {/* Price */}
                <div className="mb-5">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={`${tier.name}-${billingInterval}`}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -6 }}
                      transition={{ duration: 0.2, ease: 'easeOut' as const }}
                    >
                      <span className={`text-oatmeal-100 ${hasDollar ? 'font-mono text-3xl font-bold' : 'font-serif text-2xl'}`}>
                        {priceStr}
                      </span>
                      {billingInterval === 'annual' && hasDollar && tier.monthlyPrice !== null && (
                        <span className="block font-mono text-xs text-oatmeal-500 mt-0.5 line-through">
                          ${(tier.monthlyPrice * 12).toLocaleString()}/yr
                        </span>
                      )}
                    </motion.div>
                  </AnimatePresence>
                  <p className="font-sans text-xs text-oatmeal-500 mt-1">
                    {tier.priceSubtitle(billingInterval)}
                  </p>
                </div>

                {/* Features */}
                <ul className="space-y-2.5 mb-6 flex-1">
                  {tier.features.map((feature) => (
                    <li key={feature.text} className="flex items-start gap-2.5">
                      <svg className="w-4 h-4 text-sage-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="font-sans text-sm text-oatmeal-300">{feature.text}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA */}
                <Link
                  href={tier.ctaHref(billingInterval)}
                  onClick={() => trackEvent('click_plan_cta', { plan: tier.name, interval: billingInterval })}
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
          })}
        </motion.div>
      </section>

      {/* -- Feature Comparison Table ---------- */}
      <section className="pb-20 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-40px' }}
          >
            <h2 className="type-headline-sm text-oatmeal-200 text-center mb-10">
              Feature Comparison
            </h2>

            <div className="overflow-x-auto rounded-2xl border border-obsidian-500/30">
              <table className="w-full text-left min-w-[700px]">
                <thead>
                  <tr className="border-b border-obsidian-500/30">
                    <th className="font-serif text-sm text-oatmeal-400 py-4 px-5 w-[22%]">Feature</th>
                    <th className="font-serif text-xs text-oatmeal-400 py-4 px-3 text-center w-[15%]">Free</th>
                    <th className="font-serif text-xs text-oatmeal-400 py-4 px-3 text-center w-[15%]">Starter</th>
                    <th className="font-serif text-xs text-sage-400 py-4 px-3 text-center w-[16%]">Professional</th>
                    <th className="font-serif text-xs text-oatmeal-400 py-4 px-3 text-center w-[16%]">Team</th>
                    <th className="font-serif text-xs text-oatmeal-400 py-4 px-3 text-center w-[16%]">Enterprise</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonRows.map((row, idx) => (
                    <tr
                      key={row.feature}
                      className={`border-b border-obsidian-500/20 last:border-b-0 ${
                        idx % 2 === 0 ? 'bg-obsidian-800/60' : 'bg-obsidian-800/30'
                      }`}
                    >
                      <td className="font-sans text-sm text-oatmeal-300 py-3 px-5">{row.feature}</td>
                      <td className="py-3 px-3 text-center"><CellContent value={row.free} /></td>
                      <td className="py-3 px-3 text-center"><CellContent value={row.starter} /></td>
                      <td className="py-3 px-3 text-center"><CellContent value={row.professional} /></td>
                      <td className="py-3 px-3 text-center"><CellContent value={row.team} /></td>
                      <td className="py-3 px-3 text-center"><CellContent value={row.enterprise} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </div>
      </section>

      {/* -- FAQ Section ----------------------- */}
      <section className="pb-24 px-6">
        <div className="max-w-3xl mx-auto">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-40px' }}
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
                        ? 'border-sage-500/30 bg-obsidian-800/70'
                        : 'border-obsidian-500/30 bg-obsidian-800/50'
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
