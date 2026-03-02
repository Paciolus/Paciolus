'use client'

import { motion } from 'framer-motion'
import { BrandIcon, type BrandIconName } from '@/components/shared'
import { CHART_SHADOWS } from '@/utils/chartTheme'
import { STAGGER, ENTER, HOVER, VIEWPORT } from '@/utils/marketingMotion'

/**
 * FeaturePillars - Marketing Component
 *
 * Showcases three key value propositions for Paciolus:
 * 1. Zero-Storage Security
 * 2. Precision at Every Threshold
 * 3. Professional-Grade Exports
 *
 * Design: "Fintech Authority" aesthetic with Oat & Obsidian palette.
 * Cards feature subtle sage accents on icons and hover states.
 *
 * Animations:
 * - Staggered entrance via STAGGER.fast
 * - Dramatic card entrance via ENTER.fadeUpDramatic
 * - Icon pulse on hover via HOVER.iconPulse
 * - Clip-path reveal on gradient overlay via ENTER.clipReveal
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */

interface FeaturePillar {
  id: string
  title: string
  tagline: string
  description: string
  icon: BrandIconName
  accentGradient: string
  accentBorder: string
  accentIconBg: string
  accentIconBorder: string
  accentText: string
}

const pillars: FeaturePillar[] = [
  {
    id: 'zero-knowledge',
    title: 'Zero-Storage Security',
    tagline: 'Never written to disk. Never retained.',
    description:
      'Every file is processed in-memory and immediately discarded after analysis. Nothing is written to disk. Nothing is retained. Zero exposure, by design — not by policy.',
    accentGradient: 'from-sage-500/15 via-transparent to-transparent',
    accentBorder: 'border-sage-500/30 hover:border-sage-500/50',
    accentIconBg: 'bg-sage-500/20',
    accentIconBorder: 'border-sage-500/30 group-hover:border-sage-500/50',
    accentText: 'text-sage-400',
    icon: 'padlock',
  },
  {
    id: 'automated-sensitivity',
    title: 'Precision at Every Threshold',
    tagline: 'Set once. Applied everywhere.',
    description:
      'Configure materiality to your engagement. Every flag, every ratio, every anomaly is weighted against your criteria — not generic defaults. What matters surfaces. What doesn\'t, stays out of the way.',
    accentGradient: 'from-oatmeal-400/10 via-transparent to-transparent',
    accentBorder: 'border-oatmeal-400/30 hover:border-oatmeal-400/50',
    accentIconBg: 'bg-oatmeal-400/15',
    accentIconBorder: 'border-oatmeal-400/30 group-hover:border-oatmeal-400/50',
    accentText: 'text-oatmeal-300',
    icon: 'sliders',
  },
  {
    id: 'professional-exports',
    title: 'Professional-Grade Exports',
    tagline: 'Done before you close the tab.',
    description:
      'PDF memos with ISA and PCAOB citations. Excel workpapers with full underlying data. CSV exports for downstream analysis. Formatted and ready to file the moment analysis completes.',
    accentGradient: 'from-clay-500/8 via-transparent to-transparent',
    accentBorder: 'border-clay-500/20 hover:border-clay-500/40',
    accentIconBg: 'bg-clay-500/15',
    accentIconBorder: 'border-clay-500/25 group-hover:border-clay-500/40',
    accentText: 'text-clay-400',
    icon: 'document',
  },
]

// Card hover: keep inline because it uses CHART_SHADOWS import
const cardHoverVariants = {
  rest: {
    y: 0,
    boxShadow: `0 4px 6px -1px ${CHART_SHADOWS.darkShadow(0.1)}, 0 2px 4px -1px ${CHART_SHADOWS.darkShadow(0.06)}`,
  },
  hover: {
    y: -6,
    boxShadow: `0 20px 25px -5px ${CHART_SHADOWS.darkShadow(0.2)}, 0 10px 10px -5px ${CHART_SHADOWS.darkShadow(0.1)}`,
    transition: {
      type: 'spring' as const,
      stiffness: 300,
      damping: 20,
    },
  },
}

export function FeaturePillars() {
  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8">
      {/* Section Header */}
      <motion.div
        className="max-w-3xl mx-auto text-center mb-12"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={VIEWPORT.default}
        transition={{ duration: 0.5 }}
      >
        <div className="w-12 h-[2px] bg-sage-500 rounded-full mx-auto mb-4" />
        <span className="inline-block font-sans text-xs uppercase tracking-[0.2em] text-sage-400 mb-3">
          Why Paciolus
        </span>
        <h2 className="font-serif text-3xl sm:text-4xl font-bold text-oatmeal-100 mb-4">
          Built for Financial Professionals
        </h2>
        <p className="font-sans text-lg text-oatmeal-400 max-w-2xl mx-auto mb-4">
          What used to take days now takes seconds. Your client&apos;s data is never stored — the architecture makes it impossible. Every output is report-ready the moment analysis completes.
        </p>
        <div className="w-12 h-[2px] bg-sage-500 rounded-full mx-auto" />
      </motion.div>

      {/* Pillars Grid */}
      <motion.div
        variants={STAGGER.fast}
        initial="hidden"
        whileInView="visible"
        viewport={VIEWPORT.eager}
        className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8"
      >
        {pillars.map((pillar) => (
          <motion.div
            key={pillar.id}
            variants={ENTER.fadeUpDramatic}
            whileHover="hover"
            initial="rest"
            animate="rest"
            className="relative group"
          >
            <motion.div
              variants={cardHoverVariants}
              className={`relative h-full bg-obsidian-800 rounded-2xl border ${pillar.accentBorder} overflow-hidden transition-colors`}
            >
              {/* Per-pillar gradient overlay — clip-path reveal */}
              <motion.div
                variants={ENTER.clipReveal}
                initial="hidden"
                whileInView="visible"
                viewport={VIEWPORT.default}
                className={`absolute inset-0 bg-gradient-to-br ${pillar.accentGradient} pointer-events-none`}
              />

              {/* Top accent line */}
              <div className={`absolute top-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-current to-transparent ${pillar.accentText} opacity-30`} />

              <div className="relative p-6 lg:p-8">
                {/* Icon Container */}
                <motion.div
                  variants={HOVER.iconPulse}
                  className={`w-14 h-14 rounded-xl ${pillar.accentIconBg} border ${pillar.accentIconBorder} flex items-center justify-center mb-5 ${pillar.accentText} transition-colors`}
                >
                  <BrandIcon name={pillar.icon} className="w-7 h-7" />
                </motion.div>

                {/* Title */}
                <h3 className="font-serif text-xl font-semibold text-oatmeal-100 mb-2 group-hover:text-oatmeal-50 transition-colors">
                  {pillar.title}
                </h3>

                {/* Tagline */}
                <p className={`font-sans text-sm font-medium ${pillar.accentText} mb-3`}>
                  {pillar.tagline}
                </p>

                {/* Description */}
                <p className="font-sans text-sm text-oatmeal-500 leading-relaxed">
                  {pillar.description}
                </p>

                {/* Bottom decorative element */}
                <div className={`absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-current to-transparent ${pillar.accentText} opacity-0 group-hover:opacity-40 transition-opacity`} />
              </div>
            </motion.div>
          </motion.div>
        ))}
      </motion.div>
    </section>
  )
}

export default FeaturePillars
