'use client'

import { useRef, useState, useEffect } from 'react'
import Link from 'next/link'
import { motion, useInView, AnimatePresence } from 'framer-motion'

/**
 * ToolShowcase — Sprint 332
 *
 * Outcome-clustered accordion with progressive disclosure.
 * 4 clusters (Analyze, Detect, Validate, Assess) in a 2x2 grid,
 * expanding to reveal 3 tool cards per cluster.
 */

interface ToolCard {
  title: string
  description: string
  href: string
  icon: React.ReactNode
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
  icon: React.ReactNode
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
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    tools: [
      {
        title: 'Trial Balance Diagnostics',
        description: 'Instant anomaly detection, ratio analysis, lead sheet mapping, and financial statement generation.',
        href: '/tools/trial-balance',
        featured: true,
        icon: (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        ),
      },
      {
        title: 'Multi-Period Comparison',
        description: 'Compare up to three periods side-by-side with variance analysis and budget tracking.',
        href: '/tools/multi-period',
        icon: (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
          </svg>
        ),
      },
      {
        title: 'Statistical Sampling',
        description: 'ISA 530 / PCAOB AS 2315 compliant MUS and random sampling with Stringer evaluation.',
        href: '/tools/statistical-sampling',
        icon: (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        ),
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
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    tools: [
      {
        title: 'Journal Entry Testing',
        description: "Benford's Law, structural validation, and statistical anomaly detection across the GL.",
        href: '/tools/journal-entry-testing',
        icon: (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        ),
      },
      {
        title: 'Revenue Testing',
        description: 'ISA 240 revenue recognition analysis with 12 structural and statistical tests.',
        href: '/tools/revenue-testing',
        icon: (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      },
      {
        title: 'Payroll Testing',
        description: 'Ghost employee detection, duplicate payments, and payroll anomaly analysis.',
        href: '/tools/payroll-testing',
        icon: (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        ),
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
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    tools: [
      {
        title: 'AP Payment Testing',
        description: 'Duplicate detection, vendor analysis, and fraud indicators across accounts payable.',
        href: '/tools/ap-testing',
        icon: (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
          </svg>
        ),
      },
      {
        title: 'Three-Way Match',
        description: 'PO-Invoice-Receipt matching to validate AP completeness and procurement variances.',
        href: '/tools/three-way-match',
        icon: (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      },
      {
        title: 'Bank Reconciliation',
        description: 'Match bank transactions against the general ledger with automated reconciliation.',
        href: '/tools/bank-rec',
        icon: (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
          </svg>
        ),
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
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
      </svg>
    ),
    tools: [
      {
        title: 'AR Aging Analysis',
        description: 'Receivables aging with concentration risk, stale balances, and allowance adequacy.',
        href: '/tools/ar-aging',
        icon: (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      },
      {
        title: 'Fixed Asset Testing',
        description: 'PP&E depreciation, useful life, and residual value anomaly detection per IAS 16.',
        href: '/tools/fixed-assets',
        icon: (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        ),
      },
      {
        title: 'Inventory Testing',
        description: 'Unit cost outliers, slow-moving detection, and valuation anomalies per IAS 2.',
        href: '/tools/inventory-testing',
        icon: (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
        ),
      },
    ],
  },
]

/** Count-up animation for social proof */
function CountUp({ target, suffix = '' }: { target: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null)
  const isVisible = useInView(ref, { once: true })
  const [count, setCount] = useState(0)

  useEffect(() => {
    if (!isVisible) return

    let frame = 0
    const totalFrames = 40
    const interval = setInterval(() => {
      frame++
      setCount(Math.round((frame / totalFrames) * target))
      if (frame >= totalFrames) {
        clearInterval(interval)
        setCount(target)
      }
    }, 30)

    return () => clearInterval(interval)
  }, [isVisible, target])

  return <span ref={ref}>{count.toLocaleString()}{suffix}</span>
}

const cardVariants = {
  hidden: { opacity: 0, y: 15 },
  visible: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 200, damping: 20 } },
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.06 } },
}

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
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-serif text-3xl md:text-4xl text-oatmeal-200 mb-3">Twelve Tools. One Workspace.</h2>
          <p className="font-sans text-oatmeal-500 text-sm max-w-lg mx-auto">
            Four outcomes. Twelve tools. Use independently or tie together in a Diagnostic Workspace.
          </p>
        </motion.div>

        {/* Outcome Cluster Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-50px' }}
          className="grid grid-cols-1 md:grid-cols-2 gap-3"
        >
          {OUTCOME_CLUSTERS.map((cluster) => {
            const isActive = activeCluster === cluster.id
            return (
              <motion.div key={cluster.id} variants={cardVariants}>
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
                      {cluster.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-serif text-base text-oatmeal-200">{cluster.label}</h3>
                      <p className="font-sans text-xs text-oatmeal-500 truncate">{cluster.description}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="font-mono text-xs text-oatmeal-600">{cluster.tools.length}</span>
                      <motion.svg
                        animate={{ rotate: isActive ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                        className="w-4 h-4 text-oatmeal-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </motion.svg>
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
                variants={containerVariants}
                initial="hidden"
                animate="visible"
              >
                {activeTools.map((tool) => (
                  <motion.div key={tool.href} variants={cardVariants}>
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
                          {tool.icon}
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
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="mt-10"
        >
          <Link
            href="/engagements"
            className="block bg-obsidian-800/70 border border-sage-500/30 rounded-2xl p-8 hover:border-sage-500/50 hover:bg-obsidian-800/80 transition-all duration-200 group"
          >
            <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
              <div className="w-14 h-14 rounded-xl bg-sage-500/20 flex items-center justify-center text-sage-400 group-hover:bg-sage-500/30 transition-colors shrink-0">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
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
                <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>
          </Link>
        </motion.div>

        {/* Social Proof / Metrics */}
        <motion.div
          className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
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
