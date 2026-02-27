'use client'

import { useState, useEffect, useCallback } from 'react'
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
type TierName = 'Solo' | 'Team' | 'Organization' | 'Enterprise'
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
    label: 'Large Firm',
    description: 'Multi-team department or regional firm',
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
  if (teamSize === '20+') return 'Organization'
  if (teamSize === '6-20') return 'Team'
  if (tools === 'all-12' && uploads === '50+') return 'Team'
  if (tools === 'all-12') return 'Team'
  if (uploads === '50+') return 'Team'
  if (uploads === '21-50') return 'Solo'
  if (tools === '3-5') return 'Solo'
  if (uploads === '6-20') return 'Solo'
  if (teamSize === '2-5') return 'Solo'
  return 'Solo'
}

/* ────────────────────────────────────────────────
   Seat pricing constants (mirror backend price_config.py)
   ──────────────────────────────────────────────── */

const SEAT_TIERS = [
  { min: 4, max: 10, monthly: 80, annual: 800 },
  { min: 11, max: 25, monthly: 70, annual: 700 },
] as const

const MAX_SELF_SERVE_SEATS = 25

function calculateSeatCost(additionalSeats: number, interval: BillingInterval): number | null {
  if (additionalSeats <= 0) return 0
  let total = 0
  for (let i = 0; i < additionalSeats; i++) {
    const seatNum = 4 + i
    if (seatNum > MAX_SELF_SERVE_SEATS) return null
    const tier = SEAT_TIERS.find(t => seatNum >= t.min && seatNum <= t.max)
    if (!tier) return null
    total += interval === 'annual' ? tier.annual : tier.monthly
  }
  return total
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
   Seat calculator widget
   ──────────────────────────────────────────────── */

function SeatCalculator({
  interval,
}: {
  interval: BillingInterval
}) {
  const [additionalSeats, setAdditionalSeats] = useState(0)

  const handleChange = useCallback((value: number) => {
    setAdditionalSeats(Math.max(0, Math.min(value, 25)))
  }, [])

  const totalSeats = 3 + additionalSeats
  const seatCost = calculateSeatCost(additionalSeats, interval)
  const exceedsLimit = seatCost === null

  return (
    <div className="rounded-xl border border-obsidian-500/30 bg-obsidian-800/60 p-5">
      <h3 className="font-serif text-sm text-oatmeal-200 mb-4">Seat Calculator</h3>
      <div className="flex items-center gap-4 mb-3">
        <label htmlFor="seat-slider" className="font-sans text-xs text-oatmeal-400 shrink-0">
          Additional seats
        </label>
        <input
          id="seat-slider"
          type="range"
          min={0}
          max={25}
          value={additionalSeats}
          onChange={(e) => handleChange(Number(e.target.value))}
          className="flex-1 h-1.5 rounded-full appearance-none bg-obsidian-600 accent-sage-500 cursor-pointer"
        />
        <span className="font-mono text-sm text-oatmeal-200 w-8 text-right tabular-nums">
          {additionalSeats}
        </span>
      </div>

      <div className="flex items-baseline justify-between">
        <span className="font-sans text-xs text-oatmeal-400">
          {totalSeats} total seat{totalSeats !== 1 ? 's' : ''} (3 included + {additionalSeats} add-on)
        </span>
        {exceedsLimit ? (
          <Link
            href="/contact?inquiry=seats"
            className="font-sans text-xs text-sage-400 hover:text-sage-300 underline underline-offset-2"
          >
            Contact sales for 26+ seats
          </Link>
        ) : (
          <span className="font-mono text-sm text-oatmeal-200 tabular-nums">
            {seatCost === 0
              ? 'Included'
              : `+$${seatCost.toLocaleString()}/${interval === 'annual' ? 'yr' : 'mo'}`}
          </span>
        )}
      </div>

      {/* Tier breakdown */}
      {additionalSeats > 0 && !exceedsLimit && (
        <div className="mt-3 pt-3 border-t border-obsidian-500/20 space-y-1">
          {SEAT_TIERS.map((tier) => {
            const seatsInTier = Math.max(0, Math.min(additionalSeats, tier.max - 3) - Math.max(0, tier.min - 4))
            if (seatsInTier <= 0) return null
            const rate = interval === 'annual' ? tier.annual : tier.monthly
            return (
              <div key={tier.min} className="flex justify-between font-sans text-xs text-oatmeal-500">
                <span>Seats {tier.min}–{tier.max}: {seatsInTier} × ${rate}/{interval === 'annual' ? 'yr' : 'mo'}</span>
                <span className="font-mono tabular-nums">${(seatsInTier * rate).toLocaleString()}</span>
              </div>
            )
          })}
        </div>
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
  internalId: string
  monthlyPrice: number
  annualPrice: number
  priceSubtitle: (interval: BillingInterval) => string
  features: TierFeature[]
  cta: string
  ctaHref: (interval: BillingInterval) => string
  badge?: string
  ctaFilled: boolean
  hasSeats: boolean
  isContactSales?: boolean
}

const tiers: Tier[] = [
  {
    name: 'Solo',
    internalId: 'solo',
    monthlyPrice: 50,
    annualPrice: 500,
    priceSubtitle: (interval) => interval === 'annual' ? 'per year' : 'per month',
    features: [
      { text: '20 uploads per month' },
      { text: 'TB Diagnostics + 5 testing tools' },
      { text: 'Client metadata management' },
      { text: 'PDF & Excel exports' },
      { text: 'Priority email support' },
      { text: '7-day free trial' },
    ],
    cta: 'Start Free Trial',
    ctaHref: (interval) => `/register?plan=solo&interval=${interval}`,
    ctaFilled: false,
    hasSeats: false,
  },
  {
    name: 'Team',
    internalId: 'team',
    monthlyPrice: 130,
    annualPrice: 1300,
    priceSubtitle: (interval) => interval === 'annual' ? 'per year, 3 seats included' : 'per month, 3 seats included',
    features: [
      { text: 'Unlimited uploads' },
      { text: 'All 12 diagnostic tools' },
      { text: 'Diagnostic Workspace' },
      { text: 'Statistical Sampling (ISA 530)' },
      { text: 'Multi-Currency Conversion' },
      { text: '3 seats included (add more)' },
      { text: '7-day free trial' },
    ],
    cta: 'Start Free Trial',
    ctaHref: (interval) => `/register?plan=team&interval=${interval}`,
    badge: 'Most Popular',
    ctaFilled: true,
    hasSeats: true,
  },
  {
    name: 'Organization',
    internalId: 'enterprise',
    monthlyPrice: 400,
    annualPrice: 4000,
    priceSubtitle: (interval) => interval === 'annual' ? 'per year, 3 seats included' : 'per month, 3 seats included',
    features: [
      { text: 'Everything in Team' },
      { text: '3 seats included (add more)' },
      { text: 'Engagement Completion Gate' },
      { text: 'Workpaper index & sign-off' },
      { text: 'Dedicated onboarding' },
      { text: 'SSO integration' },
      { text: '7-day free trial' },
    ],
    cta: 'Start Free Trial',
    ctaHref: (interval) => `/register?plan=enterprise&interval=${interval}`,
    ctaFilled: false,
    hasSeats: true,
  },
  {
    name: 'Enterprise',
    internalId: 'enterprise-contact',
    monthlyPrice: 0,
    annualPrice: 0,
    priceSubtitle: () => 'tailored to your firm',
    features: [
      { text: 'Everything in Organization' },
      { text: 'Unlimited seats' },
      { text: 'Dedicated account manager' },
      { text: 'Custom integrations' },
      { text: 'On-premise deployment option' },
      { text: 'Custom SLA & support' },
    ],
    cta: 'Contact Sales',
    ctaHref: () => '/contact?inquiry=enterprise',
    ctaFilled: false,
    hasSeats: false,
    isContactSales: true,
  },
]

/* ────────────────────────────────────────────────
   Feature comparison table data
   ──────────────────────────────────────────────── */

type CellValue = true | false | string

interface ComparisonRow {
  feature: string
  solo: CellValue
  team: CellValue
  organization: CellValue
  enterprise: CellValue
}

const comparisonRows: ComparisonRow[] = [
  { feature: 'Monthly uploads', solo: '20', team: 'Unlimited', organization: 'Unlimited', enterprise: 'Unlimited' },
  { feature: 'TB Diagnostics', solo: true, team: true, organization: true, enterprise: true },
  { feature: 'Testing Tools', solo: '5 tools', team: 'All 12', organization: 'All 12', enterprise: 'All 12' },
  { feature: 'Diagnostic Workspace', solo: false, team: true, organization: true, enterprise: true },
  { feature: 'Statistical Sampling', solo: false, team: true, organization: true, enterprise: true },
  { feature: 'Multi-Currency', solo: false, team: true, organization: true, enterprise: true },
  { feature: 'Client Metadata', solo: true, team: true, organization: true, enterprise: true },
  { feature: 'Team Seats', solo: '1', team: '3 (expandable)', organization: '3 (expandable)', enterprise: 'Unlimited' },
  { feature: 'Team Collaboration', solo: false, team: true, organization: true, enterprise: true },
  { feature: 'Engagement Gate', solo: false, team: true, organization: true, enterprise: true },
  { feature: 'SSO', solo: false, team: false, organization: true, enterprise: true },
  { feature: 'Dedicated Account Manager', solo: false, team: false, organization: false, enterprise: true },
  { feature: 'Support SLA', solo: 'Priority email', team: 'Dedicated', organization: 'Custom SLA', enterprise: 'Custom SLA' },
  { feature: 'Free Trial', solo: '7 days', team: '7 days', organization: '7 days', enterprise: false },
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
    question: 'How does the 7-day free trial work?',
    answer: 'Every plan includes a 7-day free trial. Start using the full feature set immediately with no charge. You can cancel anytime during the trial period and will not be billed. After 7 days, your selected plan begins billing automatically.',
  },
  {
    question: 'What promotions are available?',
    answer: 'Monthly plans can receive 20% off the first 3 months. Annual plans can receive an extra 10% off the first year. Only one promotional discount applies per subscription — whichever is best for you.',
  },
  {
    question: 'How do Team and Organization seats work?',
    answer: 'Both the Team and Organization plans include 3 seats. Each seat allows one team member to log in, upload data, and collaborate on engagements. Additional seats can be added: seats 4-10 are $80/month ($800/year), seats 11-25 are $70/month ($700/year). For 26+ seats, contact our sales team.',
  },
  {
    question: 'What is the difference between Solo and Team?',
    answer: 'Solo includes TB Diagnostics plus 5 testing tools, ideal for practitioners who need core audit support. Team unlocks all 12 tools, the Diagnostic Workspace, Statistical Sampling, Multi-Currency Conversion, and team collaboration with 3 included seats.',
  },
  {
    question: 'Why is Organization priced separately from Team?',
    answer: 'Organization adds enterprise-grade features that Team does not include: SSO integration, dedicated onboarding, Engagement Completion Gate, and workpaper index with sign-off. These capabilities support firms with formal quality control and multi-engagement workflows.',
  },
  {
    question: 'What does Enterprise include?',
    answer: 'Enterprise is designed for large firms and regional practices that need unlimited seats, a dedicated account manager, custom integrations, on-premise deployment options, and a tailored SLA. Contact our sales team to discuss your requirements.',
  },
  {
    question: 'Can I downgrade my plan?',
    answer: 'Yes. You can downgrade at any time. When downgrading, your current plan remains active until the end of the billing period. After that, your account transitions to the lower tier. Existing exports and metadata remain accessible; upload limits adjust to the new tier.',
  },
  {
    question: 'What payment methods do you accept?',
    answer: 'We accept all major credit cards. Annual plans and Organization accounts can also be invoiced. Enterprise contracts support custom payment terms.',
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
  const amount = interval === 'annual' ? tier.annualPrice : tier.monthlyPrice
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
    <main className="relative z-10 min-h-screen bg-gradient-obsidian">
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
              Twelve tools. Zero stored data. One platform. Pick the plan that matches your practice.
            </p>
            <p className="font-sans text-sm text-sage-400">
              Every plan includes a 7-day free trial — no credit card required to start.
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
            className="rounded-xl border border-sage-500/30 bg-sage-500/10 px-6 py-4 text-center"
          >
            <p className="font-sans text-sm text-sage-300">
              {billingInterval === 'monthly' ? (
                <>
                  <span className="font-semibold">Limited time:</span> 20% off your first 3 months on any monthly plan
                </>
              ) : (
                <>
                  <span className="font-semibold">Annual bonus:</span> Extra 10% off your first year on any annual plan
                </>
              )}
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
            animate="visible"
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
          className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 items-stretch"
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
                  {tier.isContactSales ? (
                    <div>
                      <span className="font-serif text-2xl text-oatmeal-100">Custom</span>
                    </div>
                  ) : (
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={`${tier.name}-${billingInterval}`}
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -6 }}
                        transition={{ duration: 0.2, ease: 'easeOut' as const }}
                      >
                        <span className={`text-oatmeal-100 ${hasDollar ? 'type-num-xl' : 'font-serif text-2xl'}`}>
                          {priceStr}
                        </span>
                        {billingInterval === 'annual' && hasDollar && (
                          <span className="block type-num-xs text-oatmeal-500 mt-0.5 line-through">
                            ${(tier.monthlyPrice * 12).toLocaleString()}/yr
                          </span>
                        )}
                      </motion.div>
                    </AnimatePresence>
                  )}
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

      {/* -- Seat Calculator ------------------- */}
      <section className="pb-20 px-6">
        <div className="max-w-xl mx-auto">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="visible"
          >
            <h2 className="type-headline-sm text-oatmeal-200 text-center mb-6">
              Need More Seats?
            </h2>
            <p className="font-sans text-sm text-oatmeal-400 text-center mb-6">
              Team and Organization plans include 3 seats. Add more as your team grows.
            </p>
            <SeatCalculator interval={billingInterval} />
          </motion.div>
        </div>
      </section>

      {/* -- Feature Comparison Table ---------- */}
      <section className="pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="visible"
          >
            <h2 className="type-headline-sm text-oatmeal-200 text-center mb-10">
              Feature Comparison
            </h2>

            <div className="overflow-x-auto rounded-2xl border border-obsidian-500/30">
              <table className="w-full text-left min-w-[600px]">
                <thead>
                  <tr className="border-b border-obsidian-500/30">
                    <th className="font-serif text-sm text-oatmeal-400 py-4 px-5 w-[20%]">Feature</th>
                    <th className="font-serif text-xs text-oatmeal-400 py-4 px-3 text-center w-[20%]">Solo</th>
                    <th className="font-serif text-xs text-sage-400 py-4 px-3 text-center w-[20%]">Team</th>
                    <th className="font-serif text-xs text-oatmeal-400 py-4 px-3 text-center w-[20%]">Organization</th>
                    <th className="font-serif text-xs text-oatmeal-400 py-4 px-3 text-center w-[20%]">Enterprise</th>
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
                      <td className="py-3 px-3 text-center"><CellContent value={row.solo} /></td>
                      <td className="py-3 px-3 text-center"><CellContent value={row.team} /></td>
                      <td className="py-3 px-3 text-center"><CellContent value={row.organization} /></td>
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
