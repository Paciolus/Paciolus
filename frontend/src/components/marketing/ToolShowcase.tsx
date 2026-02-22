'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { BrandIcon, type BrandIconName } from '@/components/shared'
import { STAGGER, ENTER, VIEWPORT, CountUp } from '@/utils/marketingMotion'

/**
 * ToolShowcase — Sprint 333, motion migrated Sprint 337
 *
 * Outcome-clustered accordion with progressive disclosure.
 * 4 clusters (Analyze, Detect, Validate, Assess) in a 2x2 grid,
 * expanding to reveal 3 tool cards per cluster.
 */

interface ToolCard {
  title: string
  description: string
  href: string
  icon: BrandIconName
  featured?: boolean
}

interface OutcomeCluster {
  id: string
  label: string
  description: string
  accentBorder: string
  accentBorderActive: string
  accentIconBg: string
  accentText: string
  icon: BrandIconName
  tools: ToolCard[]
}

const OUTCOME_CLUSTERS: OutcomeCluster[] = [
  {
    id: 'analyze',
    label: 'Analyze',
    description: 'Understand the data landscape',
    accentBorder: 'border-l-sage-500/30',
    accentBorderActive: 'border-l-sage-500/60',
    accentIconBg: 'bg-sage-500/15',
    accentText: 'text-sage-400',
    icon: 'bar-chart',
    tools: [
      {
        title: 'Trial Balance Diagnostics',
        description: 'Instant anomaly detection, ratio analysis, lead sheet mapping, and financial statement generation.',
        href: '/tools/trial-balance',
        featured: true,
        icon: 'calculator',
      },
      {
        title: 'Multi-Period Comparison',
        description: 'Compare up to three periods side-by-side with variance analysis and budget tracking.',
        href: '/tools/multi-period',
        icon: 'trend-chart',
      },
      {
        title: 'Statistical Sampling',
        description: 'ISA 530 / PCAOB AS 2315 compliant MUS and random sampling with Stringer evaluation.',
        href: '/tools/statistical-sampling',
        icon: 'bar-chart',
      },
    ],
  },
  {
    id: 'detect',
    label: 'Detect',
    description: 'Surface anomalies & fraud indicators',
    accentBorder: 'border-l-clay-500/30',
    accentBorderActive: 'border-l-clay-500/60',
    accentIconBg: 'bg-clay-500/15',
    accentText: 'text-clay-400',
    icon: 'warning-triangle',
    tools: [
      {
        title: 'Journal Entry Testing',
        description: "Benford's Law, structural validation, and statistical anomaly detection across the GL.",
        href: '/tools/journal-entry-testing',
        icon: 'shield-check',
      },
      {
        title: 'Revenue Testing',
        description: 'ISA 240 revenue recognition analysis with 12 structural and statistical tests.',
        href: '/tools/revenue-testing',
        icon: 'currency-circle',
      },
      {
        title: 'Payroll Testing',
        description: 'Ghost employee detection, duplicate payments, and payroll anomaly analysis.',
        href: '/tools/payroll-testing',
        icon: 'users',
      },
    ],
  },
  {
    id: 'validate',
    label: 'Validate',
    description: 'Verify transactions & balances',
    accentBorder: 'border-l-oatmeal-400/30',
    accentBorderActive: 'border-l-oatmeal-400/60',
    accentIconBg: 'bg-oatmeal-400/15',
    accentText: 'text-oatmeal-300',
    icon: 'circle-check',
    tools: [
      {
        title: 'AP Payment Testing',
        description: 'Duplicate detection, vendor analysis, and fraud indicators across accounts payable.',
        href: '/tools/ap-testing',
        icon: 'document-duplicate',
      },
      {
        title: 'Three-Way Match',
        description: 'PO-Invoice-Receipt matching to validate AP completeness and procurement variances.',
        href: '/tools/three-way-match',
        icon: 'circle-check',
      },
      {
        title: 'Bank Reconciliation',
        description: 'Match bank transactions against the general ledger with automated reconciliation.',
        href: '/tools/bank-rec',
        icon: 'arrows-vertical',
      },
    ],
  },
  {
    id: 'assess',
    label: 'Assess',
    description: 'Evaluate asset integrity',
    accentBorder: 'border-l-sage-300/30',
    accentBorderActive: 'border-l-sage-300/60',
    accentIconBg: 'bg-sage-300/15',
    accentText: 'text-sage-300',
    icon: 'clipboard-check',
    tools: [
      {
        title: 'AR Aging Analysis',
        description: 'Receivables aging with concentration risk, stale balances, and allowance adequacy.',
        href: '/tools/ar-aging',
        icon: 'clock',
      },
      {
        title: 'Fixed Asset Testing',
        description: 'PP&E depreciation, useful life, and residual value anomaly detection per IAS 16.',
        href: '/tools/fixed-assets',
        icon: 'building',
      },
      {
        title: 'Inventory Testing',
        description: 'Unit cost outliers, slow-moving detection, and valuation anomalies per IAS 2.',
        href: '/tools/inventory-testing',
        icon: 'cube',
      },
    ],
  },
]

