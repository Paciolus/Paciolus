// Presentational shell: imports animation and telemetry hooks, renders JSX — no animation or telemetry logic inline.
'use client'

import { useRef, useCallback } from 'react'
import Link from 'next/link'
import {
  motion,
  useMotionValue,
  useTransform,
  AnimatePresence,
  MotionConfig,
  animate,
} from 'framer-motion'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { BrandIcon } from '@/components/shared'
import { useReducedMotion } from '@/hooks/useReducedMotion'
import { staggerContainer, fadeUp } from '@/lib/motion'
import { UploadLayer, AnalyzeLayer, ExportLayer } from './HeroFilmFrame'
import {
  useScrubberFilm,
  useHasMounted,
  STEPS,
  STEP_LABELS,
  STEP_SUBTITLES,
  STEP_POSITIONS,
} from './useHeroAnimation'
import { useHeroTelemetry } from './useHeroTelemetry'
import type { FilmStep } from './useHeroAnimation'
import type { MotionValue as MotionValueType } from 'framer-motion'


// ── Magnetic Hover (A1 — Visual Polish) ─────────────────────────────

/** Wrapper that subtly pulls its child toward the cursor (3px max). */
function MagneticButton({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const prefersReduced = useReducedMotion()
  const x = useMotionValue(0)
  const y = useMotionValue(0)

  const handleMouse = useCallback((e: React.MouseEvent) => {
    if (prefersReduced || !ref.current) return
    const rect = ref.current.getBoundingClientRect()
    const cx = rect.left + rect.width / 2
    const cy = rect.top + rect.height / 2
    const dx = (e.clientX - cx) / rect.width
    const dy = (e.clientY - cy) / rect.height
    x.set(dx * 3)
    y.set(dy * 3)
  }, [prefersReduced, x, y])

  const handleLeave = useCallback(() => {
    animate(x, 0, { type: 'spring' as const, stiffness: 300, damping: 20 })
    animate(y, 0, { type: 'spring' as const, stiffness: 300, damping: 20 })
  }, [x, y])

  return (
    <motion.div
      ref={ref}
      style={{ x, y }}
      onMouseMove={handleMouse}
      onMouseLeave={handleLeave}
      className={className}
    >
      {children}
    </motion.div>
  )
}

// ── Left Column ──────────────────────────────────────────────────────

function LeftColumn({ trackCtaClick }: { trackCtaClick: (cta: string) => void }) {
  const { isAuthenticated } = useAuthSession()
  const mounted = useHasMounted()

  return (
    <motion.div
      className="flex flex-col justify-center editorial-hero"
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
    >
      <motion.h1
        className="type-display-xl text-oatmeal-100 mb-6 text-center lg:text-left"
        variants={fadeUp}
      >
        The Workpapers
        <br />
        <span className="bg-gradient-to-r from-sage-400 via-sage-300 to-oatmeal-300 bg-clip-text text-transparent">
          Write Themselves
        </span>
      </motion.h1>

      {/* Subheadline */}
      <motion.p
        className="font-sans text-lg text-oatmeal-400 max-w-lg mb-6 text-center lg:text-left"
        variants={fadeUp}
      >
        Professional-grade diagnostics, testing, and workpapers — built on ISA and PCAOB standards. Zero data retained.
      </motion.p>

      {/* Introductory pricing callout */}
      <motion.div
        className="mb-8 max-w-lg mx-auto lg:mx-0"
        variants={fadeUp}
      >
        <Link
          href="/pricing"
          className="group flex items-center gap-3 px-4 py-3 rounded-xl bg-obsidian-800/80 border border-sage-500/30 hover:border-sage-500/50 transition-colors"
        >
          <div className="w-0.5 h-8 bg-sage-500 rounded-full flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="font-sans text-sm text-oatmeal-200">
              Introductory: <span className="text-sage-400 font-medium">20% off your first 3 months</span>
            </p>
            <p className="font-sans text-xs text-oatmeal-500 group-hover:text-oatmeal-400 transition-colors">
              See Pricing &rarr;
            </p>
          </div>
        </Link>
      </motion.div>

      {/* CTAs */}
      <motion.div
        className="flex items-center justify-center lg:justify-start gap-4"
        variants={fadeUp}
      >
        {mounted && !isAuthenticated && (
          <MagneticButton>
            <Link
              href="/register"
              className="group relative inline-block px-8 py-3.5 bg-sage-600 rounded-xl text-white font-sans font-medium hover:bg-sage-500 transition-all shadow-lg shadow-sage-600/25 hover:shadow-xl hover:shadow-sage-600/30"
              onClick={() => trackCtaClick('start_trial')}
            >
              <span className="relative z-10">Start Free Trial</span>
            </Link>
          </MagneticButton>
        )}
        <Link
          href="/demo"
          className="px-8 py-3.5 bg-transparent border border-oatmeal-400/30 rounded-xl text-oatmeal-300 font-sans font-medium hover:border-oatmeal-400/50 hover:bg-oatmeal-200/5 transition-all"
          onClick={() => trackCtaClick('explore_demo')}
        >
          Explore Demo
        </Link>
      </motion.div>
    </motion.div>
  )
}

// ── Timeline Scrubber ────────────────────────────────────────────────

function TimelineScrubber({
  progress,
  activeStep,
  goToStep,
  scrubTo,
  animateTo,
  onUserInteract,
}: {
  progress: MotionValueType<number>
  activeStep: FilmStep
  goToStep: (step: FilmStep) => void
  scrubTo: (value: number) => void
  animateTo: (value: number) => void
  onUserInteract: () => void
}) {
  const trackRef = useRef<HTMLDivElement>(null)
  const isDragging = useRef(false)

  const getProgressFromEvent = useCallback((clientX: number) => {
    if (!trackRef.current) return 0
    const rect = trackRef.current.getBoundingClientRect()
    return Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
  }, [])

  // Mouse drag handlers
  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    onUserInteract()
    isDragging.current = true
    const value = getProgressFromEvent(e.clientX)
    scrubTo(value)
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
  }, [getProgressFromEvent, scrubTo, onUserInteract])

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!isDragging.current) return
    const value = getProgressFromEvent(e.clientX)
    scrubTo(value)
  }, [getProgressFromEvent, scrubTo])

  const handlePointerUp = useCallback(() => {
    isDragging.current = false
  }, [])

  // Track click (not on handle)
  const handleTrackClick = useCallback((e: React.MouseEvent) => {
    onUserInteract()
    const value = getProgressFromEvent(e.clientX)
    animateTo(value)
  }, [getProgressFromEvent, animateTo, onUserInteract])

  // Keyboard navigation for the slider
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    const step = 0.05
    if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
      e.preventDefault()
      onUserInteract()
      animateTo(Math.min(1, progress.get() + step))
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
      e.preventDefault()
      onUserInteract()
      animateTo(Math.max(0, progress.get() - step))
    } else if (e.key === 'Home') {
      e.preventDefault()
      onUserInteract()
      animateTo(0)
    } else if (e.key === 'End') {
      e.preventDefault()
      onUserInteract()
      animateTo(1)
    }
  }, [animateTo, progress, onUserInteract])

  // Handle position driven by progress
  const handleX = useTransform(progress, (v) => `${v * 100}%`)

  // Filled track width
  const filledWidth = useTransform(progress, (v) => `${v * 100}%`)

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Step labels with integrated descriptions */}
      <div className="relative flex justify-between mb-3 px-1">
        {STEPS.map((step) => {
          const isActive = step === activeStep
          const isPast = STEPS.indexOf(activeStep) > STEPS.indexOf(step)

          return (
            <button
              key={step}
              onClick={() => { onUserInteract(); goToStep(step) }}
              className="group relative flex flex-col items-center gap-1.5 max-w-[30%]"
              aria-label={`Go to ${STEP_LABELS[step]} step`}
            >
              {/* Step dot */}
              <div className={`
                w-3 h-3 rounded-full border-2 transition-all duration-300 flex-shrink-0
                ${isActive
                  ? 'bg-sage-400 border-sage-400 shadow-sm shadow-sage-400/50 scale-110'
                  : isPast
                    ? 'bg-sage-500/60 border-sage-500/60'
                    : 'bg-obsidian-700 border-obsidian-500/50 group-hover:border-oatmeal-500/50'
                }
              `} />

              {/* Label */}
              <span className={`
                font-sans text-xs font-medium uppercase tracking-wider transition-colors duration-300
                ${isActive ? 'text-oatmeal-200' : 'text-oatmeal-600 group-hover:text-oatmeal-400'}
              `}>
                {STEP_LABELS[step]}
              </span>

              {/* Inline subtitle — visible on active step */}
              <span className={`
                font-sans text-[10px] leading-snug text-center transition-all duration-300 hidden sm:block
                ${isActive ? 'text-oatmeal-400 opacity-100' : 'text-oatmeal-700 opacity-0'}
              `}>
                {STEP_SUBTITLES[step]}
              </span>
            </button>
          )
        })}
      </div>

      {/* Track */}
      <div
        ref={trackRef}
        className="relative h-8 flex items-center cursor-pointer group"
        onClick={handleTrackClick}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onKeyDown={handleKeyDown}
        role="slider"
        aria-label="Timeline scrubber"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round((STEPS.indexOf(activeStep) / (STEPS.length - 1)) * 100)}
        aria-valuetext={STEP_LABELS[activeStep]}
        tabIndex={0}
      >
        {/* Track background */}
        <div className="absolute inset-x-0 h-1.5 rounded-full bg-obsidian-600/60">
          {/* Filled portion */}
          <motion.div
            className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-sage-500/80 to-sage-400/80"
            style={{ width: filledWidth }}
          />

          {/* Step markers on track */}
          {STEPS.map((step) => (
            <div
              key={step}
              className="absolute top-1/2 -translate-y-1/2 w-1 h-1 rounded-full bg-obsidian-400/60"
              style={{ left: `${STEP_POSITIONS[step] * 100}%` }}
            />
          ))}
        </div>

        {/* Draggable handle */}
        <motion.div
          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10"
          style={{ left: handleX }}
        >
          <div className="
            w-5 h-5 rounded-full bg-oatmeal-100 border-2 border-sage-400
            shadow-lg shadow-sage-500/30
            cursor-grab active:cursor-grabbing
            transition-transform duration-150
            hover:scale-125 active:scale-110
          " />

          {/* Glow ring */}
          <div className="absolute inset-0 -m-1 rounded-full bg-sage-400/20 motion-safe:animate-pulse pointer-events-none" />
        </motion.div>
      </div>
    </div>
  )
}

