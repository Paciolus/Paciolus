'use client'

import { motion, useInView } from 'framer-motion'
import { useRef } from 'react'

/**
 * ProcessTimeline - Marketing Component
 *
 * Visual flow showing the Paciolus transformation process:
 * 1. Upload - Raw trial balance data
 * 2. Analyze - Intelligent classification & anomaly detection
 * 3. Export - Reclassified intelligence (PDF/Excel)
 *
 * Design: "Visual Storytelling" with connecting timeline.
 * Horizontal on desktop, vertical on mobile.
 *
 * Tier 1 Animations:
 * - Scroll-triggered entrance
 * - Staggered step appearance (100ms delay)
 * - Connecting line draw animation
 * - Icon pulse on step completion
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */

interface ProcessStep {
  id: string
  number: string
  title: string
  description: string
  detail: string
  icon: React.ReactNode
  accentColor: 'sage' | 'oatmeal' | 'clay'
}

const steps: ProcessStep[] = [
  {
    id: 'upload',
    number: '01',
    title: 'Upload',
    description: 'Raw trial balance data',
    detail: 'CSV or Excel files. Multi-sheet workbooks supported. Your data stays in your browser.',
    accentColor: 'oatmeal',
    icon: (
      <svg
        className="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
        />
      </svg>
    ),
  },
  {
    id: 'analyze',
    number: '02',
    title: 'Analyze',
    description: 'Intelligent classification',
    detail: 'Automated account typing, anomaly detection, and materiality assessment in seconds.',
    accentColor: 'sage',
    icon: (
      <svg
        className="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
    ),
  },
  {
    id: 'export',
    number: '03',
    title: 'Export',
    description: 'Reclassified intelligence',
    detail: 'Professional PDF summaries and Excel workpapers. Branded and ready for delivery.',
    accentColor: 'sage',
    icon: (
      <svg
        className="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
    ),
  },
]

// Get accent color classes based on step
function getAccentClasses(accent: ProcessStep['accentColor']) {
  const classes = {
    sage: {
      bg: 'bg-sage-500/20',
      border: 'border-sage-500/40',
      text: 'text-sage-400',
      line: 'from-sage-500/40 to-sage-500/20',
      glow: 'shadow-sage-500/30',
    },
    oatmeal: {
      bg: 'bg-oatmeal-500/15',
      border: 'border-oatmeal-400/40',
      text: 'text-oatmeal-300',
      line: 'from-oatmeal-400/40 to-oatmeal-400/20',
      glow: 'shadow-oatmeal-400/25',
    },
    clay: {
      bg: 'bg-clay-500/20',
      border: 'border-clay-500/40',
      text: 'text-clay-400',
      line: 'from-clay-500/40 to-clay-500/20',
      glow: 'shadow-clay-500/30',
    },
  }
  return classes[accent]
}

// Container animation
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
}

// Step card animation
const stepVariants = {
  hidden: {
    opacity: 0,
    y: 40,
    scale: 0.9,
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: 'spring' as const,
      stiffness: 260,
      damping: 22,
    },
  },
}

// Connecting line animation
const lineVariants = {
  hidden: {
    scaleX: 0,
    originX: 0,
  },
  visible: {
    scaleX: 1,
    transition: {
      duration: 0.6,
      ease: 'easeOut' as const,
      delay: 0.4,
    },
  },
}

// Vertical line animation (mobile)
const verticalLineVariants = {
  hidden: {
    scaleY: 0,
    originY: 0,
  },
  visible: {
    scaleY: 1,
    transition: {
      duration: 0.6,
      ease: 'easeOut' as const,
      delay: 0.4,
    },
  },
}

// Icon pulse animation
const iconVariants = {
  hidden: { scale: 0.8, opacity: 0 },
  visible: {
    scale: 1,
    opacity: 1,
    transition: {
      type: 'spring' as const,
      stiffness: 400,
      damping: 15,
      delay: 0.2,
    },
  },
}

// Number badge animation
const numberVariants = {
  hidden: { scale: 0, rotate: -180 },
  visible: {
    scale: 1,
    rotate: 0,
    transition: {
      type: 'spring' as const,
      stiffness: 300,
      damping: 20,
    },
  },
}

