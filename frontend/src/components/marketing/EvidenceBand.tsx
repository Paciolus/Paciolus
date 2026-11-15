'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { BrandIcon, type BrandIconName } from '@/components/shared'
import { Reveal } from '@/components/ui/Reveal'
import { METHODOLOGY_SOURCES } from '@/content/methodology-sources'
import { TOTAL_AUTOMATED_TESTS } from '@/content/tool-ledger'
import { VIEWPORT } from '@/utils/marketingMotion'
import { staggerContainerTight, fadeUp } from '@/lib/motion'

/**
 * EvidenceBand
 *
 * Static credential strip on the homepage. Four cells surface the
 * platform's auditor-relevant differentiators: test depth, standards
 * coverage, a memo mock, and upload handling.
 */

interface EvidenceCell {
  icon: BrandIconName
  stat: string
  label: string
  sub: string
  accent: 'sage' | 'oatmeal'
  /** Sprint 861: every claim links to where the reader can check it. */
  check: { label: string; href: string }
}

/** Rules listed on the Sources page — derived, never typed. */
const METHODOLOGY_RULE_COUNT = METHODOLOGY_SOURCES.reduce((n, tool) => n + tool.rules.length, 0)

// Sprint 861 (CEO decision 2026-11-14): no standard names, no speed claim and
// no "None kept" absolute on marketing pages — each cell states a fact the
// reader can check.
const CELLS: EvidenceCell[] = [
  {
    icon: 'shield-check',
    stat: String(TOTAL_AUTOMATED_TESTS),
    label: 'Automated Tests',
    sub: 'Across the testing tools',
    accent: 'sage',
    check: { label: 'See every test', href: '/sources' },
  },
  {
    icon: 'document-duplicate',
    stat: String(METHODOLOGY_RULE_COUNT),
    label: 'Rules With Their Source',
    sub: 'Each rule names its source, or says the threshold is our own convention',
    accent: 'oatmeal',
    check: { label: 'Sources & Methodology', href: '/sources' },
  },
  {
    icon: 'padlock',
    stat: 'In memory',
    label: 'Uploaded Files',
    sub: 'Processed in memory and not kept after analysis',
    accent: 'sage',
    check: { label: 'See exactly what we keep', href: '/trust#transparency' },
  },
]

export function EvidenceBand() {
  return (
    <section className="relative py-16 px-6 overflow-hidden paper-grain">
      {/* Background texture — Sprint 703: swapped marble JPG at 7% for the
          canonical .paper-grain utility (256x256 seamless FFT noise, 5.6KB,
          3% opacity via mix-blend-mode multiply). One texture language
          across the site, and the decorative div below is no longer
          needed — .paper-grain handles the overlay via ::before. */}
      <div className="max-w-5xl mx-auto relative z-10">

        {/* Section Header */}
        <Reveal className="text-center mb-8">
          <div className="w-12 h-[2px] bg-sage-500 rounded-full mx-auto mb-4" />
          <span className="inline-block font-sans text-xs uppercase tracking-[0.2em] text-sage-400 mb-3">
            Platform Credentials
          </span>
          <h2 className="font-serif text-3xl md:text-4xl text-oatmeal-100 mb-3">
            Standards-Driven by Design
          </h2>
          <p className="font-sans text-oatmeal-400 text-sm max-w-xl mx-auto mb-4">
            Every test names the rule it applies, or says when a threshold is our own convention.
          </p>
          <div className="w-12 h-[2px] bg-sage-500 rounded-full mx-auto" />
        </Reveal>

        {/* 4-cell grid */}
        <Reveal>
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-3"
            variants={staggerContainerTight}
            initial="hidden"
            whileInView="visible"
            viewport={VIEWPORT.eager}
          >
            {CELLS.map((cell) => (
              <motion.div
                key={cell.label}
                variants={fadeUp}
              className={`
                p-5 rounded-xl border border-l-[3px] bg-obsidian-800/50
                ${cell.accent === 'sage'
                  ? 'border-l-sage-500/50 border-obsidian-500/20'
                  : 'border-l-oatmeal-400/35 border-obsidian-500/20'
                }
              `}
            >
              <div className={`
                w-9 h-9 rounded-lg flex items-center justify-center mb-4
                ${cell.accent === 'sage'
                  ? 'bg-sage-500/15 text-sage-400'
                  : 'bg-oatmeal-400/10 text-oatmeal-400'
                }
              `}>
                <BrandIcon name={cell.icon} className="w-4 h-4" />
              </div>

              <p className={`
                font-mono text-xl font-bold mb-1 tabular-nums
                ${cell.accent === 'sage' ? 'text-sage-300' : 'text-oatmeal-200'}
              `}>
                {cell.stat}
              </p>
              <p className="font-serif text-sm text-oatmeal-300 mb-1">{cell.label}</p>
              <p className="font-sans text-xs text-oatmeal-600 leading-snug">{cell.sub}</p>
              <Link href={cell.check.href} className="inline-block mt-2 font-sans text-xs text-sage-400 hover:text-sage-300 underline">
                {cell.check.label}
              </Link>
            </motion.div>
          ))}
          </motion.div>
        </Reveal>

        {/* CTA */}
        <Reveal delay={0.08} className="flex justify-center mt-6">
          <Link
            href="/demo"
            className="inline-flex items-center gap-2 font-sans text-sm text-oatmeal-400 hover:text-oatmeal-200 transition-colors group"
          >
            Explore all 18 tools in the interactive demo
            <BrandIcon name="chevron-right" className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </Reveal>

      </div>
    </section>
  )
}
