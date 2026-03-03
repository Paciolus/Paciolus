'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import Link from 'next/link'
import {
  motion,
  useMotionValue,
  useTransform,
  AnimatePresence,
  animate,
} from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { BrandIcon } from '@/components/shared'
import { useReducedMotion } from '@/hooks/useReducedMotion'
import { trackEvent } from '@/utils/telemetry'
import { SPRING } from '@/utils/themeUtils'
import { staggerContainer, fadeUp } from '@/lib/motion'
import type { MotionValue } from 'framer-motion'

// ── Hydration guard ─────────────────────────────────────────────────
function useHasMounted() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  return mounted
}

// ── Types ────────────────────────────────────────────────────────────

type FilmStep = 'upload' | 'analyze' | 'export'

const STEPS: FilmStep[] = ['upload', 'analyze', 'export']

const STEP_LABELS: Record<FilmStep, string> = {
  upload: 'Drop your file',
  analyze: 'See the findings',
  export: 'Take the workpapers',
}

const STEP_SUBTITLES: Record<FilmStep, string> = {
  upload: 'One gesture. Instant recognition.',
  analyze: '108 tests. Your file, read in full.',
  export: 'Complete engagement package. Yours alone.',
}

// Normalized positions for each step on the 0-1 timeline
const STEP_POSITIONS: Record<FilmStep, number> = {
  upload: 0.0,
  analyze: 0.5,
  export: 1.0,
}

// ── Auto-play constants ──────────────────────────────────────────────

/** Per-step dwell times (ms) before sweeping to the next */
const DWELL_BY_STEP: Record<FilmStep, number> = {
  upload: 3500,
  analyze: 5000,
  export: 4000,
}

/** Ordered auto-play cycle: upload → analyze → export → upload … */
const AUTO_CYCLE: FilmStep[] = ['upload', 'analyze', 'export']

// ── useScrubberFilm Hook ─────────────────────────────────────────────

function useScrubberFilm() {
  const progress = useMotionValue(0)
  const [activeStep, setActiveStep] = useState<FilmStep>('upload')
  const lastStepRef = useRef<FilmStep>('upload')

  // Auto-play state
  const [isAutoPlaying, setIsAutoPlaying] = useState(true)
  const autoPlayTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Three crossfading opacity transforms
  const uploadOpacity = useTransform(progress, [0, 0.35, 0.45], [1, 1, 0])
  const analyzeOpacity = useTransform(progress, [0.35, 0.45, 0.55, 0.65], [0, 1, 1, 0])
  const exportOpacity = useTransform(progress, [0.55, 0.65, 1.0], [0, 1, 1])

  // Upload progress bar
  const uploadProgress = useTransform(progress, [0, 0.3], [0, 1])

  // Overall progress
  const overallProgress = useTransform(progress, [0, 1], [0, 1])

  // Track active step
  useEffect(() => {
    const unsubscribe = progress.on('change', (v) => {
      let step: FilmStep = 'upload'
      if (v >= 0.55) step = 'export'
      else if (v >= 0.35) step = 'analyze'

      if (step !== lastStepRef.current) {
        lastStepRef.current = step
        setActiveStep(step)
        trackEvent('hero_step_reached', { step })
      }
    })
    return unsubscribe
  }, [progress])

  // Animate to a specific step
  const goToStep = useCallback((step: FilmStep) => {
    const target = STEP_POSITIONS[step]
    animate(progress, target, {
      type: 'spring',
      stiffness: 200,
      damping: 25,
    })
  }, [progress])

  // Scrub to arbitrary position (for drag)
  const scrubTo = useCallback((value: number) => {
    progress.set(Math.max(0, Math.min(1, value)))
  }, [progress])

  // Animate to position (for click on track)
  const animateTo = useCallback((value: number) => {
    animate(progress, Math.max(0, Math.min(1, value)), {
      type: 'spring',
      stiffness: 200,
      damping: 25,
    })
  }, [progress])

  // Pause auto-play on any user interaction with the scrubber
  const pauseAutoPlay = useCallback(() => {
    setIsAutoPlaying(false)
    if (autoPlayTimer.current) {
      clearTimeout(autoPlayTimer.current)
      autoPlayTimer.current = null
    }
  }, [])

  // Toggle auto-play (for the play/pause button)
  const toggleAutoPlay = useCallback(() => {
    setIsAutoPlaying((prev) => !prev)
  }, [])

  // Auto-play cycling effect with per-step dwell times
  useEffect(() => {
    if (!isAutoPlaying) return

    const scheduleNext = () => {
      const currentStep = lastStepRef.current
      const dwellMs = DWELL_BY_STEP[currentStep]

      autoPlayTimer.current = setTimeout(() => {
        const currentIdx = Math.max(0, AUTO_CYCLE.indexOf(lastStepRef.current))
        const nextIdx = (currentIdx + 1) % AUTO_CYCLE.length
        const nextStep = AUTO_CYCLE[nextIdx] ?? 'upload'
        const target = STEP_POSITIONS[nextStep]

        // Use a smooth tween for the auto-play sweep
        animate(progress, target, {
          type: 'tween',
          duration: 0.9,
          ease: [0.4, 0.0, 0.2, 1],
        })

        scheduleNext()
      }, dwellMs)
    }

    scheduleNext()

    return () => {
      if (autoPlayTimer.current) {
        clearTimeout(autoPlayTimer.current)
        autoPlayTimer.current = null
      }
    }
  }, [isAutoPlaying, progress])

  return {
    progress,
    uploadOpacity,
    analyzeOpacity,
    exportOpacity,
    uploadProgress,
    overallProgress,
    activeStep,
    goToStep,
    scrubTo,
    animateTo,
    isAutoPlaying,
    pauseAutoPlay,
    toggleAutoPlay,
  }
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
  progress: MotionValue<number>
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
        aria-valuenow={Math.round(progress.get() * 100)}
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
          <div className="absolute inset-0 -m-1 rounded-full bg-sage-400/20 animate-pulse pointer-events-none" />
        </motion.div>
      </div>
    </div>
  )
}

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
    animate(x, 0, { type: 'spring', stiffness: 300, damping: 20 })
    animate(y, 0, { type: 'spring', stiffness: 300, damping: 20 })
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

