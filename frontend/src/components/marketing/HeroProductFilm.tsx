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
  upload: 'Upload',
  analyze: 'Analyze',
  export: 'Export',
}

const STEP_SUBTITLES: Record<FilmStep, string> = {
  upload: 'One file. Ten supported formats. Parsed in under a second.',
  analyze: '17 ratios. 6 anomaly checks. 12 testing tools primed. Zero financial data stored.',
  export: '17 ISA/PCAOB-cited memos. Engagement file complete in one click.',
}

// Normalized positions for each step on the 0-1 timeline
const STEP_POSITIONS: Record<FilmStep, number> = {
  upload: 0.0,
  analyze: 0.5,
  export: 1.0,
}

// ── Auto-play constants ──────────────────────────────────────────────

/** Seconds to dwell on each step before sweeping to the next */
const DWELL_MS = 4000
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

  // Auto-play cycling effect
  useEffect(() => {
    if (!isAutoPlaying) return

    const scheduleNext = () => {
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
      }, DWELL_MS)
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
    <div className="flex flex-col justify-center editorial-hero">
      <motion.h1
        className="type-display-xl text-oatmeal-100 mb-6 text-center lg:text-left"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.7, delay: 0.15 }}
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
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.7, delay: 0.45 }}
      >
        Professional-grade diagnostics, testing, and workpapers — built on ISA and PCAOB standards. Zero data retained.
      </motion.p>

      {/* Introductory pricing callout */}
      <motion.div
        className="mb-8 max-w-lg mx-auto lg:mx-0"
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5, delay: 0.55 }}
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
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.7, delay: 0.7 }}
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
    </div>
  )
}

// ── Upload Layer ─────────────────────────────────────────────────────

const FILE_FORMATS = [
  { ext: 'CSV', color: 'text-sage-600' },
  { ext: 'XLSX', color: 'text-sage-600' },
  { ext: 'OFX', color: 'text-obsidian-500' },
  { ext: 'PDF', color: 'text-clay-500' },
  { ext: 'TSV', color: 'text-obsidian-500' },
  { ext: 'QBO', color: 'text-obsidian-500' },
  { ext: 'IIF', color: 'text-obsidian-500' },
  { ext: 'ODS', color: 'text-sage-600' },
  { ext: 'TXT', color: 'text-obsidian-500' },
]

/** Rapid count-up for the account counter */
function useRapidCount(target: number, durationMs: number) {
  const [count, setCount] = useState(0)
  const [started, setStarted] = useState(false)
  const frameRef = useRef<number>(0)

  const start = useCallback(() => { setStarted(true) }, [])

  useEffect(() => {
    if (!started) return
    const startTime = performance.now()
    const tick = (now: number) => {
      const elapsed = now - startTime
      const progress = Math.min(1, elapsed / durationMs)
      // Ease-out curve for a decelerating counter
      const eased = 1 - Math.pow(1 - progress, 3)
      setCount(Math.round(eased * target))
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick)
      }
    }
    frameRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frameRef.current)
  }, [started, target, durationMs])

  return { count, start }
}

