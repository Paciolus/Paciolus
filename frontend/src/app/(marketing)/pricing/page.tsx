'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'

/* ────────────────────────────────────────────────
   Estimator types & logic
   ──────────────────────────────────────────────── */

type Uploads = '1-5' | '6-20' | '21-50' | '50+'
type Tools = 'tb-only' | '3-5' | 'all-12'
type TeamSize = 'solo' | '2-10' | '10+'
type PersonaKey = 'solo' | 'mid-size' | 'enterprise'
type TierName = 'Free' | 'Professional' | 'Enterprise'

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
    description: 'Growing practice, 2–20 staff',
    icon: 'building',
    defaults: { uploads: '21-50', tools: '3-5', teamSize: '2-10' },
  },
  {
    key: 'enterprise',
    label: 'Enterprise',
    description: 'Large firm or corporate department',
    icon: 'users',
    defaults: { uploads: '50+', tools: 'all-12', teamSize: '10+' },
  },
]

const uploadOptions: { value: Uploads; label: string }[] = [
  { value: '1-5', label: '1–5' },
  { value: '6-20', label: '6–20' },
  { value: '21-50', label: '21–50' },
  { value: '50+', label: '50+' },
]

const toolOptions: { value: Tools; label: string }[] = [
  { value: 'tb-only', label: 'TB Diagnostics only' },
  { value: '3-5', label: '3–5 tools' },
  { value: 'all-12', label: 'All 12 tools' },
]

const teamOptions: { value: TeamSize; label: string }[] = [
  { value: 'solo', label: 'Just me' },
  { value: '2-10', label: '2–10 people' },
  { value: '10+', label: '10+ people' },
]

function getRecommendedTier(uploads: Uploads, tools: Tools, teamSize: TeamSize): TierName {
  if (teamSize === '10+') return 'Enterprise'
  if (tools === 'all-12') return 'Professional'
  if (uploads === '50+') return 'Professional'
  if (uploads === '21-50') return 'Professional'
  if (tools === '3-5') return 'Professional'
  if (teamSize === '2-10') return 'Professional'
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
  const [uploads, setUploads] = useState<Uploads>('1-5')
  const [tools, setTools] = useState<Tools>('tb-only')
  const [teamSize, setTeamSize] = useState<TeamSize>('solo')
  const [activePersona, setActivePersona] = useState<PersonaKey | null>(null)

  const recommendedTier = getRecommendedTier(uploads, tools, teamSize)

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
      {/* ── Hero Section ──────────────────────── */}
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
              Start free. Upgrade when you need more.
            </p>
          </motion.div>
        </div>
      </section>

      {/* ── Plan Estimator ────────────────────── */}
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

      {/* ── Pricing Cards ─────────────────────── */}
      <section className="pb-20 px-6">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-60px' }}
          className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch"
        >
          {tiers.map((tier) => {
            const isRecommended = tier.name === recommendedTier
            const highlighted = isRecommended
            const badge = isRecommended
              ? 'Best Fit for You'
              : tier.badge && tier.name !== recommendedTier
                ? tier.badge
                : undefined

            return (
            <motion.div
              key={tier.name}
              variants={cardVariants}
              className={`relative rounded-2xl p-8 flex flex-col border ${
                highlighted
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
              <h3 className="font-serif text-xl text-oatmeal-200 mb-4">{tier.name}</h3>

              {/* Price */}
              <div className="mb-6">
                <span className={`text-oatmeal-100 ${tier.price.startsWith('$') ? 'type-proof' : 'font-serif text-3xl'}`}>
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
                    <span className="type-body-sm text-oatmeal-300">{feature.text}</span>
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
            )
          })}
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
            <h2 className="type-headline-sm text-oatmeal-200 text-center mb-10">
              Feature Comparison
            </h2>

            <div className="overflow-x-auto rounded-2xl border border-obsidian-500/30">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-obsidian-500/30">
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
                      className={`border-b border-obsidian-500/20 last:border-b-0 ${
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