function LeftColumn() {
  const { isAuthenticated } = useAuth()
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
              onClick={() => trackEvent('hero_cta_click', { cta: 'start_trial' })}
            >
              <span className="relative z-10">Start Free Trial</span>
            </Link>
          </MagneticButton>
        )}
        <Link
          href="/demo"
          className="px-8 py-3.5 bg-transparent border border-oatmeal-400/30 rounded-xl text-oatmeal-300 font-sans font-medium hover:border-oatmeal-400/50 hover:bg-oatmeal-200/5 transition-all"
          onClick={() => trackEvent('hero_cta_click', { cta: 'explore_demo' })}
        >
          Explore Demo
        </Link>
      </motion.div>
    </motion.div>
  )
}

// ── Tool Tiles Data ──────────────────────────────────────────────────

const TOOL_TILES = [
  { name: 'Journal Entry Testing', activates: true },
  { name: 'AP Testing', activates: true },
  { name: 'Payroll Testing', activates: true },
  { name: 'Revenue Testing', activates: true },
  { name: 'AR Aging', activates: true },
  { name: 'Fixed Assets Testing', activates: false },
  { name: 'Inventory Testing', activates: false },
  { name: 'Bank Reconciliation', activates: true },
  { name: 'Three-Way Match', activates: false },
  { name: 'Multi-Period TB', activates: true },
  { name: 'Statistical Sampling', activates: true },
  { name: 'Multi-Currency', activates: true },
] as const

const FORMAT_BADGES = ['CSV', 'XLSX', 'OFX', 'PDF', 'QBO'] as const

// ── Upload Layer ─────────────────────────────────────────────────────

