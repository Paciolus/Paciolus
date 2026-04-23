// Pricing domain: all tier definitions, constants, and pure calculation functions.

/* ────────────────────────────────────────────────
   Estimator types
   ──────────────────────────────────────────────── */

export type Uploads = 'under-10' | 'under-100' | 'under-500' | 'unlimited'
export type Features = 'basic' | 'collab' | 'enterprise'
export type TeamSize = 'solo' | '2-5' | '6-20' | '20+'
export type PersonaKey = 'solo' | 'mid-size' | 'large'
export type TierName = 'Solo' | 'Professional' | 'Enterprise'
export type BillingInterval = 'monthly' | 'annual'

export interface Persona {
  key: PersonaKey
  label: string
  description: string
  icon: 'calculator' | 'building' | 'users'
  defaults: { uploads: Uploads; features: Features; teamSize: TeamSize }
}

export const personas: Persona[] = [
  {
    key: 'solo',
    label: 'Solo Practitioner',
    description: 'Independent CPA or consultant',
    icon: 'calculator',
    defaults: { uploads: 'under-100', features: 'basic', teamSize: 'solo' },
  },
  {
    key: 'mid-size',
    label: 'Mid-Size Firm',
    description: 'Growing practice, 2-20 staff',
    icon: 'building',
    defaults: { uploads: 'under-500', features: 'collab', teamSize: '2-5' },
  },
  {
    key: 'large',
    label: 'Large Firm',
    description: 'Multi-team department or regional firm',
    icon: 'users',
    defaults: { uploads: 'unlimited', features: 'enterprise', teamSize: '20+' },
  },
]

export const uploadOptions: { value: Uploads; label: string }[] = [
  { value: 'under-10', label: 'Under 10' },
  { value: 'under-100', label: 'Under 100' },
  { value: 'under-500', label: 'Under 500' },
  { value: 'unlimited', label: 'Unlimited' },
]

export const featureOptions: { value: Features; label: string }[] = [
  { value: 'basic', label: 'Core tools & exports' },
  { value: 'collab', label: '+ Team & sharing' },
  { value: 'enterprise', label: '+ Branding & bulk' },
]

export const teamOptions: { value: TeamSize; label: string }[] = [
  { value: 'solo', label: 'Just me' },
  { value: '2-5', label: '2-5 people' },
  { value: '6-20', label: '6-20 people' },
  { value: '20+', label: '20+ people' },
]

/* ────────────────────────────────────────────────
   Tier recommendation engine
   ──────────────────────────────────────────────── */

export function getRecommendedTier(uploads: Uploads, features: Features, teamSize: TeamSize): TierName {
  // Enterprise triggers
  if (teamSize === '20+') return 'Enterprise'
  if (features === 'enterprise') return 'Enterprise'
  if (uploads === 'unlimited') return 'Enterprise'
  // Professional triggers
  if (teamSize === '6-20') return 'Professional'
  if (features === 'collab') return 'Professional'
  if (uploads === 'under-500' && teamSize === '2-5') return 'Professional'
  if (uploads === 'under-500') return 'Professional'
  // Solo for everything else
  return 'Solo'
}

/* ────────────────────────────────────────────────
   Seat pricing constants (mirror backend price_config.py)
   ──────────────────────────────────────────────── */

export interface SeatCalcConfig {
  label: string
  baseSeats: number
  maxSeats: number
  seatMonthly: number
  seatAnnual: number
  baseMonthly: number
  baseAnnual: number
}

export const SEAT_CONFIGS: SeatCalcConfig[] = [
  {
    label: 'Professional',
    baseSeats: 7,
    maxSeats: 20,
    seatMonthly: 65,
    seatAnnual: 650,
    baseMonthly: 500,
    baseAnnual: 5000,
  },
  {
    label: 'Enterprise',
    baseSeats: 20,
    maxSeats: 100,
    seatMonthly: 45,
    seatAnnual: 450,
    baseMonthly: 1000,
    baseAnnual: 10000,
  },
]

export interface SeatBreakdown {
  baseCost: number
  additionalSeats: number
  seatCost: number
  totalCost: number
}

export function calculateSeatCost(
  config: SeatCalcConfig,
  totalSeats: number,
  interval: BillingInterval,
): SeatBreakdown | null {
  if (totalSeats > config.maxSeats) return null
  const additionalSeats = Math.max(0, totalSeats - config.baseSeats)
  const rate = interval === 'annual' ? config.seatAnnual : config.seatMonthly
  const baseCost = interval === 'annual' ? config.baseAnnual : config.baseMonthly
  const seatCost = additionalSeats * rate
  return { baseCost, additionalSeats, seatCost, totalCost: baseCost + seatCost }
}

