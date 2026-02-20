'use client'

import { motion } from 'framer-motion'
import { BrandIcon, type BrandIconName } from '@/components/shared'

/**
 * ProofStrip — Sprint 334
 *
 * Lightweight credibility band between hero and ToolShowcase.
 * Validates audience fit (industry badges) and key differentiators
 * (outcome metrics) before the product showcase begins.
 *
 * Transparent background — inherits gradient mesh atmosphere.
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
  { value: 'Under 3 seconds', label: 'Average analysis time', icon: 'clock' },
  { value: 'Zero data stored', label: 'Nothing persisted, ever', icon: 'padlock' },
  { value: 'ISA & PCAOB', label: 'Standards-aligned output', icon: 'shield-check' },
  { value: 'Built for auditors', label: '12 integrated diagnostic tools', icon: 'clipboard-check' },
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.06 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 200, damping: 20 } },
}

export function ProofStrip() {
  return (
    <section className="py-16 px-6">
      <div className="max-w-5xl mx-auto">
        {/* Section label */}
        <motion.p
          className="text-center font-sans text-xs uppercase tracking-widest text-oatmeal-600"
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          Trusted by Financial Professionals
        </motion.p>

        {/* Industry badge row */}
        <motion.div
          className="flex flex-wrap justify-center gap-3 mt-6"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {INDUSTRY_BADGES.map((badge) => (
            <motion.div
              key={badge.label}
              variants={itemVariants}
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-obsidian-800/40 border border-obsidian-500/20"
            >
              <BrandIcon name={badge.icon} className="w-4 h-4 text-oatmeal-400" />
              <span className="font-sans text-xs text-oatmeal-300">{badge.label}</span>
            </motion.div>
          ))}
        </motion.div>

        {/* Outcome metric cards */}
        <motion.div
          className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-10"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {OUTCOME_METRICS.map((metric) => (
            <motion.div
              key={metric.label}
              variants={itemVariants}
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
      </div>
    </section>
  )
}
