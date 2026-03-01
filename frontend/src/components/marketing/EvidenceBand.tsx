'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { BrandIcon, type BrandIconName } from '@/components/shared'
import { STAGGER, ENTER, VIEWPORT } from '@/utils/marketingMotion'

/**
 * EvidenceBand — Sprint 448
 *
 * Static credential strip replacing ProductPreview on the homepage.
 * Four cells surface the platform's auditor-relevant differentiators
 * without requiring interaction: test depth, standards coverage,
 * a memo mock, and Zero-Storage architecture.
 *
 * CTA directs to /demo for visitors who want to explore further.
 */

interface EvidenceCell {
  icon: BrandIconName
  stat: string
  label: string
  sub: string
  accent: 'sage' | 'oatmeal'
}

const CELLS: EvidenceCell[] = [
  {
    icon: 'shield-check',
    stat: '140+',
    label: 'Automated Tests',
    sub: 'Across all 12 diagnostic tools',
    accent: 'sage',
  },
  {
    icon: 'document-duplicate',
    stat: 'ISA · PCAOB · ASC',
    label: 'Per-Memo Citations',
    sub: 'Every export cites the governing standard',
    accent: 'oatmeal',
  },
  {
    icon: 'padlock',
    stat: 'Zero',
    label: 'Lines Stored',
    sub: 'Client data never written to disk',
    accent: 'sage',
  },
  {
    icon: 'trend-chart',
    stat: '< 2s',
    label: 'Diagnostic Runtime',
    sub: 'Full TB analysis in under two seconds',
    accent: 'oatmeal',
  },
]

export function EvidenceBand() {
  return (
    <section className="py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">

        {/* Label */}
        <motion.div
          className="text-center mb-8"
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.4 }}
        >
          <span className="font-sans text-xs uppercase tracking-[0.2em] text-oatmeal-600">
            Platform Credentials
          </span>
        </motion.div>

        {/* 4-cell grid */}
        <motion.div
          className="grid grid-cols-2 lg:grid-cols-4 gap-3"
          variants={STAGGER.fast}
          initial="hidden"
          whileInView="visible"
          viewport={VIEWPORT.eager}
        >
          {CELLS.map((cell) => (
            <motion.div
              key={cell.label}
              variants={ENTER.fadeUp}
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
            </motion.div>
          ))}
        </motion.div>

        {/* Memo preview strip */}
        <motion.div
          className="mt-4 rounded-xl border border-obsidian-500/20 bg-obsidian-800/40 overflow-hidden"
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          {/* Mock memo header */}
          <div className="flex items-center gap-3 px-5 py-3 border-b border-obsidian-500/20 bg-obsidian-800/60">
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-clay-500/50" />
              <div className="w-2.5 h-2.5 rounded-full bg-oatmeal-400/30" />
              <div className="w-2.5 h-2.5 rounded-full bg-sage-500/40" />
            </div>
            <span className="font-mono text-[11px] text-oatmeal-600">
              Journal Entry Testing Memo — ISA 240 / PCAOB AS 2401
            </span>
            <div className="ml-auto flex items-center gap-2">
              <span className="font-sans text-[9px] uppercase tracking-widest text-sage-500/70 bg-sage-500/10 px-2 py-0.5 rounded border border-sage-500/20">
                PDF Export
              </span>
            </div>
          </div>

          {/* Mock memo content rows */}
          <div className="px-5 py-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <p className="font-sans text-[9px] uppercase tracking-widest text-oatmeal-700 mb-2">Test Battery</p>
              <div className="space-y-1.5">
                {[
                  { test: 'Benford\'s Law Analysis', status: 'pass' },
                  { test: 'Weekend / Holiday Posting', status: 'flag' },
                  { test: 'Round Number Concentration', status: 'pass' },
                  { test: 'Top-Strata Sampling (ISA 530)', status: 'pass' },
                ].map((row) => (
                  <div key={row.test} className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${row.status === 'pass' ? 'bg-sage-500' : 'bg-oatmeal-400'}`} />
                    <span className="font-sans text-[10px] text-oatmeal-500">{row.test}</span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <p className="font-sans text-[9px] uppercase tracking-widest text-oatmeal-700 mb-2">Standards Cited</p>
              <div className="space-y-1.5">
                {['ISA 240.A40 — Holiday postings', 'ISA 240.A32 — Benford deviation', 'PCAOB AS 2401.65 — Fraud risk', 'ISA 530 — Sample design'].map((s) => (
                  <div key={s} className="flex items-start gap-1.5">
                    <span className="font-sans text-[10px] text-oatmeal-600 leading-snug">{s}</span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <p className="font-sans text-[9px] uppercase tracking-widest text-oatmeal-700 mb-2">Summary</p>
              <div className="space-y-2">
                <div className="flex justify-between items-baseline">
                  <span className="font-sans text-[10px] text-oatmeal-600">Tests Passed</span>
                  <span className="font-mono text-xs text-sage-400">16 / 19</span>
                </div>
                <div className="flex justify-between items-baseline">
                  <span className="font-sans text-[10px] text-oatmeal-600">Flagged Items</span>
                  <span className="font-mono text-xs text-oatmeal-400">3</span>
                </div>
                <div className="flex justify-between items-baseline">
                  <span className="font-sans text-[10px] text-oatmeal-600">Risk Level</span>
                  <span className="font-mono text-xs text-oatmeal-300">Low</span>
                </div>
              </div>
              <p className="font-sans text-[9px] text-oatmeal-700 italic mt-3 leading-snug">
                Synthetic data — no client information stored
              </p>
            </div>
          </div>
        </motion.div>

        {/* CTA */}
        <motion.div
          className="flex justify-center mt-6"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={VIEWPORT.default}
          transition={{ delay: 0.35 }}
        >
          <Link
            href="/demo"
            className="inline-flex items-center gap-2 font-sans text-sm text-oatmeal-400 hover:text-oatmeal-200 transition-colors group"
          >
            Explore all 12 tools in the interactive demo
            <BrandIcon name="chevron-right" className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </motion.div>

      </div>
    </section>
  )
}