export function ProcessTimeline() {
  const containerRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(containerRef, { once: true, margin: '-100px' })

  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 overflow-hidden">
      {/* Section Header */}
      <div className="max-w-3xl mx-auto text-center mb-16">
        <motion.span
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="inline-block font-sans text-sm font-medium text-sage-400 tracking-wide uppercase mb-3"
        >
          How It Works
        </motion.span>
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="font-serif text-3xl sm:text-4xl font-bold text-oatmeal-100 mb-4"
        >
          From Raw Data to Diagnostic Intelligence
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="font-sans text-lg text-oatmeal-400"
        >
          Three steps. Zero data retention. Complete control.
        </motion.p>
      </div>

      {/* Timeline Container */}
      <motion.div
        ref={containerRef}
        variants={containerVariants}
        initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
        className="max-w-5xl mx-auto"
      >
        {/* Desktop: Horizontal Timeline */}
        <div className="hidden md:block relative">
          {/* Connecting Lines (between steps) */}
          <div className="absolute top-[4.5rem] left-0 right-0 flex justify-center pointer-events-none">
            <div className="w-full max-w-3xl flex">
              {/* Line 1 -> 2 */}
              <div className="flex-1 flex justify-center px-8">
                <motion.div
                  variants={lineVariants}
                  className="w-full h-0.5 bg-gradient-to-r from-oatmeal-400/50 via-sage-500/50 to-sage-500/40"
                />
              </div>
              {/* Line 2 -> 3 */}
              <div className="flex-1 flex justify-center px-8">
                <motion.div
                  variants={lineVariants}
                  className="w-full h-0.5 bg-gradient-to-r from-sage-500/40 via-sage-500/50 to-sage-500/40"
                />
              </div>
            </div>
          </div>

          {/* Steps Grid */}
          <div className="grid grid-cols-3 gap-8">
            {steps.map((step, index) => {
              const accent = getAccentClasses(step.accentColor)

              return (
                <motion.div
                  key={step.id}
                  variants={stepVariants}
                  className="relative flex flex-col items-center text-center"
                >
                  {/* Step Number Badge */}
                  <motion.div
                    variants={numberVariants}
                    className="absolute -top-3 left-1/2 -translate-x-1/2 z-10"
                  >
                    <span
                      className={`inline-flex items-center justify-center w-7 h-7 rounded-full ${accent.bg} border ${accent.border} font-mono text-xs font-bold ${accent.text}`}
                    >
                      {step.number}
                    </span>
                  </motion.div>

                  {/* Icon Container */}
                  <motion.div
                    variants={iconVariants}
                    whileHover={{ scale: 1.05, rotate: 5 }}
                    className={`relative w-24 h-24 rounded-2xl ${accent.bg} border ${accent.border} flex items-center justify-center mb-6 ${accent.text} shadow-lg ${accent.glow}`}
                  >
                    {/* Subtle inner glow */}
                    <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
                    {step.icon}
                  </motion.div>

                  {/* Title */}
                  <h3 className="font-serif text-xl font-semibold text-oatmeal-100 mb-2">
                    {step.title}
                  </h3>

                  {/* Description */}
                  <p className={`font-sans text-sm font-medium ${accent.text} mb-3`}>
                    {step.description}
                  </p>

                  {/* Detail */}
                  <p className="font-sans text-sm text-oatmeal-500 leading-relaxed max-w-xs">
                    {step.detail}
                  </p>
                </motion.div>
              )
            })}
          </div>
        </div>

        {/* Mobile: Vertical Timeline */}
        <div className="md:hidden relative">
          {/* Vertical Connecting Line */}
          <motion.div
            variants={verticalLineVariants}
            className="absolute left-[2.25rem] top-12 bottom-12 w-0.5 bg-gradient-to-b from-oatmeal-400/50 via-sage-500/50 to-sage-500/40"
          />

          {/* Steps */}
          <div className="space-y-12">
            {steps.map((step, index) => {
              const accent = getAccentClasses(step.accentColor)

              return (
                <motion.div
                  key={step.id}
                  variants={stepVariants}
                  className="relative flex items-start gap-6"
                >
                  {/* Icon Container */}
                  <motion.div
                    variants={iconVariants}
                    className={`relative flex-shrink-0 w-[4.5rem] h-[4.5rem] rounded-xl ${accent.bg} border ${accent.border} flex items-center justify-center ${accent.text} shadow-lg ${accent.glow}`}
                  >
                    {/* Step Number Badge */}
                    <motion.div
                      variants={numberVariants}
                      className="absolute -top-2 -right-2 z-10"
                    >
                      <span
                        className={`inline-flex items-center justify-center w-6 h-6 rounded-full bg-obsidian-800 border ${accent.border} font-mono text-[10px] font-bold ${accent.text}`}
                      >
                        {step.number}
                      </span>
                    </motion.div>

                    {/* Inner glow */}
                    <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
                    {step.icon}
                  </motion.div>

                  {/* Content */}
                  <div className="flex-1 pt-1">
                    <h3 className="font-serif text-lg font-semibold text-oatmeal-100 mb-1">
                      {step.title}
                    </h3>
                    <p className={`font-sans text-sm font-medium ${accent.text} mb-2`}>
                      {step.description}
                    </p>
                    <p className="font-sans text-sm text-oatmeal-500 leading-relaxed">
                      {step.detail}
                    </p>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      </motion.div>

      {/* Bottom CTA hint */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5, delay: 0.6 }}
        className="max-w-lg mx-auto text-center mt-16"
      >
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-obsidian-800/70 border border-obsidian-500/40">
          <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
          <span className="font-sans text-sm text-oatmeal-400">
            Average analysis time: <span className="font-mono text-sage-400">under 3 seconds</span>
          </span>
        </div>
      </motion.div>
    </section>
  )
}

export default ProcessTimeline
