'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { BrandIcon, type BrandIconName } from '@/components/shared'
import { STAGGER, ENTER, VIEWPORT } from '@/utils/marketingMotion'

/**
 * ToolShowcase — Redesigned
 *
 * Full 12-tool grid with tier-gating visualization.
 * Filter tabs let visitors scope by pricing plan so they immediately
 * understand what's included — and what's available with an upgrade.
 */

type ToolTier = 'solo' | 'team'
type ActiveFilter = 'all' | 'solo' | 'team'

interface Tool {
  title: string
  description: string
  href: string
  icon: BrandIconName
  tier: ToolTier
  cluster: string
  tests?: number
}

const TOOLS: Tool[] = [
  // ─── Solo tier (6 tools · available from $50/mo) ─────────────────────
  {
    title: 'Trial Balance Diagnostics',
    description: 'Anomaly detection, ratio analysis, lead sheet mapping, and financial statement generation.',
    href: '/tools/trial-balance',
    icon: 'calculator',
    tier: 'solo',
    cluster: 'Analyze',
  },
  {
    title: 'Multi-Period Comparison',
    description: 'Compare up to three periods side-by-side with variance analysis and budget tracking.',
    href: '/tools/multi-period',
    icon: 'trend-chart',
    tier: 'solo',
    cluster: 'Analyze',
  },
  {
    title: 'Journal Entry Testing',
    description: "Benford's Law, structural validation, and statistical anomaly detection across the GL.",
    href: '/tools/journal-entry-testing',
    icon: 'shield-check',
    tier: 'solo',
    cluster: 'Detect',
    tests: 19,
  },
  {
    title: 'Revenue Testing',
    description: 'ISA 240 fraud risk plus ASC 606 / IFRS 15 recognition timing and cut-off analysis.',
    href: '/tools/revenue-testing',
    icon: 'currency-circle',
    tier: 'solo',
    cluster: 'Detect',
    tests: 16,
  },
  {
    title: 'AP Payment Testing',
    description: 'Duplicate detection, vendor concentration, and fraud indicators across payables.',
    href: '/tools/ap-testing',
    icon: 'document-duplicate',
    tier: 'solo',
    cluster: 'Validate',
    tests: 13,
  },
  {
    title: 'Bank Reconciliation',
    description: 'Match bank transactions against the general ledger with automated reconciliation.',
    href: '/tools/bank-rec',
    icon: 'arrows-vertical',
    tier: 'solo',
    cluster: 'Validate',
  },
  // ─── Team tier (6 additional · available from $130/mo) ───────────────
  {
    title: 'Statistical Sampling',
    description: 'ISA 530 / PCAOB AS 2315 compliant MUS and random sampling with Stringer bounds.',
    href: '/tools/statistical-sampling',
    icon: 'bar-chart',
    tier: 'team',
    cluster: 'Analyze',
  },
  {
    title: 'Payroll Testing',
    description: 'Ghost employee detection, duplicate payments, and payroll anomaly analysis.',
    href: '/tools/payroll-testing',
    icon: 'users',
    tier: 'team',
    cluster: 'Detect',
    tests: 11,
  },
  {
    title: 'Three-Way Match',
    description: 'PO-Invoice-Receipt matching with exact PO# linkage and procurement variance analysis.',
    href: '/tools/three-way-match',
    icon: 'circle-check',
    tier: 'team',
    cluster: 'Validate',
  },
  {
    title: 'AR Aging Analysis',
    description: 'Receivables aging with concentration risk, stale balances, and allowance adequacy.',
    href: '/tools/ar-aging',
    icon: 'clock',
    tier: 'team',
    cluster: 'Assess',
    tests: 11,
  },
  {
    title: 'Fixed Asset Testing',
    description: 'PP&E depreciation, useful life, and residual value anomaly detection per IAS 16.',
    href: '/tools/fixed-assets',
    icon: 'building',
    tier: 'team',
    cluster: 'Assess',
    tests: 9,
  },
  {
    title: 'Inventory Testing',
    description: 'Unit cost outliers, slow-moving detection, and valuation anomalies per IAS 2.',
    href: '/tools/inventory-testing',
    icon: 'cube',
    tier: 'team',
    cluster: 'Assess',
    tests: 9,
  },
]

const SOLO_COUNT = TOOLS.filter(t => t.tier === 'solo').length   // 6
const TOTAL_COUNT = TOOLS.length                                  // 12

const FILTER_TABS: { id: ActiveFilter; label: string; sub: string }[] = [
  { id: 'all',  label: 'All 12 tools', sub: '' },
  { id: 'solo', label: 'Solo',         sub: `${SOLO_COUNT} tools · $50/mo` },
  { id: 'team', label: 'Team',         sub: `All ${TOTAL_COUNT} tools · $130/mo` },
]

