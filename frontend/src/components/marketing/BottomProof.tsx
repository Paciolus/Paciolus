'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { STAGGER, ENTER, VIEWPORT, CountUp } from '@/utils/marketingMotion'

/**
 * BottomProof — Sprint 334, motion migrated Sprint 337, revised Sprint 448
 *
 * Closing argument section: quantified platform credentials replacing
 * placeholder social proof. Auditor-relevant metrics (test depth,
 * standards coverage, Zero-Storage) with an auth-aware CTA.
 *
 * Placed after EvidenceBand, before footer.
 */

interface ClosingMetric {
  target: number
  suffix: string
  label: string
  sub: string
}

const CLOSING_METRICS: ClosingMetric[] = [
  {
    target: 140,
    suffix: '+',
    label: 'Automated Tests',
    sub: 'Across all 12 diagnostic tools',
  },
  {
    target: 12,
    suffix: '',
    label: 'Audit Tools',
    sub: 'TB · JE · AP · Revenue · Payroll + more',
  },
  {
    target: 7,
    suffix: '',
    label: 'Standards Referenced',
    sub: 'ISA · PCAOB · IFRS · ASC · IAS',
  },
]

const CREDENTIAL_BADGES = [
  'ISA 240 — Fraud Risk in Revenue',
  'ISA 530 — Audit Sampling',
  'PCAOB AS 2315 — Sampling',
  'ASC 606 / IFRS 15 — Revenue',
  'IAS 2 — Inventory',
  'IAS 16 — Fixed Assets',
  'ISA 501 — Cutoff Risk',
]

export function BottomProof() {
  const { isAuthenticated } = useAuth()
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-serif text-3xl md:text-4xl text-oatmeal-100">
            Every Test Cites Its Standard
          </h2>
          <p className="font-sans text-oatmeal-400 mt-3 max-w-xl mx-auto">
            Twelve audit-focused tools. Every result traceable to a published accounting or auditing standard.
          </p>
        </motion.div>

        {/* Standards badge strip */}
        <motion.div
          className="flex flex-wrap justify-center gap-2 mt-10"
          variants={STAGGER.fast}
          initial="hidden"
          whileInView="visible"
          viewport={VIEWPORT.eager}
        >
          {CREDENTIAL_BADGES.map((badge) => (
            <motion.span
              key={badge}
              variants={ENTER.fadeUp}
              className="px-3 py-1.5 rounded-full font-sans text-xs text-oatmeal-400 bg-obsidian-800/50 border border-obsidian-500/25"
            >
              {badge}
            </motion.span>
          ))}
        </motion.div>

        {/* Closing metric band */}
        <motion.div
          className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 mt-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          {CLOSING_METRICS.map((metric) => (
            <div
              key={metric.label}
              className="text-center bg-obsidian-800/40 border border-obsidian-500/20 rounded-xl p-5"
            >
              <p className="type-num-lg text-oatmeal-200">
                <CountUp target={metric.target} suffix={metric.suffix} />
              </p>
              <p className="font-sans text-sm text-oatmeal-300 mt-1 font-medium">{metric.label}</p>
              <p className="font-sans text-xs text-oatmeal-600 mt-0.5">{metric.sub}</p>
            </div>
          ))}
        </motion.div>

        {/* CTA row */}
        <motion.div
          className="flex items-center justify-center gap-4 mt-12"
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          {mounted && !isAuthenticated && (
            <Link
              href="/register"
              className="px-8 py-3.5 bg-sage-600 rounded-xl text-white font-sans font-medium hover:bg-sage-500 transition-all shadow-lg shadow-sage-600/25 hover:shadow-xl hover:shadow-sage-600/30"
            >
              Start Free Trial
            </Link>
          )}
          <Link
            href="/demo"
            className="px-8 py-3.5 bg-transparent border border-oatmeal-400/30 rounded-xl text-oatmeal-300 font-sans font-medium hover:border-oatmeal-400/50 hover:bg-oatmeal-200/5 transition-all"
          >
            Explore Demo
          </Link>
        </motion.div>
      </div>
    </section>
  )
}
