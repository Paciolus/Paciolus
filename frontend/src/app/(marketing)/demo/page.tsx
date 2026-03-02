'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { DemoTabExplorer } from '@/components/marketing/DemoTabExplorer'
import { BrandIcon, type BrandIconName } from '@/components/shared'
import { STAGGER, ENTER, VIEWPORT } from '@/utils/marketingMotion'

/**
 * Platform Demo Page
 *
 * Marketing-grade interactive exploration hub. No account required.
 * Shows the 5-tab DemoTabExplorer, all-12-tools grid, and a final
 * conversion CTA toward /register.
 *
 * Guardian requirement: persistent synthetic-data disclaimer (rendered
 * inside DemoTabExplorer and again in the page footer note).
 * ThemeProvider: /demo is in DARK_ROUTES — inherits obsidian lobby theme.
 */

type ToolTier = 'solo' | 'team'

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
  { title: 'Revenue Testing',           description: 'ISA 240 fraud risk plus ASC 606 / IFRS 15 recognition timing and cut-off analysis.',     icon: 'currency-circle',   tier: 'solo', cluster: 'Detect',   tests: 16 },
  { title: 'AP Payment Testing',        description: 'Duplicate detection, vendor concentration, and fraud indicators across payables.',        icon: 'document-duplicate',tier: 'solo', cluster: 'Validate', tests: 13 },
  { title: 'Bank Reconciliation',       description: 'Match bank transactions against the general ledger with automated reconciliation.',       icon: 'arrows-vertical',   tier: 'solo', cluster: 'Validate' },
  { title: 'Statistical Sampling',      description: 'ISA 530 / PCAOB AS 2315 compliant MUS and random sampling with Stringer bounds.',         icon: 'bar-chart',         tier: 'team', cluster: 'Analyze' },
  { title: 'Payroll Testing',           description: 'Ghost employee detection, duplicate payments, and payroll anomaly analysis.',             icon: 'users',             tier: 'team', cluster: 'Detect',   tests: 11 },
  { title: 'Three-Way Match',           description: 'PO-Invoice-Receipt matching with exact PO# linkage and procurement variance analysis.',   icon: 'circle-check',      tier: 'team', cluster: 'Validate' },
  { title: 'AR Aging Analysis',         description: 'Receivables aging with concentration risk, stale balances, and allowance adequacy.',      icon: 'clock',             tier: 'team', cluster: 'Assess',   tests: 11 },
  { title: 'Fixed Asset Testing',       description: 'PP&E depreciation, useful life, and residual value anomaly detection per IAS 16.',        icon: 'building',          tier: 'team', cluster: 'Assess',   tests: 9  },
  { title: 'Inventory Testing',         description: 'Unit cost outliers, slow-moving detection, and valuation anomalies per IAS 2.',           icon: 'cube',              tier: 'team', cluster: 'Assess',   tests: 9  },
]

export default function DemoPage() {
  return (
    <main className="relative min-h-screen bg-obsidian-800 pt-20">

      {/* ── Page Hero ─────────────────────────────────────────── */}
      <section className="py-16 px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-2xl mx-auto"
        >
          <div className="inline-flex items-center gap-2 bg-sage-500/10 border border-sage-500/20 rounded-full px-4 py-1.5 mb-6">
            <svg className="w-4 h-4 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <span className="text-sage-300 text-sm font-sans font-medium">Product Tour — Sample Outputs, No Account Required</span>
          </div>

          <h1 className="font-serif text-4xl md:text-5xl text-oatmeal-100 mb-4">
            See Paciolus in Action
          </h1>
          <p className="font-sans text-oatmeal-400 text-base leading-relaxed max-w-xl mx-auto">
            Explore all twelve audit diagnostic tools using synthetic data.
            Every output cites the governing accounting or auditing standard.
          </p>
        </motion.div>
      </section>

      {/* ── Tab Explorer ──────────────────────────────────────── */}
      <section className="py-4 px-6">
        <div className="max-w-4xl mx-auto">
          <DemoTabExplorer />
        </div>
      </section>

      {/* ── All 12 Tools Grid ─────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">

          <motion.div
            className="text-center mb-10"
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={VIEWPORT.default}
            transition={{ duration: 0.5 }}
          >
            <h2 className="font-serif text-3xl text-oatmeal-200 mb-2">
              The Complete Tool Suite
            </h2>
            <p className="font-sans text-oatmeal-500 text-sm">
              Seven tools included with Solo — all twelve with Team.
            </p>
          </motion.div>

          <motion.div
            className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3"
            variants={STAGGER.fast}
            initial="hidden"
            whileInView="visible"
            viewport={VIEWPORT.eager}
          >
            {DEMO_TOOLS.map((tool) => {
              const isSolo = tool.tier === 'solo'
              return (
                <motion.div key={tool.title} variants={ENTER.fadeUp}>
                  <div className={`
                    h-full rounded-xl p-4 border-l-[3px] border
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
                      <span className="font-sans text-[9px] uppercase tracking-widest text-oatmeal-700">
                        {tool.cluster}
                      </span>
                      {tool.tests && (
                        <>
                          <span className="text-obsidian-600 text-[9px]">·</span>
                          <span className="font-mono text-[9px] text-oatmeal-700">{tool.tests} tests</span>
                        </>
                      )}
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </motion.div>

        </div>
      </section>

      {/* ── Conversion CTA ────────────────────────────────────── */}
      <section className="py-20 px-6">
        <motion.div
          className="max-w-2xl mx-auto text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-serif text-3xl text-oatmeal-100 mb-4">
            Ready to Analyze Your Own Data?
          </h2>
          <p className="font-sans text-oatmeal-400 mb-8 max-w-lg mx-auto">
            Start your 7-day free trial. Upload a real trial balance and
            run the full diagnostic suite in under three seconds.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/register"
              className="px-8 py-3.5 bg-sage-600 rounded-xl text-white font-sans font-medium hover:bg-sage-500 transition-all shadow-lg shadow-sage-600/25 hover:shadow-xl hover:shadow-sage-600/30"
            >
              Start 7-Day Trial — Free
            </Link>
            <Link
              href="/pricing"
              className="px-8 py-3.5 bg-transparent border border-oatmeal-400/30 rounded-xl text-oatmeal-300 font-sans font-medium hover:border-oatmeal-400/50 hover:bg-oatmeal-200/5 transition-all"
            >
              View Pricing
            </Link>
          </div>

          <p className="font-sans text-xs text-oatmeal-700 mt-6">
            All data shown on this page is synthetic. No client information is used or stored.
          </p>
        </motion.div>
      </section>

    </main>
  )
}