export function ToolShowcase() {
  const [filter, setFilter] = useState<ActiveFilter>('all')

  return (
    <section id="tools" className="relative z-10 py-24 px-6">
      <div className="max-w-7xl mx-auto">

        {/* ── Header ─────────────────────────────────────────── */}
        <motion.div
          className="text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-serif text-3xl md:text-4xl text-oatmeal-200 mb-3">
            The Complete Audit Intelligence Suite
          </h2>
          <p className="font-sans text-oatmeal-500 text-sm max-w-lg mx-auto">
            Twelve purpose-built tools. Start with Solo — upgrade as your practice grows.
          </p>
        </motion.div>

        {/* ── Tier Filter Tabs ────────────────────────────────── */}
        <motion.div
          className="flex justify-center mb-10"
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          <div
            role="group"
            aria-label="Filter tools by plan"
            className="inline-flex items-stretch gap-1 p-1 rounded-xl bg-obsidian-900/60 border border-obsidian-500/25"
          >
            {FILTER_TABS.map((tab) => (
              <button
                key={tab.id}
                aria-pressed={filter === tab.id}
                onClick={() => setFilter(tab.id)}
                className={`
                  px-4 py-2 rounded-lg text-left transition-all duration-200 min-w-[100px]
                  ${filter === tab.id
                    ? 'bg-obsidian-700 shadow-sm'
                    : 'hover:bg-obsidian-800/50'
                  }
                `}
              >
                <span className={`font-sans text-sm font-medium block transition-colors ${
                  filter === tab.id ? 'text-oatmeal-100' : 'text-oatmeal-500'
                }`}>
                  {tab.label}
                </span>
                {tab.sub && (
                  <span className={`font-sans text-[10px] block transition-colors ${
                    filter === tab.id ? 'text-oatmeal-500' : 'text-oatmeal-700'
                  }`}>
                    {tab.sub}
                  </span>
                )}
              </button>
            ))}
          </div>
        </motion.div>

        {/* ── 12-Tool Grid ────────────────────────────────────── */}
        <motion.div
          variants={STAGGER.fast}
          initial="hidden"
          whileInView="visible"
          viewport={VIEWPORT.eager}
          className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3"
        >
          {TOOLS.map((tool) => {
            const locked  = filter === 'solo' && tool.tier === 'team'
            const isSolo  = tool.tier === 'solo'

            return (
              <motion.div key={tool.href} variants={ENTER.fadeUp}>
                <Link
                  href={locked ? '/pricing' : '/demo'}
                  aria-label={locked ? `${tool.title} — requires Team plan` : `${tool.title} — explore in demo`}
                  className={`
                    group block h-full rounded-xl p-4 border-l-[3px] border
                    transition-all duration-200
                    ${isSolo
                      ? 'border-l-sage-500/50 border-obsidian-500/25 bg-obsidian-800/50 hover:border-obsidian-500/40 hover:bg-obsidian-800/70 hover:shadow-lg hover:shadow-obsidian-900/30 hover:-translate-y-0.5'
                      : 'border-l-oatmeal-400/35 border-obsidian-500/20 bg-obsidian-800/40 hover:border-obsidian-500/35 hover:bg-obsidian-800/60 hover:shadow-lg hover:shadow-obsidian-900/30 hover:-translate-y-0.5'
                    }
                    ${locked ? 'opacity-40' : ''}
                  `}
                >
                  {/* Icon + Tier badge */}
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div className={`
                      w-9 h-9 rounded-lg flex items-center justify-center shrink-0 transition-all duration-200
                      group-hover:scale-110 group-hover:rotate-3
                      ${isSolo
                        ? 'bg-sage-500/15 text-sage-400 group-hover:bg-sage-500/25'
                        : 'bg-oatmeal-400/10 text-oatmeal-400 group-hover:bg-oatmeal-400/18'
                      }
                    `}>
                      <BrandIcon name={tool.icon} className="w-4 h-4" />
                    </div>

                    <span className={`
                      shrink-0 px-1.5 py-0.5 rounded text-[9px] uppercase tracking-wider
                      font-sans font-semibold border
                      ${isSolo
                        ? 'bg-sage-500/10 text-sage-400 border-sage-500/25'
                        : 'bg-oatmeal-400/8 text-oatmeal-500 border-oatmeal-400/20'
                      }
                    `}>
                      {isSolo ? 'Solo' : 'Team'}
                    </span>
                  </div>

                  {/* Tool name */}
                  <h3 className="font-serif text-sm text-oatmeal-200 mb-1.5 leading-snug group-hover:text-oatmeal-100 transition-colors">
                    {tool.title}
                  </h3>

                  {/* Description */}
                  <p className="font-sans text-xs text-oatmeal-600 leading-relaxed line-clamp-2">
                    {tool.description}
                  </p>

                  {/* Footer: cluster + test count */}
                  <div className="flex items-center gap-1.5 mt-3 pt-2.5 border-t border-obsidian-600/25">
                    <span className="font-sans text-[9px] uppercase tracking-widest text-oatmeal-700">
                      {tool.cluster}
                    </span>
                    {tool.tests && (
                      <>
                        <span className="text-obsidian-600 text-[9px]">·</span>
                        <span style={{ fontVariantNumeric: 'tabular-nums lining-nums' }} className="font-mono text-[9px] text-oatmeal-700">{tool.tests} tests</span>
                      </>
                    )}
                  </div>
                </Link>
              </motion.div>
            )
          })}
        </motion.div>

        {/* ── Plan CTA Strip ──────────────────────────────────── */}
        <motion.div
          className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-3"
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          {/* Solo */}
          <Link
            href="/pricing"
            className="group flex items-center gap-4 p-5 rounded-xl border border-l-[3px] border-l-sage-500/50 transition-all duration-200 bg-sage-500/[0.06] border-obsidian-500/20 hover:bg-sage-500/10 hover:border-sage-500/30"
          >
            <div className="w-10 h-10 rounded-lg bg-sage-500/15 text-sage-400 flex items-center justify-center shrink-0 group-hover:bg-sage-500/25 transition-colors">
              <BrandIcon name="shield-check" className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2 mb-0.5">
                <span className="font-serif text-base text-oatmeal-100">Solo</span>
                <span className="type-num-sm text-sage-400">
                  $50<span className="font-sans text-xs text-oatmeal-600">/mo</span>
                </span>
              </div>
              <p className="font-sans text-xs text-oatmeal-500 truncate">
                {SOLO_COUNT} tools · 20 diagnostics/mo · PDF &amp; Excel export
              </p>
            </div>
            <div className="flex items-center gap-1 text-sage-500 group-hover:text-sage-400 shrink-0 transition-colors">
              <span className="font-sans text-xs whitespace-nowrap">Start 7-day trial</span>
              <BrandIcon name="chevron-right" className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </Link>

          {/* Team */}
          <Link
            href="/pricing"
            className="group flex items-center gap-4 p-5 rounded-xl border border-l-[3px] border-l-oatmeal-400/40 transition-all duration-200 bg-oatmeal-400/[0.04] border-obsidian-500/20 hover:bg-oatmeal-400/[0.07] hover:border-oatmeal-400/25"
          >
            <div className="w-10 h-10 rounded-lg bg-oatmeal-400/10 text-oatmeal-400 flex items-center justify-center shrink-0 group-hover:bg-oatmeal-400/16 transition-colors">
              <BrandIcon name="users" className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="font-serif text-base text-oatmeal-100">Team</span>
                <span className="type-num-sm text-oatmeal-300">
                  $130<span className="font-sans text-xs text-oatmeal-600">/mo</span>
                </span>
                <span className="px-1.5 py-0.5 rounded text-[9px] font-sans bg-oatmeal-400/15 text-oatmeal-400 border border-oatmeal-400/25">
                  Most popular
                </span>
              </div>
              <p className="font-sans text-xs text-oatmeal-500 truncate">
                All {TOTAL_COUNT} tools · Unlimited diagnostics · Workspace · 3 seats
              </p>
            </div>
            <div className="flex items-center gap-1 text-oatmeal-500 group-hover:text-oatmeal-400 shrink-0 transition-colors">
              <span className="font-sans text-xs whitespace-nowrap">Start 7-day trial</span>
              <BrandIcon name="chevron-right" className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </Link>
        </motion.div>

        {/* ── Pricing footnote ────────────────────────────────── */}
        <motion.p
          className="text-center mt-5 font-sans text-xs text-oatmeal-700"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={VIEWPORT.default}
          transition={{ delay: 0.35 }}
        >
          Also available:{' '}
          <Link href="/pricing" className="text-oatmeal-500 hover:text-oatmeal-300 transition-colors underline underline-offset-2">
            Organization ($400/mo)
          </Link>
          {' '}and{' '}
          <Link href="/pricing" className="text-oatmeal-500 hover:text-oatmeal-300 transition-colors underline underline-offset-2">
            Enterprise
          </Link>
          {' '}for full-firm deployments.
        </motion.p>

      </div>
    </section>
  )
}
