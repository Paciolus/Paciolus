'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { DemoTabExplorer } from '@/components/marketing/DemoTabExplorer'
import { BrandIcon, type BrandIconName } from '@/components/shared'
import { Reveal } from '@/components/ui/Reveal'
import { fadeUp } from '@/lib/motion'

/**
 * Platform Demo Page
 *
 * Marketing-grade interactive exploration hub. No account required.
 * Shows the 5-tab DemoTabExplorer, the full 18-tool grid (kept in step with
 * backend/tools_registry.py — see the doc-consistency guard), and a final
 * conversion CTA toward /register.
 *
 * Guardian requirement: persistent synthetic-data disclaimer (rendered
 * inside DemoTabExplorer and again in the page footer note).
 * ThemeProvider: /demo is in DARK_ROUTES — inherits obsidian lobby theme.
 */

type ToolTier = 'solo'

interface DemoTool {
  title: string
  description: string
  icon: BrandIconName
  tier: ToolTier
  cluster: string
  tests?: number
}

const DEMO_TOOLS: DemoTool[] = [
  { title: 'Trial Balance Diagnostics', description: 'Anomaly detection, ratio analysis, lead sheet mapping, and financial statement generation.', icon: 'calculator',         tier: 'solo', cluster: 'Analyze' },
  { title: 'Multi-Period Comparison',   description: 'Compare up to three periods side-by-side with variance analysis and budget tracking.',    icon: 'trend-chart',       tier: 'solo', cluster: 'Analyze' },
  { title: 'Journal Entry Testing',     description: "Benford's Law, structural validation, and statistical anomaly detection across the GL.",  icon: 'shield-check',      tier: 'solo', cluster: 'Detect',   tests: 19 },
  { title: 'Revenue Testing',           description: 'Revenue analytics plus contract-aware recognition timing and cut-off analysis.',     icon: 'currency-circle',   tier: 'solo', cluster: 'Detect',   tests: 18 },
  { title: 'AP Payment Testing',        description: 'Duplicate payments, vendor concentration, and patterns associated with fraud schemes across payables.',        icon: 'document-duplicate',tier: 'solo', cluster: 'Validate', tests: 14 },
  { title: 'Bank Reconciliation',       description: 'Match bank transactions against the general ledger and list the reconciling items.',       icon: 'arrows-vertical',   tier: 'solo', cluster: 'Validate' },
  { title: 'Statistical Sampling',      description: 'MUS and random sampling with Stringer bounds, for your sampling procedures.', icon: 'bar-chart',         tier: 'solo', cluster: 'Analyze' },
  { title: 'Payroll Testing',           description: 'Ghost-employee indicators, duplicate payments, and payroll anomaly analysis.',             icon: 'users',             tier: 'solo', cluster: 'Detect',   tests: 13 },
  { title: 'Three-Way Match',           description: 'PO-Invoice-Receipt matching with exact PO# linkage and procurement variance analysis.',   icon: 'circle-check',      tier: 'solo', cluster: 'Validate' },
  { title: 'AR Aging Analysis',         description: 'Receivables aging with concentration risk, stale balances, and allowance adequacy.',      icon: 'clock',             tier: 'solo', cluster: 'Assess',   tests: 12 },
  { title: 'Fixed Asset Testing',       description: 'PP&E depreciation, useful life and residual value anomaly detection.',        icon: 'building',          tier: 'solo', cluster: 'Assess',   tests: 11 },
  { title: 'Inventory Testing',         description: 'Unit cost outliers, slow-moving detection and valuation anomalies.',           icon: 'cube',              tier: 'solo', cluster: 'Assess',   tests: 10 },
  { title: 'Segregation of Duties',     description: 'User-role and role-permission matrices checked against an SoD rule library, ranked per user.', icon: 'padlock',        tier: 'solo', cluster: 'Validate' },
  { title: 'Intercompany Elimination',  description: 'Reciprocal balance matching across entities, proposed elimination entries, consolidation worksheet.', icon: 'arrows-vertical', tier: 'solo', cluster: 'Validate' },
  { title: 'W-2 / W-3 Reconciliation',  description: 'Payroll YTD reconciled to draft W-2s and Form 941 quarterlies before year-end filing.',   icon: 'clipboard-check',   tier: 'solo', cluster: 'Validate' },
  { title: '1099 Vendor Threshold Review',     description: '1099-NEC / MISC / INT threshold detection with corporate safe-harbour and processor exemptions.', icon: 'document',    tier: 'solo', cluster: 'Validate' },
  { title: 'Book-to-Tax Reconciliation',description: 'Book pretax income bridged to taxable income with Schedule M-1 / M-3 and a deferred-tax roll.', icon: 'spreadsheet', tier: 'solo', cluster: 'Analyze' },
  { title: 'Cash Flow Projector',       description: '90-day cash position across base, stress and best scenarios with liquidity-breach flagging.', icon: 'bar-chart',      tier: 'solo', cluster: 'Analyze' },
]

