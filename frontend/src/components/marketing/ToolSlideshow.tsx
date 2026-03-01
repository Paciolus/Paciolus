'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { BrandIcon, type BrandIconName } from '@/components/shared'
import { VIEWPORT } from '@/utils/marketingMotion'

/**
 * ToolSlideshow — Centered Hero Layout
 *
 * Full-screen animated slideshow for the 12-tool suite.
 * Each tool gets a dedicated centered slide with:
 * - Dominant tool name (large serif heading)
 * - Extended value proposition
 * - Capabilities grid (2-col)
 * - Standards pills + export formats
 * - CTA
 *
 * Team-only tools show a subtle inline note.
 * Bottom: compact 4-tier pricing summary.
 *
 * Navigation: arrows + dots + keyboard.
 */

// ── Types ────────────────────────────────────────────────────────────

type ToolTier = 'solo' | 'team'

interface ToolSlide {
  title: string
  shortTitle: string
  description: string
  valueProposition: string
  href: string
  icon: BrandIconName
  tier: ToolTier
  cluster: string
  tests?: number
  standards: string[]
  capabilities: string[]
}

// ── Tool Data ────────────────────────────────────────────────────────

const TOOLS: ToolSlide[] = [
  {
    title: 'Trial Balance Diagnostics',
    shortTitle: 'TB Diagnostics',
    description: 'Anomaly detection, ratio analysis, lead sheet mapping, and financial statement generation.',
    valueProposition: 'Upload a trial balance and receive a complete diagnostic workup in under three seconds. Seventeen financial ratios, automated account classification, anomaly flagging, and full financial statement generation — all from a single file upload. The foundation of every engagement.',
    href: '/tools/trial-balance',
    icon: 'calculator',
    tier: 'solo',
    cluster: 'Analyze',
    standards: ['ISA 520', 'ISA 315', 'IAS 1'],
    capabilities: ['17 financial ratios', 'A-Z lead sheet mapping', 'Balance sheet & income statement', 'Anomaly detection engine', 'Classification validator'],
  },
  {
    title: 'Multi-Period Comparison',
    shortTitle: 'Multi-Period',
    description: 'Compare up to three periods side-by-side with variance analysis and budget tracking.',
    valueProposition: 'Place two or three trial balance periods side by side and instantly surface account movements, significant variances, and budget deviations. Reclassification detection highlights accounts that shifted between periods — critical for identifying misstatement risk before fieldwork begins.',
    href: '/tools/multi-period',
    icon: 'trend-chart',
    tier: 'solo',
    cluster: 'Analyze',
    standards: ['ISA 520', 'ISA 315'],
    capabilities: ['2-way & 3-way comparison', 'Budget variance analysis', 'Reclassification detection', 'Material movement flags', 'Period-over-period trends'],
  },
  {
    title: 'Journal Entry Testing',
    shortTitle: 'JE Testing',
    description: "Benford's Law, structural validation, and statistical anomaly detection across the GL.",
    valueProposition: "Upload your general ledger extract and run a 19-test battery that covers everything from Benford's Law digit distribution to weekend/holiday posting detection. Stratified sampling isolates high-risk entries for focused review. Every flagged item traces to a specific ISA or PCAOB standard.",
    href: '/tools/journal-entry-testing',
    icon: 'shield-check',
    tier: 'solo',
    cluster: 'Detect',
    tests: 19,
    standards: ['ISA 240', 'ISA 240.A40', 'PCAOB AS 2401', 'ISA 530'],
    capabilities: ["Benford's Law analysis", 'Weekend & holiday posting', 'Round number concentration', 'Stratified sampling (ISA 530)', 'Duplicate entry detection'],
  },
  {
    title: 'Revenue Testing',
    shortTitle: 'Revenue',
    description: 'ISA 240 fraud risk plus ASC 606 / IFRS 15 recognition timing and cut-off analysis.',
    valueProposition: 'Revenue recognition is the highest fraud risk area on every engagement. Run 16 automated tests covering recognition timing, cut-off analysis, and contract mechanics. Optional ASC 606 / IFRS 15 contract columns unlock four additional tests — SSP allocation, obligation linkage, modification treatment, and recognition timing.',
    href: '/tools/revenue-testing',
    icon: 'currency-circle',
    tier: 'solo',
    cluster: 'Detect',
    tests: 16,
    standards: ['ISA 240', 'ASC 606', 'IFRS 15', 'ISA 240.A32'],
    capabilities: ['Recognition timing analysis', 'Cut-off risk detection', 'Contract-aware testing (optional)', 'SSP allocation validation', 'Fraud risk indicators'],
  },
  {
    title: 'AP Payment Testing',
    shortTitle: 'AP Testing',
    description: 'Duplicate detection, vendor concentration, and fraud indicators across payables.',
    valueProposition: 'Upload your AP payment register and surface duplicate payments, vendor concentration risks, and fraud indicators across 13 automated tests. Pattern matching catches near-duplicates that manual review misses — same vendor, same amount, different dates. Every finding maps to a specific PCAOB standard.',
    href: '/tools/ap-testing',
    icon: 'document-duplicate',
    tier: 'solo',
    cluster: 'Validate',
    tests: 13,
    standards: ['PCAOB AS 2401', 'ISA 240', 'ISA 500'],
    capabilities: ['Duplicate payment detection', 'Vendor concentration analysis', 'Round number patterns', 'Unusual timing flags', 'Fraud indicator scoring'],
  },
  {
    title: 'Bank Reconciliation',
    shortTitle: 'Bank Rec',
    description: 'Match bank transactions against the general ledger with automated reconciliation.',
    valueProposition: 'Upload both your bank statement and GL cash detail. The matching engine reconciles transactions by exact amount, auto-categorizes unmatched items, and produces a reconciliation bridge. Dual-file ingestion means no manual cross-referencing — the platform does the heavy lifting.',
    href: '/tools/bank-rec',
    icon: 'arrows-vertical',
    tier: 'solo',
    cluster: 'Validate',
    standards: ['ISA 500', 'ISA 505'],
    capabilities: ['Exact amount matching', 'Auto-categorization', 'Reconciliation bridge', 'Dual-file ingestion', 'Unmatched item flagging'],
  },
  {
    title: 'Statistical Sampling',
    shortTitle: 'Sampling',
    description: 'ISA 530 / PCAOB AS 2315 compliant MUS and random sampling with Stringer bounds.',
    valueProposition: 'Design your sample using ISA 530-compliant parameters, then evaluate results with Stringer bound analysis. Two-phase workflow mirrors audit methodology — design and select first, evaluate exceptions second. Supports both monetary unit sampling (MUS) and random selection with 2-tier stratification.',
    href: '/tools/statistical-sampling',
    icon: 'bar-chart',
    tier: 'team',
    cluster: 'Analyze',
    standards: ['ISA 530', 'PCAOB AS 2315'],
    capabilities: ['Monetary unit sampling (MUS)', 'Random sampling', '2-tier stratification', 'Stringer bound evaluation', 'Two-phase workflow'],
  },
  {
    title: 'Payroll Testing',
    shortTitle: 'Payroll',
    description: 'Ghost employee detection, duplicate payments, and payroll anomaly analysis.',
    valueProposition: 'Upload your payroll register and detect ghost employees, duplicate payments, and statistical anomalies across 11 automated tests. Pattern analysis surfaces employees with identical bank details, addresses, or tax identifiers — the most common indicators of payroll fraud schemes.',
    href: '/tools/payroll-testing',
    icon: 'users',
    tier: 'team',
    cluster: 'Detect',
    tests: 11,
    standards: ['ISA 240', 'PCAOB AS 2401'],
    capabilities: ['Ghost employee detection', 'Duplicate payment analysis', 'Shared bank detail flags', 'Statistical outlier detection', 'Address clustering'],
  },
  {
    title: 'Three-Way Match',
    shortTitle: '3-Way Match',
    description: 'PO-Invoice-Receipt matching with exact PO# linkage and procurement variance analysis.',
    valueProposition: 'Upload purchase orders, invoices, and receiving reports. The matching engine links records by exact PO number with fuzzy fallback, then quantifies variances between authorized, billed, and received amounts. Exception reporting highlights procurement integrity failures that require investigation.',
    href: '/tools/three-way-match',
    icon: 'circle-check',
    tier: 'team',
    cluster: 'Validate',
    standards: ['ISA 500', 'PCAOB AS 2401'],
    capabilities: ['Exact PO# linkage', 'Fuzzy match fallback', 'Variance quantification', 'Exception reporting', 'Procurement integrity'],
  },
  {
    title: 'AR Aging Analysis',
    shortTitle: 'AR Aging',
    description: 'Receivables aging with concentration risk, stale balances, and allowance adequacy.',
    valueProposition: 'Analyze receivables aging across 11 automated tests. Surface concentration risk in your customer base, identify stale balances requiring write-off evaluation, and assess allowance adequacy. Optional sub-ledger upload enables granular customer-level analysis alongside TB-level diagnostics.',
    href: '/tools/ar-aging',
    icon: 'clock',
    tier: 'team',
    cluster: 'Assess',
    tests: 11,
    standards: ['ISA 540', 'ISA 500', 'ASC 326'],
    capabilities: ['Aging bucket analysis', 'Concentration risk detection', 'Stale balance identification', 'Allowance adequacy assessment', 'Dual-input (TB + sub-ledger)'],
  },
  {
    title: 'Fixed Asset Testing',
    shortTitle: 'Fixed Assets',
    description: 'PP&E depreciation, useful life, and residual value anomaly detection per IAS 16.',
    valueProposition: 'Upload your fixed asset register and run 9 automated tests covering depreciation accuracy, useful life reasonableness, and residual value anomalies. Pattern analysis catches assets with inconsistent depreciation methods, unusual capitalizations, and items that should have been fully depreciated but carry remaining book value.',
    href: '/tools/fixed-assets',
    icon: 'building',
    tier: 'team',
    cluster: 'Assess',
    tests: 9,
    standards: ['IAS 16', 'ASC 360', 'ISA 540'],
    capabilities: ['Depreciation accuracy check', 'Useful life analysis', 'Residual value anomalies', 'Capitalization threshold test', 'Fully depreciated asset scan'],
  },
  {
    title: 'Inventory Testing',
    shortTitle: 'Inventory',
    description: 'Unit cost outliers, slow-moving detection, and valuation anomalies per IAS 2.',
    valueProposition: 'Analyze your inventory register for valuation anomalies, slow-moving items, and obsolescence indicators across 9 automated tests. Unit cost outlier detection surfaces items priced significantly above or below category averages. Slow-moving analysis identifies carrying risk — the items most likely to require write-down.',
    href: '/tools/inventory-testing',
    icon: 'cube',
    tier: 'team',
    cluster: 'Assess',
    tests: 9,
    standards: ['IAS 2', 'ASC 330', 'ISA 501'],
    capabilities: ['Unit cost outlier detection', 'Slow-moving inventory flags', 'Obsolescence indicators', 'Valuation anomaly detection', 'NRV assessment signals'],
  },
]

