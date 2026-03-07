'use client'

import { motion } from 'framer-motion'
import { BrandIcon, type BrandIconName } from '@/components/shared'
import { Reveal } from '@/components/ui/Reveal'
import { VIEWPORT } from '@/utils/marketingMotion'
import { staggerContainerTight, fadeUp } from '@/lib/motion'
// Performance claim derived from ANALYSIS_LABEL_STANDARD in @/utils/constants
// Title-cased inline because it starts a sentence

/**
 * ProofStrip
 *
 * Lightweight credibility band between hero and ToolShowcase.
 * Validates audience fit (industry badges) and key differentiators
 * (outcome metrics) before the product showcase begins.
 */

interface IndustryBadge {
  label: string
  icon: BrandIconName
}

interface OutcomeMetric {
  value: string
  label: string
  icon: BrandIconName
}

const INDUSTRY_BADGES: IndustryBadge[] = [
  { label: 'CPA Firms', icon: 'calculator' },
  { label: 'Internal Audit', icon: 'shield-check' },
  { label: 'Corporate Finance', icon: 'currency-circle' },
  { label: 'Consulting', icon: 'bar-chart' },
  { label: 'Government', icon: 'building' },
  { label: 'Non-Profit', icon: 'users' },
]

const OUTCOME_METRICS: OutcomeMetric[] = [
  { value: 'Typically under three seconds', label: 'For standard file sizes', icon: 'clock' },
  { value: 'Zero file storage', label: 'Raw files destroyed on completion', icon: 'padlock' },
  { value: 'ISA & PCAOB', label: 'Standards-aligned output', icon: 'shield-check' },
  { value: '140+ automated tests', label: 'Across all 12 tools', icon: 'clipboard-check' },
]

export function ProofStrip() {
  return (
    <section className="py-16 px-6">
      <div className="max-w-5xl mx-auto">
        {/* Section label */}
        <Reveal>
          <p className="text-center font-sans text-xs uppercase tracking-widest text-oatmeal-600">
            Used across the profession
          </p>
        </Reveal>

        {/* Industry badge row */}
        <Reveal delay={0.06}>
          <motion.div
            className="flex flex-wrap justify-center gap-3 mt-6"
            variants={staggerContainerTight}
            initial="hidden"
            whileInView="visible"
            viewport={VIEWPORT.eager}
          >
            {INDUSTRY_BADGES.map((badge) => (
              <motion.div
                key={badge.label}
                variants={fadeUp}
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-obsidian-800/40 border border-obsidian-500/20"
            >
              <BrandIcon name={badge.icon} className="w-4 h-4 text-oatmeal-400" />
              <span className="font-sans text-xs text-oatmeal-300">{badge.label}</span>
            </motion.div>
          ))}
          </motion.div>
        </Reveal>

        {/* Outcome metric cards */}
        <Reveal delay={0.12}>
          <motion.div
            className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-10"
            variants={staggerContainerTight}
            initial="hidden"
            whileInView="visible"
            viewport={VIEWPORT.default}
          >
            {OUTCOME_METRICS.map((metric) => (
              <motion.div
                key={metric.label}
                variants={fadeUp}
              className="flex items-center gap-3 bg-obsidian-800/30 border border-obsidian-500/15 rounded-xl p-4"
            >
              <div className="shrink-0 w-9 h-9 rounded-lg bg-sage-500/10 flex items-center justify-center">
                <BrandIcon name={metric.icon} className="w-4 h-4 text-sage-400" />
              </div>
              <div className="min-w-0">
                <p className="font-sans text-sm font-semibold text-oatmeal-200">{metric.value}</p>
                <p className="font-sans text-xs text-oatmeal-500 leading-snug">{metric.label}</p>
              </div>
            </motion.div>
          ))}
          </motion.div>
        </Reveal>
      </div>
    </section>
  )
}