export default function DemoPage() {
  return (
    <main id="main-content" className="relative min-h-screen bg-obsidian-800 pt-20">

      {/* ── Page Hero ─────────────────────────────────────────── */}
      <section className="py-16 px-6">
        <motion.div
          initial="hidden"
          animate="visible"
          variants={fadeUp}
          className="max-w-5xl mx-auto"
        >
          <h1 className="font-serif text-4xl md:text-5xl text-oatmeal-100 mb-4">
            Sample Outputs From All 18 Tools
          </h1>
          <p className="font-sans text-oatmeal-400 text-base leading-relaxed max-w-2xl">
            Explore all eighteen audit diagnostic tools using synthetic data.
            Every test names the rule it applies, or says when a threshold is our own convention.
          </p>
          <p className="font-sans text-sm text-oatmeal-500 mt-3">
            Sample outputs on synthetic data. No account required.
          </p>
        </motion.div>
      </section>

      {/* ── Tab Explorer ──────────────────────────────────────── */}
      <section className="py-4 px-6">
        <div className="max-w-4xl mx-auto">
          <DemoTabExplorer />
        </div>
      </section>

      {/* ── All 18 Tools Grid (>8 items — single fadeUp, no stagger) ── */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">

          <Reveal className="text-center mb-10">
            <h2 className="font-serif text-3xl text-oatmeal-200 mb-2">
              The Complete Tool Suite
            </h2>
            <p className="font-sans text-oatmeal-500 text-sm">
              All eighteen tools included with every paid plan.
            </p>
          </Reveal>

          <Reveal>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {DEMO_TOOLS.map((tool) => {
                const isSolo = tool.tier === 'solo'
                return (
                  <div key={tool.title}>
                    <div className={`
                      h-full rounded-lg p-4 border-l-[3px] border
                      ${isSolo
                        ? 'border-l-sage-500/50 border-obsidian-500/25 bg-obsidian-800/50'
                        : 'border-l-oatmeal-400/35 border-obsidian-500/20 bg-obsidian-800/40'
                      }
                    `}>
                      {/* Icon + badge */}
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <div className={`
                          w-9 h-9 rounded-lg flex items-center justify-center shrink-0
                          ${isSolo ? 'bg-sage-500/15 text-sage-400' : 'bg-oatmeal-400/10 text-oatmeal-400'}
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

                      <h3 className="font-serif text-sm text-oatmeal-200 mb-1.5 leading-snug">
                        {tool.title}
                      </h3>
                      <p className="font-sans text-xs text-oatmeal-600 leading-relaxed line-clamp-2">
                        {tool.description}
                      </p>

                      <div className="flex items-center gap-1.5 mt-3 pt-2.5 border-t border-obsidian-600/25">
                        <span className="font-sans text-[9px] uppercase tracking-widest text-oatmeal-600">
                          {tool.cluster}
                        </span>
                        {tool.tests && (
                          <>
                            <span className="text-obsidian-600 text-[9px]">·</span>
                            <span className="font-mono text-[9px] text-oatmeal-600">{tool.tests} tests</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </Reveal>

        </div>
      </section>

      {/* ── Conversion CTA ────────────────────────────────────── */}
      <section className="py-20 px-6">
        <Reveal className="max-w-2xl mx-auto text-center">
          <h2 className="font-serif text-3xl text-oatmeal-100 mb-4">
            Run the Tools on Your Own Trial Balance
          </h2>
          <p className="font-sans text-oatmeal-400 mb-8 max-w-lg mx-auto">
            Start the 7-day trial and run the tools on your own trial balance. A card is required;
            you are not charged until the trial ends, and you can cancel before then.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/register"
              className="px-8 py-3.5 bg-sage-600 rounded-lg text-oatmeal-50 font-sans font-medium hover:bg-sage-500 transition-colors"
            >
              Start 7-Day Trial
            </Link>
            <Link
              href="/pricing"
              className="px-8 py-3.5 bg-transparent border border-oatmeal-400/30 rounded-lg text-oatmeal-300 font-sans font-medium hover:border-oatmeal-400/50 hover:bg-oatmeal-200/5 transition-all"
            >
              View Pricing
            </Link>
          </div>

          <p className="font-sans text-xs text-oatmeal-600 mt-6">
            All data shown on this page is synthetic. No client information is used or stored.
          </p>
        </Reveal>
      </section>

    </main>
  )
}
