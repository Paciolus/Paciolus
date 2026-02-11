'use client'

import { motion } from 'framer-motion'

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
  icon: React.ReactNode
}

const pillars: FeaturePillar[] = [
  {
    id: 'zero-knowledge',
    title: 'Zero-Knowledge Security',
    tagline: 'Your data never touches our servers',
    description:
      'All analysis happens locally in your browser. Financial data is processed client-side and immediately discarded. No storage, no risk, no compromise.',
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
        />
      </svg>
    ),
  },
  {
    id: 'automated-sensitivity',
    title: 'Automated Sensitivity',
    tagline: 'Intelligent threshold tuning',
    description:
      'Dynamic materiality thresholds adapt to your practice settings and client profiles. Surface what matters, filter the noise automatically.',
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
        />
      </svg>
    ),
  },
  {
    id: 'professional-exports',
    title: 'Professional-Grade Exports',
    tagline: 'PDF reports & Excel workpapers',
    description:
      'Generate presentation-ready diagnostic summaries and detailed workpapers. Branded, formatted, and ready for client delivery or working papers.',
    icon: (
      <svg
        className="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
    ),
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
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  },
  hover: {
    y: -6,
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1)',
    transition: {
      type: 'spring' as const,
      stiffness: 300,
      damping: 20,
    },
  },
}

export function FeaturePillars() {
  return (
    <section className="py-16 px-4 sm:px-6 lg:px-8">
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
              className="relative h-full bg-obsidian-800 rounded-2xl border border-obsidian-600/50 overflow-hidden"
            >
              {/* Subtle gradient overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-obsidian-700/20 via-transparent to-sage-500/10 pointer-events-none" />

              {/* Top accent line */}
              <div className="absolute top-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-sage-500/30 to-transparent" />

              <div className="relative p-6 lg:p-8">
                {/* Icon Container */}
                <motion.div
                  variants={iconVariants}
                  className="w-14 h-14 rounded-xl bg-sage-500/10 border border-sage-500/20 flex items-center justify-center mb-5 text-sage-400 group-hover:border-sage-500/40 transition-colors"
                >
                  {pillar.icon}
                </motion.div>

                {/* Title */}
                <h3 className="font-serif text-xl font-semibold text-oatmeal-100 mb-2 group-hover:text-oatmeal-50 transition-colors">
                  {pillar.title}
                </h3>

                {/* Tagline */}
                <p className="font-sans text-sm font-medium text-sage-400 mb-3">
                  {pillar.tagline}
                </p>

                {/* Description */}
                <p className="font-sans text-sm text-oatmeal-500 leading-relaxed">
                  {pillar.description}
                </p>

                {/* Bottom decorative element */}
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-sage-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </motion.div>
          </motion.div>
        ))}
      </motion.div>
    </section>
  )
}

export default FeaturePillars
