// Pricing domain: all tier definitions, constants, and pure calculation functions.

/**
 * Free-trial length in days. Mirrors `TRIAL_PERIOD_DAYS` in
 * backend/billing/price_config.py (pinned by tests/test_pricing_copy_consistency.py).
 */

import { PLANS, type PlanTier } from '@/content/plans.generated'

export const TRIAL_DAYS = 7

/**
 * Sprint 858: self-serve purchase of Professional and Enterprise. Launch sells
 * Solo only; those tiers show "Contact us" until Sprint 853 (firm-owned client
 * data) ships and flips this. Mirrors `SELF_SERVE_TEAM_TIERS_ENABLED` in
 * backend/billing/price_config.py (pinned by tests/test_pricing_copy_consistency.py),
 * which refuses the checkout session and seat add-ons while it is off.
 */
export const SELF_SERVE_TEAM_TIERS_ENABLED = false

const SALES_ONLY_TIER_IDS = new Set(['professional', 'enterprise'])

/** Where a sales-only plan's CTA goes: the contact form, "Organization" preselected. */
export const SALES_CONTACT_HREF = '/contact?inquiry=Organization'

/** CTA label for a sales-only plan. */
export const SALES_CONTACT_LABEL = 'Contact us'

/** Whether plan `id` can be bought (or have seats added) without talking to sales. */
export function isSelfServePlan(id: string): boolean {
  return SELF_SERVE_TEAM_TIERS_ENABLED || !SALES_ONLY_TIER_IDS.has(id)
}

/** The date the first charge lands when a trial starts on `start` (Sprint 842). */
export function trialChargeDate(start: Date): Date {
  const d = new Date(start.getTime())
  d.setDate(d.getDate() + TRIAL_DAYS)
  return d
}

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
  { value: 'enterprise', label: '+ Custom branding' },
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
   Plan facts — Sprint 891 (16B): from backend/shared/plans.json through the generated
   content/plans.generated.ts. Prices are stored in cents there.
   ──────────────────────────────────────────────── */

const ENT = {
  free: PLANS.tiers.free.entitlements,
  solo: PLANS.tiers.solo.entitlements,
  professional: PLANS.tiers.professional.entitlements,
  enterprise: PLANS.tiers.enterprise.entitlements,
}
const dollars = (cents: number): number => cents / 100

/** "100", or "Unlimited" when the plan file says 0. */
export function uploadsPerMonth(tier: PlanTier): string {
  return ENT[tier].uploads_per_month === 0 ? 'Unlimited' : String(ENT[tier].uploads_per_month)
}
export function clientsLimit(tier: PlanTier): string {
  return ENT[tier].max_clients === 0 ? 'Unlimited' : String(ENT[tier].max_clients)
}
/** "7 seats (up to 20)" for team plans; "1" for single-seat plans. */
export function seatsLabel(tier: PlanTier): string {
  const e = ENT[tier]
  return e.max_team_seats > 0 ? `${e.seats_included} (up to ${e.max_team_seats})` : String(e.seats_included)
}