// ── Film Stage ───────────────────────────────────────────────────────

function FilmStage({
  uploadOpacity,
  analyzeOpacity,
  exportOpacity,
  activeStep,
  isAutoPlaying,
  onToggleAutoPlay,
}: {
  uploadOpacity: MotionValueType<number>
  analyzeOpacity: MotionValueType<number>
  exportOpacity: MotionValueType<number>
  activeStep: FilmStep
  isAutoPlaying: boolean
  onToggleAutoPlay: () => void
}) {
  return (
    <div className="w-full max-w-md mx-auto lg:max-w-none">
      <div className="rounded-2xl border border-obsidian-200/30 bg-oatmeal-50/90 backdrop-blur-xl overflow-hidden shadow-xl shadow-obsidian-200/20">
        {/* Panel header */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-obsidian-200/20">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-clay-400/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-oatmeal-500/40" />
            <div className="w-2.5 h-2.5 rounded-full bg-sage-400/60" />
          </div>
          {/* Play / Pause toggle */}
          <button
            onClick={onToggleAutoPlay}
            className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-oatmeal-100/80 border border-obsidian-200/20 text-obsidian-400 hover:text-obsidian-600 hover:bg-oatmeal-200/60 transition-all duration-200"
            aria-label={isAutoPlaying ? 'Pause auto-play' : 'Resume auto-play'}
          >
            {isAutoPlaying ? (
              <svg className="w-2.5 h-2.5" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true">
                <rect x="1" y="1" width="3.5" height="10" rx="0.75" />
                <rect x="7.5" y="1" width="3.5" height="10" rx="0.75" />
              </svg>
            ) : (
              <svg className="w-2.5 h-2.5" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true">
                <path d="M2.5 1.5a.5.5 0 0 1 .76-.43l7.5 4.5a.5.5 0 0 1 0 .86l-7.5 4.5A.5.5 0 0 1 2.5 10.5v-9z" />
              </svg>
            )}
            <span className="text-[10px] font-sans font-medium uppercase tracking-wider">
              {isAutoPlaying ? 'Pause' : 'Play'}
            </span>
          </button>
        </div>

        {/* Layer container */}
        <div
          className="relative min-h-[300px] md:min-h-[280px] lg:min-h-[300px] bg-oatmeal-50"
          aria-label="Product workflow demonstration: upload, analyze, export"
          role="img"
        >
          <UploadLayer opacity={uploadOpacity} isActive={activeStep === 'upload'} />
          <AnalyzeLayer opacity={analyzeOpacity} isActive={activeStep === 'analyze'} />
          <ExportLayer opacity={exportOpacity} isActive={activeStep === 'export'} />
        </div>

        {/* Caption — mobile-only subtitle (desktop shows in scrubber) */}
        <div className="px-5 pt-2 pb-2 sm:hidden border-t border-obsidian-200/20">
          <div className="h-6 relative">
            <AnimatePresence mode="wait">
              <motion.p
                key={activeStep}
                className="font-sans text-sm italic text-obsidian-400 absolute inset-0"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25, ease: 'easeOut' as const }}
              >
                {STEP_SUBTITLES[activeStep]}
              </motion.p>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main Export: HeroScrollSection ───────────────────────────────────

export function HeroScrollSection() {
  // Always render ScrubberHero — MotionConfig handles reduced-motion gracefully
  // by completing animations instantly instead of hiding the entire UI
  return (
    <MotionConfig reducedMotion="user">
      <ScrubberHero />
    </MotionConfig>
  )
}

function ScrubberHero() {
  const { onStepChange, trackCtaClick } = useHeroTelemetry()

  const {
    progress,
    uploadOpacity,
    analyzeOpacity,
    exportOpacity,
    activeStep,
    goToStep,
    scrubTo,
    animateTo,
    isAutoPlaying,
    pauseAutoPlay,
    toggleAutoPlay,
  } = useScrubberFilm(onStepChange)

  return (
    <section
      className="relative z-10 min-h-[600px] lg:min-h-[700px] max-h-[900px] flex flex-col justify-center pt-28 lg:pt-20 pb-8 px-6"
      aria-label="Product demonstration"
    >
      <div className="max-w-7xl mx-auto w-full flex-1 flex flex-col justify-center">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-8 items-center mb-12">
          <LeftColumn trackCtaClick={trackCtaClick} />
          <FilmStage
            uploadOpacity={uploadOpacity}
            analyzeOpacity={analyzeOpacity}
            exportOpacity={exportOpacity}
            activeStep={activeStep}
            isAutoPlaying={isAutoPlaying}
            onToggleAutoPlay={toggleAutoPlay}
          />
        </div>

        {/* Timeline Scrubber */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 1.0 }}
        >
          <TimelineScrubber
            progress={progress}
            activeStep={activeStep}
            goToStep={goToStep}
            scrubTo={scrubTo}
            animateTo={animateTo}
            onUserInteract={pauseAutoPlay}
          />
        </motion.div>
      </div>
    </section>
  )
}
