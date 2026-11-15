'use client'

import { motion } from 'framer-motion'
import { BrandIcon, type BrandIconName } from '@/components/shared'
import { Reveal } from '@/components/ui/Reveal'
import { STORAGE_STATEMENT, RESPONSIBILITY_STATEMENT, UPLOAD_HANDLING } from '@/content/storage-statement'
import { CHART_SHADOWS } from '@/utils/chartTheme'
import { HOVER, VIEWPORT } from '@/utils/marketingMotion'
import { staggerContainerTight, fadeUp } from '@/lib/motion'

/**
 * FeaturePillars - Marketing Component
 *
 * Showcases three key value propositions for Paciolus:
 * 1. Uploads not kept
 * 2. Your materiality, your thresholds
 * 3. PDF memos and Excel workpapers
 *
 * Sprint 861: copy states only what can be shown (CEO decision 2026-11-14).
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
    title: 'Uploads Not Kept',
    tagline: 'Processed in memory.',
    description: `${STORAGE_STATEMENT} The Trust page lists exactly what.`,
    accentGradient: 'from-sage-500/15 via-transparent to-transparent',
    accentBorder: 'border-sage-500/30 hover:border-sage-500/50',
    accentIconBg: 'bg-sage-500/20',
    accentIconBorder: 'border-sage-500/30 group-hover:border-sage-500/50',
    accentText: 'text-sage-400',
    icon: 'padlock',
  },
  {
    id: 'automated-sensitivity',
    title: 'Your Materiality, Your Thresholds',
    tagline: 'Set per engagement.',
    description:
      'You set materiality for each engagement. Where a tool lets you change a threshold for a run, the Sources page says so, and every default Paciolus sets is marked there as our own convention.',
    accentGradient: 'from-oatmeal-400/10 via-transparent to-transparent',
    accentBorder: 'border-oatmeal-400/30 hover:border-oatmeal-400/50',
    accentIconBg: 'bg-oatmeal-400/15',
    accentIconBorder: 'border-oatmeal-400/30 group-hover:border-oatmeal-400/50',
    accentText: 'text-oatmeal-300',
    icon: 'sliders',
  },
  {
    id: 'professional-exports',
    title: 'PDF Memos and Excel Workpapers',
    tagline: 'For your review.',
    description: `PDF memos cite the rule behind each test; Excel and CSV exports hold the results. ${RESPONSIBILITY_STATEMENT}`,
    accentGradient: 'from-clay-500/8 via-transparent to-transparent',
    accentBorder: 'border-clay-500/20 hover:border-clay-500/40',
    accentIconBg: 'bg-clay-500/15',
    accentIconBorder: 'border-clay-500/25 group-hover:border-clay-500/40',
    accentText: 'text-clay-400',
    icon: 'document',
  },
]

// Clip-path reveal — wipes in top-down (inlined from deprecated ENTER.clipReveal)
const clipReveal = {
  hidden: { clipPath: 'inset(0 0 100% 0)' },
  visible: {
    clipPath: 'inset(0 0 0% 0)',
    transition: { duration: 0.6, ease: 'easeOut' as const },
  },
}

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
} as const

export function FeaturePillars() {
  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8">
      {/* Section Header */}
      <Reveal className="max-w-3xl mx-auto text-center mb-12">
        <div className="w-12 h-[2px] bg-sage-500 rounded-full mx-auto mb-4" />
        <span className="inline-block font-sans text-xs uppercase tracking-[0.2em] text-sage-400 mb-3">
          Why Paciolus
        </span>
        <h2 className="font-serif text-3xl sm:text-4xl font-bold text-oatmeal-100 mb-4">
          What You Get
        </h2>
        <p className="font-sans text-lg text-oatmeal-400 max-w-2xl mx-auto mb-4">
          {UPLOAD_HANDLING} The conclusions you draw from the results are yours.
        </p>
        <div className="w-12 h-[2px] bg-sage-500 rounded-full mx-auto" />
      </Reveal>

      {/* Pillars Grid */}
      <Reveal>
        <motion.div
          variants={staggerContainerTight}
          initial="hidden"
          whileInView="visible"
          viewport={VIEWPORT.eager}
          className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8"
        >
          {pillars.map((pillar) => (
            <motion.div
              key={pillar.id}
              variants={fadeUp}
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
                variants={clipReveal}
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
      </Reveal>
    </section>
  )
}

export default FeaturePillars
