'use client'

import { motion } from 'framer-motion'
import { CHART_SHADOWS } from '@/utils/chartTheme'
import { BrandIcon, type BrandIconName } from '@/components/shared'

/**
 * FeaturePillars - Marketing Component
 *
 * Showcases three key value propositions for Paciolus:
 * 1. Zero-Knowledge Security
 * 2. Automated Sensitivity
 * 3. Professional-Grade Exports
 *
 * Design: "Fintech Authority" aesthetic with Oat & Obsidian palette.
 * Cards feature subtle sage accents on icons and hover states.
 *
 * Tier 1 Animations:
 * - Staggered entrance (60ms delay per pillar)
 * - Subtle hover lift effect
 * - Icon pulse on hover
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
    title: 'Zero-Knowledge Security',
    tagline: 'Your data never touches our servers',
    description:
      'All analysis happens locally in your browser. Financial data is processed client-side and immediately discarded. No storage, no risk, no compromise.',
    accentGradient: 'from-sage-500/15 via-transparent to-transparent',
    accentBorder: 'border-sage-500/30 hover:border-sage-500/50',
    accentIconBg: 'bg-sage-500/20',
    accentIconBorder: 'border-sage-500/30 group-hover:border-sage-500/50',
    accentText: 'text-sage-400',
    icon: 'padlock',
  },
  {
    id: 'automated-sensitivity',
    title: 'Automated Sensitivity',
    tagline: 'Intelligent threshold tuning',
    description:
      'Dynamic materiality thresholds adapt to your practice settings and client profiles. Surface what matters, filter the noise automatically.',
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
    tagline: 'PDF reports & Excel workpapers',
    description:
      'Generate presentation-ready diagnostic summaries and detailed workpapers. Branded, formatted, and ready for client delivery or working papers.',
    accentGradient: 'from-clay-500/8 via-transparent to-transparent',
    accentBorder: 'border-clay-500/20 hover:border-clay-500/40',
    accentIconBg: 'bg-clay-500/15',
    accentIconBorder: 'border-clay-500/25 group-hover:border-clay-500/40',
    accentText: 'text-clay-400',
    icon: 'document',
  },
]

// Container animation for staggered children
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06,
      delayChildren: 0.1,
    },
  },
}

// Individual pillar card animation
const pillarVariants = {
  hidden: {
    opacity: 0,
    y: 30,
    scale: 0.95,
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: 'spring' as const,
      stiffness: 280,
      damping: 24,
    },
  },
}

// Icon container animation
const iconVariants = {
  rest: {
    scale: 1,
    rotate: 0,
  },
  hover: {
    scale: 1.1,
    rotate: 3,
    transition: {
      type: 'spring' as const,
      stiffness: 400,
      damping: 15,
    },
  },
}

// Card hover animation
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
      <div className="max-w-3xl mx-auto text-center mb-12">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.5 }}
          className="font-serif text-3xl sm:text-4xl font-bold text-oatmeal-100 mb-4"
        >
          Built for Financial Professionals
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="font-sans text-lg text-oatmeal-400 max-w-2xl mx-auto"
        >
          Enterprise-grade diagnostic intelligence without the enterprise complexity.
          Security, precision, and polish in every analysis.
        </motion.p>
      </div>

      {/* Pillars Grid */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-50px' }}
        className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8"
      >
        {pillars.map((pillar) => (
          <motion.div
            key={pillar.id}
            variants={pillarVariants}
            whileHover="hover"
            initial="rest"
            animate="rest"
            className="relative group"
          >
            <motion.div
              variants={cardHoverVariants}
              className={`relative h-full bg-obsidian-800 rounded-2xl border ${pillar.accentBorder} overflow-hidden transition-colors`}
            >
              {/* Per-pillar gradient overlay */}
              <div className={`absolute inset-0 bg-gradient-to-br ${pillar.accentGradient} pointer-events-none`} />

              {/* Top accent line */}
              <div className={`absolute top-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-current to-transparent ${pillar.accentText} opacity-30`} />

              <div className="relative p-6 lg:p-8">
                {/* Icon Container */}
                <motion.div
                  variants={iconVariants}
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