/* ────────────────────────────────────────────────
   Tier definitions
   ──────────────────────────────────────────────── */

export interface TierFeature {
  text: string
}

export interface Tier {
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

export const tiers: Tier[] = [
  {
    name: 'Solo',
    internalId: 'solo',
    monthlyPrice: 100,
    annualPrice: 1000,
    priceSubtitle: (interval) => interval === 'annual' ? 'per year' : 'per month',
    features: [
      { text: '100 uploads per month' },
      { text: 'All 18 diagnostic tools' },
      { text: 'Unlimited clients' },
      { text: 'PDF, Excel & CSV exports' },
      { text: 'Diagnostic Workspace — engagement tracking & follow-ups' },
      { text: 'Email support (next business day)' },
      { text: '7-day free trial' },
    ],
    cta: 'Start Free Trial',
    ctaHref: (interval) => `/register?plan=solo&interval=${interval}`,
    ctaFilled: false,
    hasSeats: false,
  },
  {
    name: 'Professional',
    internalId: 'professional',
    monthlyPrice: 500,
    annualPrice: 5000,
    priceSubtitle: (interval) => interval === 'annual' ? 'per year, 7 seats included' : 'per month, 7 seats included',
    features: [
      { text: '500 uploads per month' },
      { text: 'All 18 diagnostic tools' },
      { text: 'Unlimited clients' },
      { text: 'All export formats' },
      { text: '7 seats included (up to 20)' },
      { text: 'Export sharing' },
      { text: 'Admin dashboard & activity logs' },
      { text: 'Priority support' },
      { text: '7-day free trial' },
    ],
    cta: 'Start Free Trial',
    ctaHref: (interval) => `/register?plan=professional&interval=${interval}`,
    ctaFilled: true,
    hasSeats: true,
  },
  {
    name: 'Enterprise',
    internalId: 'enterprise',
    monthlyPrice: 1000,
    annualPrice: 10000,
    priceSubtitle: (interval) => interval === 'annual' ? 'per year, 20 seats included' : 'per month, 20 seats included',
    features: [
      { text: 'Everything in Professional' },
      { text: 'Unlimited uploads & clients' },
      { text: '20 seats included (up to 100)' },
      { text: 'Bulk upload (up to 5 files)' },
      { text: 'Custom PDF branding' },
      { text: 'Dedicated account manager' },
      { text: 'Custom SLA & priority support' },
    ],
    cta: 'Start Free Trial',
    ctaHref: (interval) => `/register?plan=enterprise&interval=${interval}`,
    ctaFilled: false,
    hasSeats: true,
  },
]

/* ────────────────────────────────────────────────
   Feature comparison table data
   ──────────────────────────────────────────────── */

export type CellValue = true | false | string

export interface ComparisonRow {
  feature: string
  free: CellValue
  solo: CellValue
  professional: CellValue
  enterprise: CellValue
}

export const comparisonRows: ComparisonRow[] = [
  { feature: 'Monthly uploads', free: '10', solo: '100', professional: '500', enterprise: 'Unlimited' },
  { feature: 'Diagnostic Tools', free: '2 (TB + Flux)', solo: 'All 12', professional: 'All 12', enterprise: 'All 12' },
  { feature: 'Clients', free: '3', solo: 'Unlimited', professional: 'Unlimited', enterprise: 'Unlimited' },
  { feature: 'Export Formats', free: false, solo: 'PDF, Excel & CSV', professional: 'All formats', enterprise: 'All formats' },
  { feature: 'Diagnostic Workspace', free: false, solo: true, professional: true, enterprise: true },
  { feature: 'Team Seats', free: '1', solo: '1', professional: '7 (up to 20)', enterprise: '20 (up to 100)' },
  { feature: 'Export Sharing', free: false, solo: false, professional: true, enterprise: true },
  { feature: 'Admin Dashboard', free: false, solo: false, professional: true, enterprise: true },
  { feature: 'Activity Logs', free: false, solo: false, professional: true, enterprise: true },
  { feature: 'Bulk Upload', free: false, solo: false, professional: false, enterprise: true },
  { feature: 'Custom PDF Branding', free: false, solo: false, professional: false, enterprise: true },
  { feature: 'Priority Support', free: false, solo: false, professional: true, enterprise: true },
  { feature: 'Dedicated Account Manager', free: false, solo: false, professional: false, enterprise: true },
  { feature: 'Support SLA', free: 'Community', solo: 'Email — next business day', professional: 'Email — 8 hr response', enterprise: 'Custom SLA' },
  { feature: 'Free Trial', free: false, solo: '7 days', professional: '7 days', enterprise: '7 days' },
]

/* ────────────────────────────────────────────────
   FAQ data
   ──────────────────────────────────────────────── */

export interface FaqItem {
  question: string
  answer: string
}

export const faqItems: FaqItem[] = [
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
    question: 'How do seats work?',
    answer: `Professional includes ${SEAT_CONFIGS[0]!.baseSeats} seats with additional seats at $${SEAT_CONFIGS[0]!.seatMonthly}/month ($${SEAT_CONFIGS[0]!.seatAnnual}/year) each, up to ${SEAT_CONFIGS[0]!.maxSeats} total. Enterprise includes ${SEAT_CONFIGS[1]!.baseSeats} seats with additional seats at $${SEAT_CONFIGS[1]!.seatMonthly}/month ($${SEAT_CONFIGS[1]!.seatAnnual}/year) each, up to ${SEAT_CONFIGS[1]!.maxSeats} total. Solo is a single-seat plan.`,
  },
  {
    question: 'What is the difference between Solo and Professional?',
    answer: 'Both Solo and Professional include all 18 diagnostic tools and all export formats. Professional adds team collaboration (7 seats included), export sharing, admin dashboard with activity logs, and priority support. Professional is ideal for growing firms that need team-level visibility and collaboration.',
  },
  {
    question: 'What does Enterprise include beyond Professional?',
    answer: `Enterprise ($${tiers[2]!.monthlyPrice.toLocaleString()}/mo) adds unlimited uploads, ${SEAT_CONFIGS[1]!.baseSeats} seats included (expandable to ${SEAT_CONFIGS[1]!.maxSeats} at $${SEAT_CONFIGS[1]!.seatMonthly}/seat), bulk upload (up to 5 files at once), custom PDF branding with your firm logo, a dedicated account manager, and a custom SLA.`,
  },
  {
    question: 'What can Free users access?',
    answer: 'The Free tier gives you access to TB Diagnostics and Flux Analysis with up to 10 uploads per month and 3 clients. Exports are not available on the Free tier — upgrade to Solo or above to export results as PDF, Excel, or CSV.',
  },
  {
    question: 'Do uploads roll over between months?',
    answer: 'No. Upload limits reset at the start of each billing period. Unused uploads do not carry forward. Enterprise plans have unlimited uploads so rollover does not apply.',
  },
  {
    question: 'Are there file size or row limits?',
    answer: 'All plans support files up to 100 MB. There is no hard row limit — trial balances with 50,000+ rows are processed routinely. The platform supports 10 file formats: CSV, Excel (.xlsx/.xls), TSV, TXT, QBO, OFX, IIF, PDF (tabular), and ODS.',
  },
  {
    question: 'Can I downgrade my plan?',
    answer: 'Yes. You can downgrade at any time. When downgrading, your current plan remains active until the end of the billing period. After that, your account transitions to the lower tier. Existing exports and metadata remain accessible; upload limits adjust to the new tier.',
  },
  {
    question: 'What payment methods do you accept?',
    answer: 'We accept all major credit cards. Annual plans can also be invoiced. Enterprise contracts support custom payment terms.',
  },
]

/* ────────────────────────────────────────────────
   Price formatting helper (pure function)
   ──────────────────────────────────────────────── */

export function formatPrice(tier: Tier, interval: BillingInterval): string {
  const amount = interval === 'annual' ? tier.annualPrice : tier.monthlyPrice
  if (amount === 0) return '$0'
  return `$${amount.toLocaleString()}`
}

/* ────────────────────────────────────────────────
   Promo copy helper (pure function)
   ──────────────────────────────────────────────── */

export function getPromoCopy(interval: BillingInterval): { prefix: string; body: string } {
  return interval === 'monthly'
    ? { prefix: 'Introductory offer:', body: '20% off your first 3 months on any monthly plan' }
    : { prefix: 'Introductory offer:', body: 'Extra 10% off your first year on any annual plan' }
}

/* ────────────────────────────────────────────────
   Seat calculator description helper (pure function)
   ──────────────────────────────────────────────── */

export function getSeatCalculatorDescription(): string {
  const pro = SEAT_CONFIGS[0]!
  const ent = SEAT_CONFIGS[1]!
  return `Professional includes ${pro.baseSeats} seats (up to ${pro.maxSeats}). Enterprise includes ${ent.baseSeats} seats (up to ${ent.maxSeats}).`
}