function UploadLayer({ opacity }: { opacity: MotionValue<number> }) {
  const DATA_LINES = ['847 transactions', '62 accounts', 'FY 2025'] as const

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-6"
      style={{ opacity }}
    >
      {/* File drag-in group */}
      <div className="relative flex flex-col items-center">
        {/* File icon + filename — enters from upper-left along arc */}
        <motion.div
          className="flex items-center gap-3 relative"
          initial={{ x: -80, y: -60, opacity: 0, rotate: -8 }}
          whileInView={{ x: 0, y: 0, opacity: 1, rotate: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ...SPRING.gentle }}
        >
          <BrandIcon name="file-plus" className="w-10 h-10 text-sage-400 drop-shadow-md" />
          <span className="font-mono text-sm text-oatmeal-300">
            Your_Company_FY2025.xlsx
          </span>
        </motion.div>

        {/* Sage ring pulse on landing */}
        <motion.div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 rounded-full border-2 border-sage-400 pointer-events-none"
          initial={{ scale: 1, opacity: 0 }}
          whileInView={{ scale: 1.6, opacity: [0, 0.8, 0] }}
          viewport={{ once: true }}
          transition={{ delay: 0.6, duration: 0.3, ease: 'easeOut' as const }}
        />
      </div>

      {/* Recognition — three data lines resolve sequentially */}
      <div className="flex flex-col items-center gap-1.5">
        {DATA_LINES.map((line, i) => (
          <motion.p
            key={line}
            className="font-mono text-sm font-medium text-oatmeal-200"
            initial={{ opacity: 0, y: 4 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.8 + i * 0.2, duration: 0.2, ease: 'easeOut' as const }}
          >
            {line}
          </motion.p>
        ))}
      </div>

      {/* Format badges — static row */}
      <motion.div
        className="flex items-center gap-2"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 1.0, duration: 0.3 }}
      >
        {FORMAT_BADGES.map((fmt, i) => (
          <span key={fmt}>
            <span className="font-mono text-[10px] text-sage-400/60 font-medium">
              {fmt}
            </span>
            {i < FORMAT_BADGES.length - 1 && (
              <span className="text-obsidian-500 ml-2">&middot;</span>
            )}
          </span>
        ))}
      </motion.div>

      {/* Speed indicator */}
      <motion.p
        className="font-mono text-[11px] text-sage-400 uppercase tracking-widest"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 1.2, duration: 0.3 }}
      >
        {'< 1 second'}
      </motion.p>
    </motion.div>
  )
}

// ── Analyze Layer ────────────────────────────────────────────────────

function AnalyzeLayer({ opacity }: { opacity: MotionValue<number> }) {
  // Pre-compute activation indices for stagger timing
  const activationIndices: number[] = []
  let idx = 0
  for (const tile of TOOL_TILES) {
    activationIndices.push(tile.activates ? idx++ : -1)
  }

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-4"
      style={{ opacity }}
    >
      {/* 4×3 tool grid */}
      <div className="grid grid-cols-3 gap-1.5 w-full max-w-[280px]">
        {TOOL_TILES.map((tile, i) => {
          const activationDelay = tile.activates
            ? 0.3 + (activationIndices[i] ?? 0) * 0.12
            : 0

          if (tile.activates) {
            return (
              <motion.div
                key={tile.name}
                className="relative rounded-lg border border-sage-500 bg-obsidian-800 px-1.5 py-2 flex items-center justify-center overflow-hidden"
                initial={{ opacity: 0.2 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: activationDelay, duration: 0.2, ease: 'easeOut' as const }}
              >
                <span className="font-sans text-[9px] uppercase tracking-wider text-center leading-tight text-oatmeal-100">
                  {tile.name}
                </span>
                {/* Sage flash overlay */}
                <motion.div
                  className="absolute inset-0 bg-sage-500 pointer-events-none rounded-lg"
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: [0, 0.15, 0] }}
                  viewport={{ once: true }}
                  transition={{ delay: activationDelay, duration: 0.3, ease: 'easeOut' as const }}
                />
              </motion.div>
            )
          }

          return (
            <div
              key={tile.name}
              className="rounded-lg border border-obsidian-700/50 bg-obsidian-800/50 px-1.5 py-2 flex items-center justify-center opacity-25"
            >
              <span className="font-sans text-[9px] uppercase tracking-wider text-center leading-tight text-oatmeal-500/60 line-through decoration-obsidian-600">
                {tile.name}
              </span>
            </div>
          )
        })}
      </div>

      {/* Summary line */}
      <motion.p
        className="font-sans text-xs text-oatmeal-200 text-center"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{
          delay: 0.3 + 8 * 0.12 + 0.3, // after last tile + 0.3s
          duration: 0.3,
          ease: 'easeOut' as const,
        }}
      >
        108 tests run across 9 tools &middot; 3 findings flagged
      </motion.p>
    </motion.div>
  )
}

// ── Export Layer ──────────────────────────────────────────────────────