// ── Animation Variants ───────────────────────────────────────────────

const slideVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 400 : -400,
    opacity: 0,
    scale: 0.95,
  }),
  center: {
    x: 0,
    opacity: 1,
    scale: 1,
  },
  exit: (direction: number) => ({
    x: direction < 0 ? 400 : -400,
    opacity: 0,
    scale: 0.95,
  }),
}

const slideTransition = {
  x: { type: 'spring' as const, stiffness: 300, damping: 30 },
  opacity: { duration: 0.3 },
  scale: { duration: 0.3 },
}

// ── Slide Content (Centered Hero) ───────────────────────────────────

function SlideContent({ tool }: { tool: ToolSlide }) {
  const isTeam = tool.tier === 'team'

  return (
    <div className="flex flex-col items-center text-center max-w-3xl mx-auto">
      {/* Cluster + Test Count Label */}
      <div className="flex items-center gap-2 mb-5">
        <div className="w-8 h-8 rounded-lg bg-sage-500/12 text-sage-400 flex items-center justify-center">
          <BrandIcon name={tool.icon} className="w-4 h-4" />
        </div>
        <span className="font-sans text-[10px] uppercase tracking-[0.2em] text-oatmeal-600">
          {tool.cluster}
        </span>
        {tool.tests && (
          <>
            <span className="text-obsidian-500 text-[10px]">&middot;</span>
            <span className="font-mono text-[10px] text-oatmeal-600 tabular-nums">
              {tool.tests} automated tests
            </span>
          </>
        )}
      </div>

      {/* Tool Name — Dominant */}
      <h3 className="font-serif text-4xl md:text-5xl text-oatmeal-100 mb-5 leading-tight">
        {tool.title}
      </h3>

      {/* Value Proposition */}
      <p className="font-sans text-sm text-oatmeal-400 leading-relaxed max-w-2xl mb-6">
        {tool.valueProposition}
      </p>

      {/* Team-only note */}
      {isTeam && (
        <p className="font-sans text-xs text-oatmeal-600 italic mb-6">
          Available on Team, Organization, and Enterprise plans
        </p>
      )}

      {/* Capabilities Grid — 2 columns */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2.5 max-w-xl mb-7">
        {tool.capabilities.map((cap) => (
          <div key={cap} className="flex items-start gap-2.5 text-left">
            <svg
              className="w-3.5 h-3.5 text-sage-500 shrink-0 mt-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            <span className="font-sans text-sm text-oatmeal-400">
              {cap}
            </span>
          </div>
        ))}
      </div>

      {/* Standards + Export Formats */}
      <div className="flex flex-wrap items-center justify-center gap-2 mb-4">
        {tool.standards.map((s) => (
          <span
            key={s}
            className="px-2.5 py-1 rounded-md bg-obsidian-800/60 border border-obsidian-500/20 font-mono text-[10px] text-oatmeal-500"
          >
            {s}
          </span>
        ))}
      </div>
      <div className="flex items-center gap-1.5 mb-8">
        <span className="font-sans text-[10px] text-oatmeal-700 uppercase tracking-widest">
          Exports
        </span>
        {['PDF', 'XLSX', 'CSV'].map((fmt, i) => (
          <span key={fmt} className="font-mono text-[10px] text-oatmeal-500">
            {i > 0 && <span className="text-obsidian-500 mx-1">&middot;</span>}
            {fmt}
          </span>
        ))}
      </div>

      {/* CTA */}
      <Link
        href={tool.href}
        className="group inline-flex items-center gap-2 px-7 py-3 rounded-xl font-sans text-sm font-medium bg-sage-600 text-white hover:bg-sage-500 shadow-lg shadow-sage-600/20 transition-all"
      >
        Try This Tool
        <BrandIcon name="chevron-right" className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
      </Link>
    </div>
  )
}

// ── Navigation Arrows ────────────────────────────────────────────────

function NavArrow({
  direction,
  onClick,
  disabled,
}: {
  direction: 'left' | 'right'
  onClick: () => void
  disabled: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={direction === 'left' ? 'Previous tool' : 'Next tool'}
      className={`
        absolute top-1/2 -translate-y-1/2 z-20
        w-12 h-12 rounded-full flex items-center justify-center
        bg-obsidian-800/70 border border-obsidian-500/30
        text-oatmeal-400 backdrop-blur-sm
        transition-all duration-200
        ${disabled
          ? 'opacity-20 cursor-not-allowed'
          : 'hover:bg-obsidian-700/80 hover:border-obsidian-500/50 hover:text-oatmeal-200 hover:scale-105'
        }
        ${direction === 'left' ? 'left-0 lg:-left-6' : 'right-0 lg:-right-6'}
      `}
    >
      <svg
        className={`w-5 h-5 ${direction === 'right' ? '' : 'rotate-180'}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </button>
  )
}

// ── Dot Indicators ───────────────────────────────────────────────────

function DotIndicators({
  total,
  current,
  onSelect,
}: {
  total: number
  current: number
  onSelect: (index: number) => void
}) {
  return (
    <div className="flex items-center justify-center gap-2" role="tablist" aria-label="Tool slides">
      {Array.from({ length: total }).map((_, i) => {
        const tool = TOOLS[i]
        const isActive = i === current

        return (
          <button
            key={i}
            role="tab"
            aria-selected={isActive}
            aria-label={tool?.shortTitle ?? `Tool ${i + 1}`}
            onClick={() => onSelect(i)}
            className="group relative p-1.5"
          >
            <div className={`
              rounded-full transition-all duration-300
              ${isActive
                ? 'w-8 h-2.5 bg-sage-400'
                : 'w-2.5 h-2.5 bg-obsidian-500/60 group-hover:bg-obsidian-400/80'
              }
            `} />

            {/* Tooltip on hover */}
            <div className={`
              absolute bottom-full left-1/2 -translate-x-1/2 mb-2
              px-2.5 py-1 rounded-md bg-obsidian-900 border border-obsidian-500/30
              font-sans text-[10px] text-oatmeal-400 whitespace-nowrap
              opacity-0 group-hover:opacity-100 transition-opacity duration-200
              pointer-events-none
            `}>
              {tool?.shortTitle}
            </div>
          </button>
        )
      })}
    </div>
  )
}

// ── Pricing Tiers Data ──────────────────────────────────────────────

const PRICING_TIERS = [
  {
    name: 'Solo',
    price: '$50',
    period: '/mo',
    summary: '6 tools · 20 diagnostics/mo',
    popular: false,
  },
  {
    name: 'Team',
    price: '$130',
    period: '/mo',
    summary: 'All 12 tools · 3 seats included',
    popular: true,
  },
  {
    name: 'Organization',
    price: '$400',
    period: '/mo',
    summary: 'SSO · Completion gate · Onboarding',
    popular: false,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    summary: 'Unlimited seats · On-premise',
    popular: false,
  },
]

// ── Main Export ───────────────────────────────────────────────────────

export function ToolSlideshow() {
  const [[activeIndex, direction], setSlide] = useState([0, 0])
  const containerRef = useRef<HTMLDivElement>(null)

  const paginate = useCallback((newDirection: number) => {
    setSlide(([prev]) => {
      const next = prev + newDirection
      if (next < 0 || next >= TOOLS.length) return [prev, 0]
      return [next, newDirection]
    })
  }, [])

  const goTo = useCallback((index: number) => {
    setSlide(([prev]) => [index, index > prev ? 1 : -1])
  }, [])

  // Keyboard navigation
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      // Only respond if this section is somewhat visible
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      if (rect.bottom < 0 || rect.top > window.innerHeight) return

      if (e.key === 'ArrowLeft') paginate(-1)
      if (e.key === 'ArrowRight') paginate(1)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [paginate])

  const tool = TOOLS[activeIndex] as ToolSlide

  return (
    <section
      ref={containerRef}
      id="tools"
      className="relative z-10 py-20 px-6"
    >
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="text-center mb-14"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.5 }}
        >
          <div className="w-10 h-[2px] bg-sage-500 rounded-full mx-auto mb-5" />
          <h2 className="font-serif text-3xl md:text-4xl mb-3 bg-gradient-to-r from-sage-400 via-oatmeal-200 to-oatmeal-200 bg-clip-text text-transparent">
            Twelve Tools. One Platform.
          </h2>
          <p className="font-sans text-oatmeal-500 text-sm max-w-lg mx-auto">
            Twelve purpose-built tools. Explore each one to see exactly what you get.
          </p>
        </motion.div>

        {/* Slideshow Container */}
        <div className="relative">
          {/* Navigation Arrows */}
          <NavArrow
            direction="left"
            onClick={() => paginate(-1)}
            disabled={activeIndex === 0}
          />
          <NavArrow
            direction="right"
            onClick={() => paginate(1)}
            disabled={activeIndex === TOOLS.length - 1}
          />

          {/* Slide Area */}
          <div className="overflow-hidden px-4 lg:px-12">
            <AnimatePresence mode="wait" custom={direction}>
              <motion.div
                key={activeIndex}
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={slideTransition}
              >
                <SlideContent tool={tool} />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        {/* Dot Indicators */}
        <div className="mt-10">
          <DotIndicators
            total={TOOLS.length}
            current={activeIndex}
            onSelect={goTo}
          />
        </div>

        {/* Counter */}
        <div className="flex items-center justify-center mt-4">
          <span className="font-mono text-xs text-oatmeal-600 tabular-nums">
            {String(activeIndex + 1).padStart(2, '0')} / {String(TOOLS.length).padStart(2, '0')}
          </span>
        </div>

        {/* Compact 4-Tier Pricing Summary */}
        <motion.div
          className="mt-12"
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {PRICING_TIERS.map((tier) => (
              <Link
                key={tier.name}
                href="/pricing"
                className={`
                  group relative p-4 rounded-xl border text-center transition-all duration-200
                  ${tier.popular
                    ? 'bg-oatmeal-400/[0.06] border-oatmeal-400/25 hover:bg-oatmeal-400/[0.10] hover:border-oatmeal-400/40'
                    : 'bg-obsidian-800/30 border-obsidian-500/20 hover:bg-obsidian-800/50 hover:border-obsidian-500/35'
                  }
                `}
              >
                {tier.popular && (
                  <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded text-[9px] font-sans bg-oatmeal-400/15 text-oatmeal-400 border border-oatmeal-400/25 whitespace-nowrap">
                    Most popular
                  </span>
                )}
                <p className="font-serif text-sm text-oatmeal-200 mb-1">
                  {tier.name}
                </p>
                <p className="font-mono text-lg text-oatmeal-100 tabular-nums mb-1.5">
                  {tier.price}
                  {tier.period && (
                    <span className="font-sans text-xs text-oatmeal-600">{tier.period}</span>
                  )}
                </p>
                <p className="font-sans text-[11px] text-oatmeal-500 leading-snug">
                  {tier.summary}
                </p>
              </Link>
            ))}
          </div>

          {/* Compare plans link */}
          <div className="flex justify-center mt-5">
            <Link
              href="/pricing"
              className="group inline-flex items-center gap-1.5 font-sans text-xs text-oatmeal-600 hover:text-oatmeal-400 transition-colors"
            >
              Compare all plans
              <BrandIcon name="chevron-right" className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
