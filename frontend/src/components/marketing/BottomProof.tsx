'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { EngravedStat } from '@/components/marketing/EngravedStat'
import { StandardsSpecimen } from '@/components/marketing/StandardsSpecimen'
import { Reveal } from '@/components/ui/Reveal'
import { TOTAL_AUTOMATED_TESTS } from '@/content/tool-ledger'
import { VIEWPORT } from '@/utils/marketingMotion'
import { fadeUp } from '@/lib/motion'

/**
 * BottomProof — Sprint 334, motion migrated Sprint 337, revised Sprint 448
 *
 * Closing argument section: quantified platform credentials replacing
 * placeholder social proof. Auditor-relevant metrics (test depth,
 * standards coverage, upload handling) with an auth-aware CTA.
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
    target: TOTAL_AUTOMATED_TESTS,
    suffix: '',
    label: 'Automated Tests',
    sub: 'Across the testing tools',
  },
  {
    target: 18,
    suffix: '',
    label: 'Audit Tools',
    sub: 'TB · JE · AP · Revenue · Payroll + more',
  },
  {
    // Sprint 843: was "7 Standards Referenced" — the registry holds 80+ citations.
    // Counted by standard-setter instead; pinned by test_pricing_copy_consistency.py.
    target: 6,
    suffix: '',
    label: 'Standard-Setters Cited',
    sub: 'IAASB · PCAOB · AICPA · FASB · IASB · IRS',
  },
]

export function BottomProof() {
  const { isAuthenticated } = useAuthSession()
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  return (
    <section className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <Reveal className="text-center">
          <div className="w-12 h-[2px] bg-sage-500 rounded-full mx-auto mb-4" />
          <span className="inline-block font-sans text-xs uppercase tracking-[0.2em] text-sage-400 mb-3">
            Professional Standards
          </span>
          <h2 className="font-serif text-3xl md:text-4xl text-oatmeal-100">
            Every Test Names Its Rule
          </h2>
          <p className="font-sans text-oatmeal-400 mt-3 max-w-xl mx-auto mb-4">
            Eighteen tools. Every test names the rule it applies, or says when a threshold is our own convention.
          </p>
          <div className="w-12 h-[2px] bg-sage-500 rounded-full mx-auto" />
        </Reveal>

        {/* Sprint 705 — Standards specimen replaces the pill strip.
            The specimen layout is the single differentiating design
            moment on the homepage; the pill strip is retained as a
            mobile-only fallback inside <StandardsSpecimen>. */}
        <Reveal>
          <StandardsSpecimen />
        </Reveal>

        {/* Sprint 704 — closing metric band rendered as engraved
            monuments (oversized display serif numerals + Roman-numeral
            kicker + hairline underline + small-caps label). Replaces the
            pre-Sprint-704 obsidian-tile stat-cards. CountUp retired —
            the editorial reading mode values a stable number more than
            an animated one. */}
        <Reveal delay={0.08} className="grid grid-cols-1 sm:grid-cols-3 gap-8 sm:gap-6 mt-16">
          {CLOSING_METRICS.map((metric, i) => (
            <EngravedStat
              key={metric.label}
              kicker={['I.', 'II.', 'III.'][i]}
              value={`${metric.target.toLocaleString()}${metric.suffix}`}
              label={metric.label}
              sub={metric.sub}
            />
          ))}
        </Reveal>

        {/* CTA row */}
        <Reveal delay={0.16} className="flex items-center justify-center gap-4 mt-12">
          {mounted && !isAuthenticated && (
            <Link
              href="/register"
              className="px-8 py-3.5 bg-sage-600 rounded-xl text-oatmeal-50 font-sans font-medium hover:bg-sage-500 transition-all shadow-lg shadow-sage-600/25 hover:shadow-xl hover:shadow-sage-600/30"
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
        </Reveal>
      </div>
    </section>
  )
}