function ExportLayer({ opacity }: { opacity: MotionValue<number> }) {
  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-5"
      style={{ opacity }}
    >
      {/* File list — two rows, instantly present */}
      <div className="w-full max-w-[320px] flex flex-col gap-2.5">
        {/* Workpapers row */}
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-obsidian-700 border border-obsidian-500">
          <BrandIcon name="spreadsheet" className="w-5 h-5 text-sage-400 flex-shrink-0" />
          <span className="font-sans text-sm text-oatmeal-100 font-medium flex-1 min-w-0 truncate">
            Your_Company_Workpapers.xlsx
          </span>
          <BrandIcon name="download-arrow" className="w-4 h-4 text-sage-400 flex-shrink-0" />
        </div>

        {/* PDF memos row */}
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-obsidian-700 border border-obsidian-500">
          <BrandIcon name="document-blank" className="w-5 h-5 text-oatmeal-300 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <span className="font-sans text-sm text-oatmeal-100 font-medium">
              17 PDF Memos
            </span>
            <p className="font-sans text-[11px] text-oatmeal-400 truncate mt-0.5">
              JE Testing &middot; Revenue &middot; AP &middot; Sampling &middot; ...
            </p>
          </div>
          <BrandIcon name="download-arrow" className="w-4 h-4 text-sage-400 flex-shrink-0" />
        </div>
      </div>

      {/* Download CTA button */}
      <div className="w-full max-w-[320px]">
        <div className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-sage-500 text-obsidian-900">
          <BrandIcon name="download-arrow" className="w-4 h-4" />
          <span className="font-sans text-sm font-medium">
            Download Engagement File
          </span>
        </div>
      </div>

      {/* Zero-storage whisper — fades in, holds, fades out */}
      <motion.p
        className="font-sans text-[11px] text-oatmeal-400 italic text-center"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: [0, 0, 1, 1, 0] }}
        viewport={{ once: true }}
        transition={{
          duration: 4.2,
          times: [0, 0.286, 0.429, 0.905, 1.0],
          ease: 'linear',
        }}
      >
        Processed entirely in your browser. Your data never left this tab.
      </motion.p>
    </motion.div>
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
  uploadOpacity: MotionValue<number>
  analyzeOpacity: MotionValue<number>
  exportOpacity: MotionValue<number>
  activeStep: FilmStep
  isAutoPlaying: boolean
  onToggleAutoPlay: () => void
}) {
  return (
    <div className="w-full max-w-md mx-auto lg:max-w-none">
      <div className="rounded-2xl border border-obsidian-500/30 bg-obsidian-800/60 backdrop-blur-xl overflow-hidden shadow-2xl shadow-obsidian-900/50">
        {/* Panel header */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-obsidian-500/30">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-clay-400/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-oatmeal-500/40" />
            <div className="w-2.5 h-2.5 rounded-full bg-sage-400/60" />
          </div>
          {/* Play / Pause toggle */}
          <button
            onClick={onToggleAutoPlay}
            className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-obsidian-700/40 border border-obsidian-500/30 text-oatmeal-500 hover:text-oatmeal-300 hover:bg-obsidian-700/60 transition-all duration-200"
            aria-label={isAutoPlaying ? 'Pause auto-play' : 'Resume auto-play'}
          >
            {isAutoPlaying ? (
              <svg className="w-2.5 h-2.5" viewBox="0 0 12 12" fill="currentColor">
                <rect x="1" y="1" width="3.5" height="10" rx="0.75" />
                <rect x="7.5" y="1" width="3.5" height="10" rx="0.75" />
              </svg>
            ) : (
              <svg className="w-2.5 h-2.5" viewBox="0 0 12 12" fill="currentColor">
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
          className="relative min-h-[280px] md:min-h-[260px] lg:min-h-[280px] bg-obsidian-900"
          aria-label="Product workflow demonstration: upload, analyze, export"
          role="img"
        >
          <UploadLayer opacity={uploadOpacity} />
          <AnalyzeLayer opacity={analyzeOpacity} />
          <ExportLayer opacity={exportOpacity} />
        </div>

        {/* Caption — mobile-only subtitle (desktop shows in scrubber) */}
        <div className="px-5 pt-2 pb-2 sm:hidden border-t border-obsidian-500/20">
          <div className="h-6 relative">
            <AnimatePresence mode="wait">
              <motion.p
                key={activeStep}
                className="font-sans text-sm italic text-oatmeal-400 absolute inset-0"
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

// ── Reduced Motion Fallback ──────────────────────────────────────────

function StaticFallback() {
  const { isAuthenticated } = useAuth()
  const mounted = useHasMounted()

  return (
    <section className="relative z-10 pt-28 pb-24 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-8 items-center">
          <div className="text-center lg:text-left">
            <h1 className="type-display-xl text-oatmeal-100 mb-6 text-center lg:text-left">
              The Workpapers
              <br />
              <span className="bg-gradient-to-r from-sage-400 via-sage-300 to-oatmeal-300 bg-clip-text text-transparent">
                Write Themselves
              </span>
            </h1>

            <p className="font-sans text-lg text-oatmeal-400 max-w-lg mb-10 text-center lg:text-left">
              Professional-grade diagnostics, testing, and workpapers — built on ISA and PCAOB standards. Zero data retained.
            </p>

            <div className="flex items-center justify-center lg:justify-start gap-4">
              {mounted && !isAuthenticated && (
                <Link
                  href="/register"
                  className="group relative px-8 py-3.5 bg-sage-600 rounded-xl text-white font-sans font-medium hover:bg-sage-500 transition-all shadow-lg shadow-sage-600/25 hover:shadow-xl hover:shadow-sage-600/30"
                  onClick={() => trackEvent('hero_cta_click', { cta: 'start_trial' })}
                >
                  <span className="relative z-10">Start Free Trial</span>
                </Link>
              )}
              <Link
                href="/demo"
                className="px-8 py-3.5 bg-transparent border border-oatmeal-400/30 rounded-xl text-oatmeal-300 font-sans font-medium hover:border-oatmeal-400/50 hover:bg-oatmeal-200/5 transition-all"
                onClick={() => trackEvent('hero_cta_click', { cta: 'explore_demo' })}
              >
                Explore Demo
              </Link>
            </div>
          </div>

          {/* Static export state panel */}
          <div className="w-full max-w-md mx-auto lg:max-w-none">
            <div className="rounded-2xl border border-obsidian-500/30 bg-obsidian-800/60 backdrop-blur-xl overflow-hidden shadow-2xl shadow-obsidian-900/50">
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-obsidian-500/30">
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-clay-400/60" />
                  <div className="w-2.5 h-2.5 rounded-full bg-oatmeal-500/40" />
                  <div className="w-2.5 h-2.5 rounded-full bg-sage-400/60" />
                </div>
                <span className="text-oatmeal-500 text-xs font-sans font-medium uppercase tracking-wider">
                  Paciolus
                </span>
              </div>

              <div className="min-h-[280px] md:min-h-[260px] lg:min-h-[280px] bg-obsidian-900 flex flex-col items-center justify-center gap-4 p-5">
                {/* File list */}
                <div className="w-full max-w-[320px] flex flex-col gap-2.5">
                  <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-obsidian-700 border border-obsidian-500">
                    <BrandIcon name="spreadsheet" className="w-5 h-5 text-sage-400 flex-shrink-0" />
                    <span className="font-sans text-sm text-oatmeal-100 font-medium flex-1 min-w-0 truncate">
                      Your_Company_Workpapers.xlsx
                    </span>
                    <BrandIcon name="download-arrow" className="w-4 h-4 text-sage-400 flex-shrink-0" />
                  </div>
                  <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-obsidian-700 border border-obsidian-500">
                    <BrandIcon name="document-blank" className="w-5 h-5 text-oatmeal-300 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <span className="font-sans text-sm text-oatmeal-100 font-medium">
                        17 PDF Memos
                      </span>
                      <p className="font-sans text-[11px] text-oatmeal-400 truncate mt-0.5">
                        JE Testing &middot; Revenue &middot; AP &middot; Sampling &middot; ...
                      </p>
                    </div>
                    <BrandIcon name="download-arrow" className="w-4 h-4 text-sage-400 flex-shrink-0" />
                  </div>
                </div>

                {/* Download button */}
                <div className="w-full max-w-[320px]">
                  <div className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-sage-500 text-obsidian-900">
                    <BrandIcon name="download-arrow" className="w-4 h-4" />
                    <span className="font-sans text-sm font-medium">
                      Download Engagement File
                    </span>
                  </div>
                </div>

                {/* Zero-storage — static text (no animation) */}
                <p className="font-sans text-[11px] text-oatmeal-400 italic text-center">
                  Processed entirely in your browser. Your data never left this tab.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

// ── Main Export: HeroScrollSection ───────────────────────────────────

export function HeroScrollSection() {
  const { prefersReducedMotion } = useReducedMotion()

  if (prefersReducedMotion) {
    return <StaticFallback />
  }

  return <ScrubberHero />
}

function ScrubberHero() {
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
  } = useScrubberFilm()

  return (
    <section
      className="relative z-10 min-h-screen flex flex-col justify-center pt-20 pb-8 px-6"
      aria-label="Product demonstration"
    >
      <div className="max-w-7xl mx-auto w-full flex-1 flex flex-col justify-center">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-8 items-center mb-12">
          <LeftColumn />
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

/** @deprecated Use HeroScrollSection instead */
export const HeroProductFilm = HeroScrollSection