function UploadLayer({
  opacity,
  progress,
}: {
  opacity: MotionValue<number>
  progress: MotionValue<number>
}) {
  const { count: accountCount, start: startCount } = useRapidCount(47, 600)
  const [formatIndex, setFormatIndex] = useState(0)

  // Cycle through file format badges
  useEffect(() => {
    const interval = setInterval(() => {
      setFormatIndex((i) => (i + 1) % FILE_FORMATS.length)
    }, 400)
    return () => clearInterval(interval)
  }, [])

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6"
      style={{ opacity }}
    >
      {/* Drop zone */}
      <motion.div
        className="w-full max-w-[280px] border-2 border-dashed border-obsidian-300/40 rounded-xl p-5 flex flex-col items-center gap-3 relative overflow-hidden"
        initial={{ opacity: 0, borderColor: 'rgba(33,33,33,0.2)' }}
        whileInView={{ opacity: 1, borderColor: 'rgba(74,124,89,0.5)' }}
        viewport={{ once: true }}
        transition={{ duration: 1.5 }}
        onViewportEnter={startCount}
      >
        {/* File icon dropping in */}
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.8 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3, ...SPRING.gentle }}
        >
          <BrandIcon name="file-plus" className="w-9 h-9 text-sage-600" />
        </motion.div>

        {/* Filename + rapid counter */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
        >
          <p className="font-mono text-sm text-obsidian-700">financial_data_2025.xlsx</p>
          <span className="font-mono text-xs text-sage-600 font-medium tabular-nums">
            {accountCount} accounts detected
          </span>
        </motion.div>

        {/* Progress ribbon — scrubber-driven */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-oatmeal-300">
          <motion.div
            className="h-full bg-sage-500 origin-left"
            style={{ scaleX: progress }}
          />
        </div>

        {/* Sage glow overlay */}
        <motion.div
          className="absolute inset-0 rounded-xl bg-sage-500/8 pointer-events-none"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 1.0, duration: 0.5 }}
        />
      </motion.div>

      {/* Format carousel — cycling badges */}
      <motion.div
        className="flex items-center gap-1.5 flex-wrap justify-center"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.8 }}
      >
        {FILE_FORMATS.map((fmt, i) => (
          <span
            key={fmt.ext}
            className={`
              px-2 py-0.5 rounded-sm text-[10px] font-mono font-medium transition-all duration-300
              ${i === formatIndex
                ? 'bg-sage-500/20 text-sage-700 scale-110 shadow-sm'
                : 'bg-obsidian-800/8 text-obsidian-400'
              }
            `}
          >
            {fmt.ext}
          </span>
        ))}
      </motion.div>

      {/* Speed indicator */}
      <motion.p
        className="text-[10px] font-mono text-obsidian-400 tracking-wider"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 1.2 }}
      >
        {'< 1 second'}
      </motion.p>
    </motion.div>
  )
}

// ── Analyze Layer ────────────────────────────────────────────────────

const PROCESSING_STEPS = [
  { label: 'Parsing file...', delay: 0.2 },
  { label: 'Classifying accounts...', delay: 0.5 },
  { label: 'Running 140+ tests...', delay: 0.8 },
  { label: 'Computing 17 ratios...', delay: 1.1 },
  { label: 'Generating diagnostics...', delay: 1.4 },
]

function AnalyzeLayer({ opacity }: { opacity: MotionValue<number> }) {
  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-4"
      style={{ opacity }}
    >
      {/* Sequential processing steps */}
      <div className="w-full max-w-[280px] space-y-2">
        {PROCESSING_STEPS.map((step, i) => (
          <motion.div
            key={step.label}
            className="flex items-center gap-2.5"
            initial={{ opacity: 0, x: -10 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: step.delay, duration: 0.3, ease: 'easeOut' as const }}
          >
            <motion.svg
              className="w-3.5 h-3.5 text-sage-600 shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              initial={{ opacity: 0, scale: 0 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: step.delay + 0.15, ...SPRING.snappy }}
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </motion.svg>
            <span className={`font-sans text-xs ${i < PROCESSING_STEPS.length - 1 ? 'text-obsidian-500' : 'text-obsidian-600 font-medium'}`}>
              {step.label}
            </span>
          </motion.div>
        ))}
      </div>

      {/* Progress bar */}
      <motion.div
        className="w-full max-w-[280px] h-1.5 rounded-full bg-obsidian-200/40 overflow-hidden"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.3, duration: 0.3 }}
      >
        <motion.div
          className="h-full bg-sage-500 rounded-full origin-left"
          initial={{ scaleX: 0 }}
          whileInView={{ scaleX: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3, duration: 1.5, ease: 'easeOut' as const }}
        />
      </motion.div>

      {/* Summary results */}
      <motion.div
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-sage-500/10 border border-sage-500/20"
        initial={{ opacity: 0, y: 6 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 1.7, duration: 0.4 }}
      >
        <span className="font-sans text-[10px] text-sage-700 font-medium">
          3 anomalies detected &middot; 17 ratios computed &middot; Report ready
        </span>
      </motion.div>
    </motion.div>
  )
}

// ── Export Layer ──────────────────────────────────────────────────────