export function ToolShowcase() {
  const [activeCluster, setActiveCluster] = useState<string | null>(null)
  const toggleCluster = (id: string) => setActiveCluster(prev => prev === id ? null : id)

  const activeTools = activeCluster
    ? OUTCOME_CLUSTERS.find(c => c.id === activeCluster)?.tools ?? []
    : []

  return (
    <section id="tools" className="relative z-10 py-24 px-6">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-serif text-3xl md:text-4xl text-oatmeal-200 mb-3">Twelve Tools. One Workspace.</h2>
          <p className="font-sans text-oatmeal-500 text-sm max-w-lg mx-auto">
            Four outcomes. Twelve tools. Use independently or tie together in a Diagnostic Workspace.
          </p>
        </motion.div>

        {/* Outcome Cluster Grid */}
        <motion.div
          variants={STAGGER.fast}
          initial="hidden"
          whileInView="visible"
          viewport={VIEWPORT.eager}
          className="grid grid-cols-1 md:grid-cols-2 gap-3"
        >
          {OUTCOME_CLUSTERS.map((cluster) => {
            const isActive = activeCluster === cluster.id
            return (
              <motion.div key={cluster.id} variants={ENTER.fadeUp}>
                <button
                  id={`cluster-${cluster.id}`}
                  aria-expanded={isActive}
                  aria-controls={`panel-${cluster.id}`}
                  onClick={() => toggleCluster(cluster.id)}
                  className={`w-full text-left rounded-xl p-4 border-l-4 border border-obsidian-500/30 transition-all duration-200 cursor-pointer ${
                    isActive
                      ? `${cluster.accentBorderActive} bg-obsidian-800/70`
                      : `${cluster.accentBorder} bg-obsidian-800/50 hover:bg-obsidian-800/70`
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${cluster.accentIconBg} ${cluster.accentText}`}>
                      <BrandIcon name={cluster.icon} className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-serif text-base text-oatmeal-200">{cluster.label}</h3>
                      <p className="font-sans text-xs text-oatmeal-500 truncate">{cluster.description}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="type-num-xs text-oatmeal-600">{cluster.tools.length}</span>
                      <motion.div
                        animate={{ rotate: isActive ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <BrandIcon name="chevron-down" className="w-4 h-4 text-oatmeal-500" />
                      </motion.div>
                    </div>
                  </div>
                </button>
              </motion.div>
            )
          })}
        </motion.div>

        {/* Expanded Tool Panel */}
        <AnimatePresence mode="wait">
          {activeCluster !== null && (
            <motion.div
              key={activeCluster}
              id={`panel-${activeCluster}`}
              role="region"
              aria-labelledby={`cluster-${activeCluster}`}
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25, ease: 'easeInOut' as const }}
              className="overflow-hidden"
            >
              <motion.div
                className="pt-6 grid grid-cols-1 md:grid-cols-3 gap-4"
                variants={STAGGER.fast}
                initial="hidden"
                animate="visible"
              >
                {activeTools.map((tool) => (
                  <motion.div key={tool.href} variants={ENTER.fadeUp}>
                    <Link
                      href={tool.href}
                      className={`group block h-full rounded-xl p-5 border transition-all duration-200 ${
                        tool.featured
                          ? 'bg-obsidian-800/70 border-sage-500/30 hover:border-sage-500/50 hover:shadow-lg hover:shadow-sage-500/5'
                          : 'bg-obsidian-800/50 border-obsidian-500/30 hover:border-oatmeal-500/30 hover:bg-obsidian-800/70'
                      }`}
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors ${
                          tool.featured
                            ? 'bg-sage-500/15 text-sage-400 group-hover:bg-sage-500/25'
                            : 'bg-obsidian-700/70 text-oatmeal-400 group-hover:text-sage-400'
                        }`}>
                          <BrandIcon name={tool.icon} />
                        </div>
                        {tool.featured && (
                          <span className="px-2 py-0.5 rounded-full text-[9px] font-sans font-medium bg-sage-500/20 text-sage-300 border border-sage-500/30">
                            Headliner
                          </span>
                        )}
                      </div>
                      <h4 className="font-serif text-sm font-medium text-oatmeal-200 mb-1.5 group-hover:text-oatmeal-100 transition-colors">
                        {tool.title}
                      </h4>
                      <p className="font-sans text-xs text-oatmeal-500 leading-relaxed line-clamp-2">
                        {tool.description}
                      </p>
                    </Link>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Diagnostic Workspace CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ delay: 0.2 }}
          className="mt-10"
        >
          <Link
            href="/engagements"
            className="block bg-obsidian-800/70 border border-sage-500/30 rounded-2xl p-8 hover:border-sage-500/50 hover:bg-obsidian-800/80 transition-all duration-200 group"
          >
            <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
              <div className="w-14 h-14 rounded-xl bg-sage-500/20 flex items-center justify-center text-sage-400 group-hover:bg-sage-500/30 transition-colors shrink-0">
                <BrandIcon name="archive" className="w-8 h-8" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="font-serif text-xl text-oatmeal-200 group-hover:text-oatmeal-100 transition-colors">
                    Diagnostic Workspace
                  </h3>
                </div>
                <p className="font-sans text-sm text-oatmeal-500 leading-relaxed max-w-2xl">
                  Tie all twelve tools together. Set materiality, track follow-up items, generate workpaper indices, and export diagnostic packages.
                </p>
              </div>
              <div className="flex items-center gap-1.5 text-sage-500 group-hover:text-sage-400 transition-colors shrink-0">
                <span className="font-sans text-sm">Open Workspace</span>
                <BrandIcon name="chevron-right" className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Link>
        </motion.div>

        {/* Social Proof / Metrics */}
        <motion.div
          className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.5 }}
        >
          {[
            { value: 12, suffix: '', label: 'Integrated Tools', detail: 'Diagnostic + Testing' },
            { value: 140, suffix: '+', label: 'Automated Tests', detail: 'Across all tools' },
            { value: 11, suffix: '', label: 'PDF Memos', detail: 'Workpaper-ready' },
            { value: 8, suffix: '', label: 'ISA/PCAOB Standards', detail: 'Full compliance' },
          ].map((metric) => (
            <div key={metric.label} className="text-center p-4 rounded-xl bg-obsidian-800/40 border border-obsidian-500/20">
              <p className="font-mono text-2xl md:text-3xl font-bold text-oatmeal-200 mb-1">
                <CountUp target={metric.value} suffix={metric.suffix} />
              </p>
              <p className="font-sans text-sm text-oatmeal-300 font-medium">{metric.label}</p>
              <p className="font-sans text-xs text-oatmeal-600 mt-0.5">{metric.detail}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
