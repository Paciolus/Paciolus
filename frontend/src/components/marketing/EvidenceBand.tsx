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
    <section className="py-16 px-6">
      <div className="max-w-5xl mx-auto">

        {/* Section Header */}
        <motion.div
          className="text-center mb-8"
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.4 }}
        >
          <div className="w-12 h-[2px] bg-sage-500 rounded-full mx-auto mb-4" />
          <span className="inline-block font-sans text-xs uppercase tracking-[0.2em] text-sage-400 mb-3">
            Platform Credentials
          </span>
          <h2 className="font-serif text-3xl md:text-4xl text-oatmeal-100 mb-3">
            Standards-Driven by Design
          </h2>
          <p className="font-sans text-oatmeal-400 text-sm max-w-xl mx-auto mb-4">
            Every test cites its standard. Every memo follows ISA/PCAOB format.
          </p>
          <div className="w-12 h-[2px] bg-sage-500 rounded-full mx-auto" />
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