const MEMO_STACK = [
  { title: 'JE Testing', standard: 'ISA 240', rotation: -6, offset: 0 },
  { title: 'Revenue', standard: 'PCAOB 2401', rotation: -3, offset: 1 },
  { title: 'Diagnostics', standard: 'ISA 520', rotation: 0, offset: 2 },
  { title: 'AP Testing', standard: 'ISA 500', rotation: 3, offset: 3 },
  { title: 'Sampling', standard: 'ISA 530', rotation: 6, offset: 4 },
]

function ExportLayer({ opacity }: { opacity: MotionValue<number> }) {
  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-5"
      style={{ opacity }}
    >
      {/* Fanned memo stack */}
      <div className="relative h-[88px] w-[280px] flex items-end justify-center mx-auto">
        {MEMO_STACK.map((memo, i) => (
          <motion.div
            key={memo.title}
            className="absolute w-[72px] h-[84px] rounded-md bg-white/80 border border-obsidian-200/40 shadow-sm flex flex-col items-center justify-center gap-0.5 px-1"
            style={{
              left: `calc(50% + ${(i - 2) * 40}px - 36px)`,
              zIndex: 5 - Math.abs(i - 2),
            }}
            initial={{ opacity: 0, y: 20, rotate: 0, scale: 0.9 }}
            whileInView={{
              opacity: 1,
              y: Math.abs(i - 2) * 4,
              rotate: memo.rotation,
              scale: 1,
            }}
            viewport={{ once: true }}
            transition={{
              delay: 0.2 + i * 0.08,
              duration: 0.4,
              ease: 'easeOut' as const,
            }}
          >
            <BrandIcon name="document-blank" className="w-4 h-4 text-clay-500/70" />
            <span className="font-sans text-[7px] font-medium text-obsidian-700 text-center leading-tight">
              {memo.title}
            </span>
            <span className="font-mono text-[6px] text-sage-600 font-medium">
              {memo.standard}
            </span>
          </motion.div>
        ))}
      </div>

      {/* Workpapers companion */}
      <motion.div
        className="flex items-center gap-3"
        initial={{ opacity: 0, y: 6 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.7, duration: 0.35 }}
      >
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-sage-500/10 border border-sage-500/20">
          <BrandIcon name="spreadsheet" className="w-3.5 h-3.5 text-sage-600" />
          <span className="font-mono text-[9px] text-sage-700 font-medium">XLSX Workpapers</span>
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-clay-500/8 border border-clay-500/15">
          <BrandIcon name="document-blank" className="w-3.5 h-3.5 text-clay-500" />
          <span className="font-mono text-[9px] text-clay-600 font-medium">17 PDF Memos</span>
        </div>
      </motion.div>

      {/* Download CTA */}
      <motion.div
        className="flex items-center gap-2"
        initial={{ opacity: 0, y: 4 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 1.0, ...SPRING.gentle }}
      >
        <BrandIcon name="download-arrow" className="w-4 h-4 text-sage-600" />
        <span className="text-sage-700 text-xs font-sans font-medium">
          Engagement file complete
        </span>
      </motion.div>
    </motion.div>
  )
}

// ── Stage Footer ─────────────────────────────────────────────────────

function StageFooter({ progress }: { progress: MotionValue<number> }) {
  return (
    <div className="px-4 py-2 border-t border-obsidian-500/30 bg-obsidian-800/40 flex items-center gap-3">
      <div className="flex-1 h-1 bg-obsidian-600/50 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-sage-500/60 rounded-full origin-left"
          style={{ scaleX: progress }}
        />
      </div>
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <BrandIcon name="padlock" className="w-3.5 h-3.5 text-sage-500" />
        <span className="text-oatmeal-600 text-[10px] font-sans font-medium">Zero-Storage</span>
      </div>
    </div>
  )
}

// ── Film Stage ───────────────────────────────────────────────────────

