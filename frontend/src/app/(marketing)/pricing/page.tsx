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
type PersonaKey = 'solo' | 'mid-size' | 'large'
type TierName = 'Solo' | 'Team' | 'Organization'
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
    key: 'large',
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
  if (teamSize === '6-20' && uploads === '50+') return 'Organization'
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

const ORG_BASE_SEATS = 15
const MAX_ORG_SEATS = 75
const ORG_SEAT_MONTHLY = 55
const ORG_SEAT_ANNUAL = 550

function calculateOrgSeatCost(totalSeats: number, interval: BillingInterval): { baseCost: number; additionalSeats: number; seatCost: number; totalCost: number } | null {
  if (totalSeats > MAX_ORG_SEATS) return null
  const additionalSeats = Math.max(0, totalSeats - ORG_BASE_SEATS)
  const rate = interval === 'annual' ? ORG_SEAT_ANNUAL : ORG_SEAT_MONTHLY
  const baseCost = interval === 'annual' ? 4500 : 450
  const seatCost = additionalSeats * rate
  return { baseCost, additionalSeats, seatCost, totalCost: baseCost + seatCost }
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
          Save ~16.7%
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
  const [teamSize, setTeamSize] = useState(15)

  const handleChange = useCallback((value: string) => {
    const num = parseInt(value, 10)
    if (!isNaN(num) && num >= 1) {
      setTeamSize(Math.min(num, 999))
    } else if (value === '') {
      setTeamSize(1)
    }
  }, [])

  const exceedsLimit = teamSize > MAX_ORG_SEATS
  const breakdown = exceedsLimit ? null : calculateOrgSeatCost(teamSize, interval)
  const periodLabel = interval === 'annual' ? '/yr' : '/mo'

  return (
    <div className="rounded-xl border border-obsidian-500/30 bg-obsidian-800/60 p-6">
      <h3 className="font-serif text-sm text-oatmeal-200 mb-4">Organization Seat Calculator</h3>

      {/* Number input */}
      <div className="flex items-center gap-4 mb-5">
        <label htmlFor="seat-input" className="font-sans text-sm text-oatmeal-400 shrink-0">
          Enter your team size
        </label>
        <input
          id="seat-input"
          type="number"
          min={1}
          max={999}
          value={teamSize}
          onChange={(e) => handleChange(e.target.value)}
          className="w-24 px-3 py-2 rounded-lg bg-obsidian-700/50 border border-obsidian-500/40 text-oatmeal-100 font-mono text-sm tabular-nums text-center focus:outline-none focus:border-sage-500/50 transition-colors"
        />
      </div>

      {exceedsLimit ? (
        <div className="text-center py-4">
          <p className="font-sans text-sm text-oatmeal-300 mb-2">
            For teams larger than {MAX_ORG_SEATS} seats, we offer custom pricing.
          </p>
          <Link
            href="/contact?inquiry=seats"
            className="inline-flex items-center gap-2 font-sans text-sm text-sage-400 hover:text-sage-300 underline underline-offset-2"
          >
            Contact sales
          </Link>
        </div>
      ) : breakdown && (
        <div className="space-y-2.5 font-sans text-sm">
          <div className="flex justify-between text-oatmeal-400">
            <span>Base plan ({ORG_BASE_SEATS} seats included)</span>
            <span className="font-mono tabular-nums text-oatmeal-200">
              ${breakdown.baseCost.toLocaleString()}{periodLabel}
            </span>
          </div>
          {breakdown.additionalSeats > 0 && (
            <div className="flex justify-between text-oatmeal-400">
              <span>+{breakdown.additionalSeats} additional seat{breakdown.additionalSeats !== 1 ? 's' : ''} @ ${interval === 'annual' ? ORG_SEAT_ANNUAL : ORG_SEAT_MONTHLY}{periodLabel}</span>
              <span className="font-mono tabular-nums text-oatmeal-200">
                ${breakdown.seatCost.toLocaleString()}{periodLabel}
              </span>
            </div>
          )}
          <div className="flex justify-between pt-2.5 border-t border-obsidian-500/30 text-oatmeal-100 font-medium">
            <span>Total</span>
            <span className="font-mono tabular-nums text-lg">
              ${breakdown.totalCost.toLocaleString()}{periodLabel}
            </span>
          </div>
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
      { text: '7 tools: TB Diagnostics, Multi-Period, JE Testing, AP Payment & more' },
      { text: 'Client metadata management (10 clients)' },
      { text: 'PDF exports' },
      { text: 'Email support (next business day)' },
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
    monthlyPrice: 150,
    annualPrice: 1500,
    priceSubtitle: (interval) => interval === 'annual' ? 'per year, 3 seats included' : 'per month, 3 seats included',
    features: [
      { text: '100 uploads per month' },
      { text: '11 tools: Solo tools + Revenue, Bank Rec, Payroll & Three-Way Match' },
      { text: 'Diagnostic Workspace — engagement tracking, materiality cascade & follow-ups' },
      { text: 'Multi-Currency Conversion' },
      { text: '50 client records' },
      { text: 'PDF, Excel & CSV exports' },
      { text: 'Team collaboration — shared results, assignments & comments' },
      { text: '3 seats included (add more)' },
      { text: 'Priority support' },
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
    internalId: 'organization',
    monthlyPrice: 450,
    annualPrice: 4500,
    priceSubtitle: (interval) => interval === 'annual' ? 'per year, 15 seats included' : 'per month, 15 seats included',
    features: [
      { text: 'Everything in Team' },
      { text: 'All 12+ diagnostic tools including Statistical Sampling (ISA 530)' },
      { text: 'Unlimited uploads & clients' },
      { text: '15 seats included (up to 75)' },
      { text: 'Dedicated account manager' },
      { text: 'SSO & completion gate' },
      { text: 'Custom SLA & priority support' },
    ],
    cta: 'Start Free Trial',
    ctaHref: (interval) => `/register?plan=organization&interval=${interval}`,
    ctaFilled: false,
    hasSeats: true,
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
}

const comparisonRows: ComparisonRow[] = [
  { feature: 'Monthly uploads', solo: '20', team: '100', organization: 'Unlimited' },
  { feature: 'TB Diagnostics', solo: true, team: true, organization: true },
  { feature: 'Testing Tools', solo: '7 tools', team: '11 tools', organization: 'All 12+' },
  { feature: 'Diagnostic Workspace', solo: false, team: 'Engagement tracking & follow-ups', organization: 'Engagement tracking & follow-ups' },
  { feature: 'Statistical Sampling', solo: false, team: false, organization: true },
  { feature: 'Multi-Currency', solo: false, team: true, organization: true },
  { feature: 'Export Formats', solo: 'PDF', team: 'PDF, Excel & CSV', organization: 'PDF, Excel & CSV' },
  { feature: 'Client Records', solo: '10', team: '50', organization: 'Unlimited' },
  { feature: 'Team Seats', solo: '1', team: '3 (expandable to 25)', organization: '15 (expandable to 75)' },
  { feature: 'Team Collaboration', solo: false, team: 'Shared results & assignments', organization: 'Shared results & assignments' },
  { feature: 'Priority Support', solo: false, team: true, organization: true },
  { feature: 'Dedicated Account Manager', solo: false, team: false, organization: true },
  { feature: 'Support SLA', solo: 'Email — next business day', team: 'Email — 8 hr response', organization: 'Custom SLA' },
  { feature: 'File size limit', solo: '50 MB', team: '100 MB', organization: 'Custom' },
  { feature: 'Free Trial', solo: '7 days', team: '7 days', organization: '7 days' },
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
    answer: 'Annual billing saves you approximately 16.7% compared to paying month-to-month. Annual plans are billed as a single payment at the start of each billing year. Monthly plans are billed at the start of each calendar month.',
  },
  {
    question: 'How does the 7-day free trial work?',
    answer: 'Every paid plan includes a 7-day free trial with full feature access — no credit card required. You can cancel anytime during the trial. After 7 days, your selected plan begins billing automatically if a payment method is on file.',
  },
  {
    question: 'What happens when my trial expires?',
    answer: 'If you have not added a payment method by day 8, your account transitions to a read-only state. You can still log in, view client metadata, and download previously exported files, but new uploads and analyses are paused until you select a plan. No data is deleted — your account resumes the moment you subscribe.',
  },
  {
    question: 'What counts as an "upload"?',
    answer: 'Each file submitted to any tool counts as one upload. Re-uploading a corrected version of the same file counts as a separate upload. A multi-sheet Excel workbook counts as one upload. Uploading a trial balance to TB Diagnostics and then journal entries to JE Testing counts as two uploads (one per tool submission).',
  },
  {
    question: 'What promotions are available?',
    answer: 'New subscribers can receive 20% off the first 3 months on any monthly plan, or an extra 10% off the first year on any annual plan. Only one introductory discount applies per subscription.',
  },
  {
    question: 'How do Team seats work?',
    answer: 'The Team plan includes 3 seats. Additional seats can be added: seats 4-10 at $80/month ($800/year), seats 11-25 at $70/month ($700/year). The Organization plan includes 15 seats with additional seats at a flat $55/month ($550/year) each, up to 75 total.',
  },
  {
    question: 'What is the difference between Solo and Team?',
    answer: 'Solo includes 7 tools (TB Diagnostics, Multi-Period, JE Testing, AP Payment, and more) with PDF export. Team adds 4 more tools (Revenue Testing, Bank Reconciliation, Payroll Testing, Three-Way Match), Excel & CSV exports, Diagnostic Workspace (engagement tracking, materiality cascade, follow-up items), Multi-Currency Conversion, team collaboration with 3 included seats, and priority support.',
  },
  {
    question: 'What does "Team Collaboration" include?',
    answer: 'Team members on the same account can view each other\'s analysis results, assign follow-up items to specific team members, add comments on flagged anomalies, and share engagement workpapers. Each member works under a single client portfolio with unified engagement history.',
  },
  {
    question: 'What does Organization include?',
    answer: 'Organization ($450/mo) is designed for large firms and regional practices. It includes all 12+ tools (including Statistical Sampling), 15 seats (expandable to 75 at $55/seat), unlimited uploads and clients, a dedicated account manager, SSO, custom integrations, and a tailored SLA.',
  },
  {
    question: 'Are there file size or row limits?',
    answer: 'Solo plans support files up to 50 MB. Team plans support files up to 100 MB. Organization limits are configurable. There is no hard row limit — trial balances with 50,000+ rows are processed routinely. The platform supports 10 file formats: CSV, Excel (.xlsx/.xls), TSV, TXT, QBO, OFX, IIF, PDF (tabular), and ODS.',
  },
  {
    question: 'Can I downgrade my plan?',
    answer: 'Yes. You can downgrade at any time. When downgrading, your current plan remains active until the end of the billing period. After that, your account transitions to the lower tier. Existing exports and metadata remain accessible; upload limits adjust to the new tier.',
  },
  {
    question: 'What payment methods do you accept?',
    answer: 'We accept all major credit cards. Annual plans can also be invoiced. Organization contracts support custom payment terms.',
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
              Twelve tools. Zero financial data stored. One platform. Pick the plan that matches your practice.
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
                  <span className="font-semibold">Introductory offer:</span> 20% off your first 3 months on any monthly plan
                </>
              ) : (
                <>
                  <span className="font-semibold">Introductory offer:</span> Extra 10% off your first year on any annual plan
                </>
              )}
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
          {tiers.map((tier) => {
            const isPopular = tier.badge === 'Most Popular'
            const priceStr = formatPrice(tier, billingInterval)
            const hasDollar = priceStr.startsWith('$') && priceStr !== '$0'

            return (
              <motion.div
                key={tier.name}
                variants={cardVariants}
                className={`relative rounded-2xl p-6 flex flex-col border transition-all duration-200 ${
                  isPopular
                    ? 'bg-sage-500/15 border-sage-500/40 shadow-lg shadow-sage-500/10 hover:shadow-xl hover:shadow-sage-500/15 hover:-translate-y-1'
                    : 'bg-obsidian-800 border-obsidian-500/30 hover:border-obsidian-500/50 hover:shadow-lg hover:shadow-obsidian-900/40 hover:-translate-y-1'
                }`}
              >
                {/* Badge */}
                {tier.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="inline-block px-4 py-1 rounded-full bg-sage-500/25 border border-sage-500/50 text-sage-300 text-xs font-sans font-semibold tracking-wide whitespace-nowrap">
                      {tier.badge}
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
              Organization plans include 15 seats. Scale up to 75 with flat-rate pricing.
            </p>
            <SeatCalculator interval={billingInterval} />
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
                    <th className="font-serif text-sm text-oatmeal-400 py-4 px-5 w-[25%]">Feature</th>
                    <th className="font-serif text-xs text-oatmeal-400 py-4 px-3 text-center w-[25%]">Solo</th>
                    <th className="font-serif text-xs text-sage-400 py-4 px-3 text-center w-[25%]">Team</th>
                    <th className="font-serif text-xs text-oatmeal-400 py-4 px-3 text-center w-[25%]">Organization</th>
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