/* ────────────────────────────────────────────────
   Seat pricing (derived from the plan file)
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

export const SEAT_CONFIGS: SeatCalcConfig[] = (['professional', 'enterprise'] as const).map(tier => ({
  label: tier === 'professional' ? 'Professional' : 'Enterprise',
  baseSeats: ENT[tier].seats_included,
  maxSeats: ENT[tier].max_team_seats,
  seatMonthly: dollars(PLANS.seat_price_cents[tier].monthly),
  seatAnnual: dollars(PLANS.seat_price_cents[tier].annual),
  baseMonthly: dollars(PLANS.tiers[tier].price_cents.monthly),
  baseAnnual: dollars(PLANS.tiers[tier].price_cents.annual),
}))

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
    monthlyPrice: dollars(PLANS.tiers.solo.price_cents.monthly),
    annualPrice: dollars(PLANS.tiers.solo.price_cents.annual),
    priceSubtitle: (interval) => interval === 'annual' ? 'per year' : 'per month',
    features: [
      { text: `${uploadsPerMonth('solo')} uploads per month` },
      { text: 'All 18 diagnostic tools' },
      { text: 'Unlimited clients' },
      { text: 'PDF, Excel & CSV exports' },
      { text: 'Diagnostic Workspace — engagement tracking & follow-ups' },
      { text: 'Email support (reply within 1–2 business days)' },
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
    monthlyPrice: dollars(PLANS.tiers.professional.price_cents.monthly),
    annualPrice: dollars(PLANS.tiers.professional.price_cents.annual),
    priceSubtitle: (interval) => `${interval === 'annual' ? 'per year' : 'per month'}, ${ENT.professional.seats_included} seats included`,
    features: [
      { text: `${uploadsPerMonth('professional')} uploads per month` },
      { text: 'All 18 diagnostic tools' },
      { text: 'Unlimited clients' },
      { text: 'All export formats' },
      { text: `${ENT.professional.seats_included} seats included (up to ${ENT.professional.max_team_seats})` },
      { text: 'Export sharing' },
      { text: 'Admin dashboard & activity logs' },
      { text: 'Email support (reply within 1–2 business days)' },
      // Sprint 858: no self-serve trial while the plan is sales-only.
      ...(isSelfServePlan('professional') ? [{ text: '7-day free trial' }] : []),
    ],
    cta: isSelfServePlan('professional') ? 'Start Free Trial' : SALES_CONTACT_LABEL,
    ctaHref: (interval) => isSelfServePlan('professional') ? `/register?plan=professional&interval=${interval}` : SALES_CONTACT_HREF,
    ctaFilled: true,
    hasSeats: true,
  },
  {
    name: 'Enterprise',
    internalId: 'enterprise',
    monthlyPrice: dollars(PLANS.tiers.enterprise.price_cents.monthly),
    annualPrice: dollars(PLANS.tiers.enterprise.price_cents.annual),
    priceSubtitle: (interval) => `${interval === 'annual' ? 'per year' : 'per month'}, ${ENT.enterprise.seats_included} seats included`,
    features: [
      { text: 'Everything in Professional' },
      { text: 'Unlimited uploads & clients' },
      { text: `${ENT.enterprise.seats_included} seats included (up to ${ENT.enterprise.max_team_seats})` },
      { text: 'Custom PDF branding' },
      { text: 'Email support (reply within 1–2 business days)' },
    ],
    cta: isSelfServePlan('enterprise') ? 'Start Free Trial' : SALES_CONTACT_LABEL,
    ctaHref: (interval) => isSelfServePlan('enterprise') ? `/register?plan=enterprise&interval=${interval}` : SALES_CONTACT_HREF,
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
  { feature: 'Monthly uploads', free: uploadsPerMonth('free'), solo: uploadsPerMonth('solo'), professional: uploadsPerMonth('professional'), enterprise: uploadsPerMonth('enterprise') },
  { feature: 'Diagnostic Tools', free: '2 (TB + Flux)', solo: 'All 18', professional: 'All 18', enterprise: 'All 18' },
  { feature: 'Clients', free: clientsLimit('free'), solo: clientsLimit('solo'), professional: clientsLimit('professional'), enterprise: clientsLimit('enterprise') },
  { feature: 'Export Formats', free: false, solo: 'PDF, Excel & CSV', professional: 'All formats', enterprise: 'All formats' },
  { feature: 'Diagnostic Workspace', free: ENT.free.workspace, solo: ENT.solo.workspace, professional: ENT.professional.workspace, enterprise: ENT.enterprise.workspace },
  { feature: 'Team Seats', free: seatsLabel('free'), solo: seatsLabel('solo'), professional: seatsLabel('professional'), enterprise: seatsLabel('enterprise') },
  { feature: 'Export Sharing', free: ENT.free.export_sharing, solo: ENT.solo.export_sharing, professional: ENT.professional.export_sharing, enterprise: ENT.enterprise.export_sharing },
  { feature: 'Admin Dashboard', free: ENT.free.admin_dashboard, solo: ENT.solo.admin_dashboard, professional: ENT.professional.admin_dashboard, enterprise: ENT.enterprise.admin_dashboard },
  { feature: 'Activity Logs', free: ENT.free.activity_logs, solo: ENT.solo.activity_logs, professional: ENT.professional.activity_logs, enterprise: ENT.enterprise.activity_logs },
  { feature: 'Custom PDF Branding', free: ENT.free.custom_branding, solo: ENT.solo.custom_branding, professional: ENT.professional.custom_branding, enterprise: ENT.enterprise.custom_branding },
  { feature: 'Support', free: 'Email', solo: 'Email', professional: 'Email', enterprise: 'Email' },
  {
    feature: 'Free Trial',
    free: false,
    solo: '7 days',
    // Sprint 858: sales-only plans have no self-serve trial.
    professional: isSelfServePlan('professional') ? '7 days' : SALES_CONTACT_LABEL,
    enterprise: isSelfServePlan('enterprise') ? '7 days' : SALES_CONTACT_LABEL,
  },
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
    answer: 'Annual billing saves you approximately 16.7% compared to paying month-to-month. Annual plans are billed as a single payment at the start of each billing year. Monthly plans are billed monthly from your start date.',
  },
  {
    question: 'How does the 7-day free trial work?',
    answer: `${SELF_SERVE_TEAM_TIERS_ENABLED ? 'Every paid plan' : 'The Solo plan'} starts with a ${TRIAL_DAYS}-day free trial with full feature access. A card is required when you start the trial, but you are not charged during it. On day ${TRIAL_DAYS + 1} we charge the plan price you chose, and then charge it again every month or year until you cancel. Cancel before the trial ends and you will not be charged. Checkout shows the exact amount and date before you enter your card.`,
  },
  // Sprint 858: while Professional and Enterprise are sales-only, say how to get them.
  ...(SELF_SERVE_TEAM_TIERS_ENABLED
    ? []
    : [{
        question: 'How do I sign up for Professional or Enterprise?',
        answer: "Professional and Enterprise are not available to buy online yet. Contact us and we will set up your firm's plan with you. Solo can be bought online today.",
      }]),
  {
    question: 'What happens when my trial expires?',
    answer: 'When the trial ends, your subscription continues on the plan you chose and the card on file is charged. If that charge fails, the rules for a failed payment below apply.',
  },
  {
    question: 'What happens if a payment fails?',
    answer: 'Paid features pause at the first failed payment: until a payment goes through, your account works as a Free account. We email you, and the card is retried over the following days. If the payment still has not gone through, the subscription is canceled 7 days after the third failed attempt. When a payment succeeds, paid features return. Your client list, analysis summaries and engagement entries remain readable throughout.',
  },
  {
    question: 'What counts as an "upload"?',
    answer: 'Each successful analysis run counts as one upload, whatever the number of files it takes: a run that compares two files (for example AR aging with its sub-ledger, or a current and prior period) counts once, and a multi-sheet Excel workbook counts once. A run that fails does not count. Running a corrected version of a file again counts as a new upload, and a trial balance in TB Diagnostics followed by journal entries in JE Testing counts as two.',
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
    answer: 'Both Solo and Professional include all 18 diagnostic tools and all export formats. Professional adds team collaboration (7 seats included), export sharing, and an admin dashboard with activity logs. Professional is ideal for growing firms that need team-level visibility and collaboration.',
  },
  {
    question: 'What does Enterprise include beyond Professional?',
    answer: `Enterprise ($${tiers[2]!.monthlyPrice.toLocaleString()}/mo) adds unlimited uploads, ${SEAT_CONFIGS[1]!.baseSeats} seats included (expandable to ${SEAT_CONFIGS[1]!.maxSeats} at $${SEAT_CONFIGS[1]!.seatMonthly}/seat) and custom PDF branding with your firm logo.`,
  },
  {
    question: 'What can Free users access?',
    answer: 'The Free tier gives you access to TB Diagnostics and Flux Analysis with up to 10 uploads per month and 3 clients. Exports are not available on the Free tier — upgrade to Solo or above to export results as PDF, Excel, or CSV.',
  },
  {
    question: 'Do uploads roll over between months?',
    answer: 'No. Upload limits reset every month, including on annual plans. Unused uploads do not carry forward. Enterprise plans have unlimited uploads so rollover does not apply.',
  },
  {
    question: 'Are there file size or row limits?',
    answer: 'Files can be up to 100 MB and 500,000 rows. The platform reads these file types: CSV, TSV, TXT, Excel (.xlsx, .xls), Word (.docx, tables), QBO, OFX, IIF and PDF (tables). The Free plan accepts CSV, TSV, TXT and Excel.',
  },
  {
    question: 'Can I downgrade my plan?',
    answer: 'Yes. You can downgrade at any time. When downgrading, your current plan remains active until the end of the billing period. After that, your account transitions to the lower tier. Your client list, analysis summaries and engagement entries stay in your account; upload limits adjust to the new tier. Exports are sent to your browser and not saved by Paciolus (except a report you share by link, which is deleted after 24 or 48 hours), so keep the ones you downloaded.',
  },
  {
    question: 'Does Paciolus keep my workpapers?',
    answer: 'No. Paciolus produces PDF memos and Excel/CSV workpapers. Your firm keeps them in its own documentation system; Paciolus is not a workpaper archive. Paciolus is not a substitute for your firm’s audit documentation and retention obligations. A report you share by link is stored for up to 24 hours (Professional) or 48 hours (Enterprise), then deleted.',
  },
  {
    question: 'What payment methods do you accept?',
    answer: 'We accept all major credit cards, processed by Stripe. If you need an invoice or other payment arrangements, contact us.',
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

/* ────────────────────────────────────────────────
   Id-keyed lookups (Sprint 818)
   Checkout and the upgrade modal key plans by backend id ('solo',
   'professional', 'enterprise'). They used to hard-code prices, base seats,
   seat limits and per-seat rates; they now read them from here.
   ──────────────────────────────────────────────── */

export function getTier(id: string): Tier | undefined {
  return tiers.find((t) => t.internalId === id)
}

function seatConfig(id: string): SeatCalcConfig | undefined {
  const tier = getTier(id)
  return tier?.hasSeats ? SEAT_CONFIGS.find((c) => c.label === tier.name) : undefined
}

export function tierPriceDollars(id: string, interval: BillingInterval): number | undefined {
  const tier = getTier(id)
  if (!tier) return undefined
  return interval === 'annual' ? tier.annualPrice : tier.monthlyPrice
}

export function baseSeats(id: string): number {
  return seatConfig(id)?.baseSeats ?? 1
}

export function maxAdditionalSeats(id: string): number {
  const config = seatConfig(id)
  return config ? config.maxSeats - config.baseSeats : 0
}

export function seatPriceDollars(id: string, interval: BillingInterval): number {
  const config = seatConfig(id)
  if (!config) return 0
  return interval === 'annual' ? config.seatAnnual : config.seatMonthly
}