function FilmStage({
  uploadOpacity,
  analyzeOpacity,
  exportOpacity,
  uploadProgress,
  overallProgress,
  activeStep,
  isAutoPlaying,
  onToggleAutoPlay,
}: {
  uploadOpacity: MotionValue<number>
  analyzeOpacity: MotionValue<number>
  exportOpacity: MotionValue<number>
  uploadProgress: MotionValue<number>
  overallProgress: MotionValue<number>
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
          className="relative min-h-[280px] md:min-h-[260px] lg:min-h-[280px] bg-oatmeal-200"
          aria-label="Product workflow demonstration: upload, analyze, export"
          role="img"
        >
          <UploadLayer opacity={uploadOpacity} progress={uploadProgress} />
          <AnalyzeLayer opacity={analyzeOpacity} />
          <ExportLayer opacity={exportOpacity} />
        </div>

        {/* Caption — mobile-only subtitle (desktop shows in scrubber) */}
        <div className="px-5 pt-2 pb-1 sm:hidden">
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

        {/* Footer */}
        <StageFooter progress={overallProgress} />
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

              <div className="min-h-[280px] md:min-h-[260px] lg:min-h-[280px] bg-oatmeal-200 flex flex-col items-center justify-center gap-3 p-5">
                <div className="relative h-[88px] w-[280px] flex items-end justify-center mx-auto">
                  {MEMO_STACK.map((memo, i) => (
                    <div
                      key={memo.title}
                      className="absolute w-[72px] h-[84px] rounded-md bg-white/80 border border-obsidian-200/40 shadow-sm flex flex-col items-center justify-center gap-0.5 px-1"
                      style={{
                        left: `calc(50% + ${(i - 2) * 40}px - 36px)`,
                        zIndex: 5 - Math.abs(i - 2),
                        transform: `rotate(${memo.rotation}deg) translateY(${Math.abs(i - 2) * 4}px)`,
                      }}
                    >
                      <BrandIcon name="document-blank" className="w-4 h-4 text-clay-500/70" />
                      <span className="font-sans text-[7px] font-medium text-obsidian-700 text-center leading-tight">
                        {memo.title}
                      </span>
                      <span className="font-mono text-[6px] text-sage-600 font-medium">
                        {memo.standard}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-sage-500/10 border border-sage-500/20">
                    <BrandIcon name="spreadsheet" className="w-3.5 h-3.5 text-sage-600" />
                    <span className="font-mono text-[9px] text-sage-700 font-medium">XLSX Workpapers</span>
                  </div>
                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-clay-500/8 border border-clay-500/15">
                    <BrandIcon name="document-blank" className="w-3.5 h-3.5 text-clay-500" />
                    <span className="font-mono text-[9px] text-clay-600 font-medium">17 PDF Memos</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <BrandIcon name="download-arrow" className="w-4 h-4 text-sage-600" />
                  <span className="text-sage-700 text-xs font-sans font-medium">Engagement file complete</span>
                </div>
              </div>

              <div className="px-5 pt-2 pb-2">
                <p className="font-sans text-xs text-oatmeal-500">
                  {STEP_SUBTITLES.export}
                </p>
              </div>

              <div className="px-4 py-2 border-t border-obsidian-500/30 bg-obsidian-800/40 flex items-center gap-3">
                <div className="flex-1 h-1 bg-sage-500/60 rounded-full" />
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <BrandIcon name="padlock" className="w-3.5 h-3.5 text-sage-500" />
                  <span className="text-oatmeal-600 text-[10px] font-sans font-medium">Zero-Storage</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

// ── Main Export: HeroScrollSection ───────────────────────────────────

/**
 * HeroScrollSection — Sprint 449
 *
 * Interactive hero with user-controlled timeline scrubber.
 * Replaces the 300vh scroll-driven approach with a draggable
 * horizontal scrubber at the bottom of the hero viewport.
 *
 * Architecture:
 * - Single viewport-height section (no scroll runway)
 * - Three opacity layers driven by useMotionValue + useTransform
 * - Timeline scrubber with labeled stops (Upload, Analyze, Export)
 * - Draggable handle with click-to-snap on labels/track
 * - Spring-animated transitions between steps
 * - Left column: headline, trust indicators, CTAs
 * - Film stage panel: step indicator, crossfading subtitle, animated layers
 * - Reduced motion: renders static fallback (export state shown)
 *
 * Replaces scroll-based HeroScrollSection (Sprint 383).
 */
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
    uploadProgress,
    overallProgress,
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
            uploadProgress={uploadProgress}
            overallProgress={overallProgress}
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
