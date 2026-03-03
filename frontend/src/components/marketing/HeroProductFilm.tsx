'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import Link from 'next/link'
import {
  motion,
  useMotionValue,
  useTransform,
  AnimatePresence,
  MotionConfig,
  animate,
} from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { BrandIcon } from '@/components/shared'
import { useReducedMotion } from '@/hooks/useReducedMotion'
import { ANALYSIS_LABEL_SHORT } from '@/utils/constants'
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
  analyze: 7500,
  export: 4000,
}

/** Ordered auto-play cycle: upload → analyze → export → upload … */
const AUTO_CYCLE: FilmStep[] = ['upload', 'analyze', 'export']

// ── Phase Timer Hook ────────────────────────────────────────────────

/** Drives sequential animation phases. Resets on deactivation. */
function usePhaseTimer(isActive: boolean, delays: readonly number[]): number {
  const [phase, setPhase] = useState(0)
  const delaysRef = useRef(delays)
  delaysRef.current = delays

  useEffect(() => {
    if (!isActive) { setPhase(0); return }

    const timers: ReturnType<typeof setTimeout>[] = []
    delaysRef.current.forEach((delay, i) => {
      timers.push(setTimeout(() => setPhase(i + 1), delay))
    })
    return () => timers.forEach(clearTimeout)
  }, [isActive])

  return phase
}

// ── Counting Animation Hook ─────────────────────────────────────────

/** Animates a number from 0 to target using rAF with ease-out. */
function useCountAnimation(target: number, durationSec: number, isActive: boolean): number {
  const [count, setCount] = useState(0)

  useEffect(() => {
    if (!isActive) { setCount(0); return }

    const startTime = performance.now()
    let raf: number

    const tick = () => {
      const elapsed = performance.now() - startTime
      const progress = Math.min(elapsed / (durationSec * 1000), 1)
      const eased = 1 - Math.pow(1 - progress, 3) // ease-out cubic
      setCount(Math.round(eased * target))
      if (progress < 1) raf = requestAnimationFrame(tick)
    }

    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [isActive, target, durationSec])

  return count
}

// ── Cursor SVG ──────────────────────────────────────────────────────

function CursorIcon({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" stroke="none">
      <path d="M5 2L19 12L12 13L15 21L12 22L9 14L5 17V2Z" />
    </svg>
  )
}

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
      type: 'spring' as const,
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
      type: 'spring' as const,
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
          type: 'tween' as const,
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

// ── Upload Layer — Cursor + File Card ───────────────────────────────

const UPLOAD_PHASES = [0, 300, 1200, 1800, 2400] as const
const DATA_LINES = ['847 transactions', '62 accounts', 'FY 2025'] as const

function UploadLayer({ opacity, isActive }: { opacity: MotionValue<number>; isActive: boolean }) {
  const phase = usePhaseTimer(isActive, UPLOAD_PHASES)

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6"
      style={{ opacity }}
    >
      {/* Drop zone container */}
      <div className="relative w-full max-w-[280px]">
        {/* Drop zone target */}
        <motion.div
          className="relative flex flex-col items-center justify-center gap-2 py-8 px-6 rounded-xl border-2 border-dashed overflow-hidden"
          animate={
            phase >= 1 && phase < 3
              ? {
                  borderColor: [
                    'rgba(74,124,89,0.2)',
                    'rgba(74,124,89,0.6)',
                    'rgba(74,124,89,0.2)',
                  ],
                }
              : phase >= 3
                ? { borderColor: 'rgba(74,124,89,0.4)' }
                : { borderColor: 'rgba(74,124,89,0.15)' }
          }
          transition={
            phase >= 1 && phase < 3
              ? { duration: 1.5, repeat: Infinity, ease: 'easeInOut' as const }
              : { duration: 0.3 }
          }
        >
          {/* Sage glow pulse on drop */}
          {phase >= 3 && (
            <motion.div
              className="absolute inset-0 bg-sage-400/10 rounded-xl pointer-events-none"
              initial={{ opacity: 0 }}
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 0.5, ease: 'easeOut' as const }}
            />
          )}

          {/* Placeholder text before file arrives */}
          {phase < 3 && (
            <motion.div
              className="flex flex-col items-center gap-1"
              animate={phase >= 1 ? { opacity: 0.4 } : { opacity: 0.6 }}
            >
              <BrandIcon name="cloud-upload" className="w-8 h-8 text-obsidian-300" />
              <span className="font-sans text-xs text-obsidian-400">Drop your file here</span>
            </motion.div>
          )}

          {/* Settled file card (after drop) */}
          {phase >= 3 && (
            <motion.div
              className="flex items-center gap-3 px-4 py-3 rounded-lg bg-white border border-sage-400/40 shadow-sm w-full"
              initial={{ scale: 1.1, opacity: 0, y: -8 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              transition={SPRING.bouncy}
            >
              <BrandIcon name="file-plus" className="w-6 h-6 text-sage-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="font-mono text-xs text-obsidian-800 font-medium truncate">
                  Your_Company_FY2025.xlsx
                </p>
                <p className="font-mono text-[10px] text-obsidian-400">2.4 MB</p>
              </div>
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, ...SPRING.bouncy }}
              >
                <BrandIcon name="checkmark" className="w-4 h-4 text-sage-500" />
              </motion.div>
            </motion.div>
          )}
        </motion.div>

        {/* Animated cursor + file card (dragging phase) */}
        {phase >= 2 && phase < 3 && (
          <motion.div
            className="absolute pointer-events-none z-20"
            initial={{ x: -80, y: -60, opacity: 0 }}
            animate={{ x: 40, y: 30, opacity: 1 }}
            transition={{ duration: 0.8, ease: [0.25, 0.1, 0.25, 1] }}
          >
            <CursorIcon className="w-5 h-5 text-obsidian-600 drop-shadow-md" />
            <motion.div
              className="absolute top-3 left-4 flex items-center gap-2 px-3 py-2 rounded-lg bg-white border border-obsidian-200 shadow-lg whitespace-nowrap"
              initial={{ rotate: -6 }}
              animate={{ rotate: 0 }}
              transition={{ delay: 0.4, duration: 0.3 }}
            >
              <BrandIcon name="file-plus" className="w-4 h-4 text-sage-500 flex-shrink-0" />
              <span className="font-mono text-[10px] text-obsidian-700">FY2025.xlsx</span>
            </motion.div>
          </motion.div>
        )}
      </div>

      {/* Recognition — three data lines resolve sequentially */}
      <div className="flex flex-col items-center gap-1">
        {DATA_LINES.map((line, i) => (
          <motion.p
            key={line}
            className="font-mono text-sm font-medium text-obsidian-700"
            animate={phase >= 4 ? { opacity: 1, y: 0 } : { opacity: 0, y: 6 }}
            transition={{ delay: i * 0.15, duration: 0.25, ease: 'easeOut' as const }}
          >
            {line}
          </motion.p>
        ))}
      </div>

      {/* Format badges */}
      <motion.div
        className="flex items-center gap-2"
        animate={phase >= 5 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 0.3 }}
      >
        {FORMAT_BADGES.map((fmt, i) => (
          <span key={fmt}>
            <span className="font-mono text-[10px] text-sage-600/70 font-medium">
              {fmt}
            </span>
            {i < FORMAT_BADGES.length - 1 && (
              <span className="text-obsidian-300 ml-2">&middot;</span>
            )}
          </span>
        ))}
      </motion.div>

      {/* Speed indicator */}
      <motion.p
        className="font-mono text-[11px] text-sage-600 uppercase tracking-widest"
        animate={phase >= 5 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ delay: 0.15, duration: 0.3 }}
      >
        {ANALYSIS_LABEL_SHORT}
      </motion.p>
    </motion.div>
  )
}

// ── Analyze Layer — Scanning Matrix ─────────────────────────────────

const ANALYZE_PHASES = [0, 200, 600, 2800, 3400] as const

function AnalyzeLayer({ opacity, isActive }: { opacity: MotionValue<number>; isActive: boolean }) {
  const phase = usePhaseTimer(isActive, ANALYZE_PHASES)
  const testCount = useCountAnimation(108, 2.0, phase >= 3)

  // Pre-compute which tiles activate and their stagger indices
  const activatingTiles: number[] = []
  TOOL_TILES.forEach((tile, i) => {
    if (tile.activates) activatingTiles.push(i)
  })

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-4"
      style={{ opacity }}
    >
      {/* 4x3 tool grid with scan effect */}
      <div className="relative w-full max-w-[280px]">
        {/* Scanning line */}
        {phase >= 1 && phase < 4 && (
          <motion.div
            className="absolute top-0 bottom-0 w-0.5 bg-gradient-to-b from-transparent via-sage-400/60 to-transparent z-10 pointer-events-none"
            initial={{ left: 0 }}
            animate={{ left: '100%' }}
            transition={{ duration: 2.0, repeat: Infinity, ease: 'linear' }}
          />
        )}

        <div className="grid grid-cols-3 gap-1.5">
          {TOOL_TILES.map((tile, i) => {
            const activationIdx = activatingTiles.indexOf(i)
            const isActiveTile = tile.activates && phase >= 2
            const tileDelay = activationIdx >= 0 ? activationIdx * 0.15 : 0
            // Each tile needs ~0.15s stagger, 9 tiles = ~1.35s total
            const isComplete = tile.activates && phase >= 3

            if (tile.activates) {
              return (
                <motion.div
                  key={tile.name}
                  className="relative rounded-lg border bg-white px-1.5 py-2 flex flex-col items-center justify-center gap-1 overflow-hidden"
                  animate={
                    isComplete
                      ? { borderColor: 'rgba(74,124,89,0.5)', opacity: 1 }
                      : isActiveTile
                        ? { borderColor: 'rgba(74,124,89,0.3)', opacity: 1 }
                        : { borderColor: 'rgba(189,189,189,0.3)', opacity: 0.5 }
                  }
                  transition={{ delay: tileDelay, duration: 0.2 }}
                >
                  <span className="font-sans text-[9px] uppercase tracking-wider text-center leading-tight text-obsidian-700">
                    {tile.name}
                  </span>

                  {/* Mini progress bar → checkmark */}
                  <div className="w-full h-1 relative">
                    {isActiveTile && !isComplete && (
                      <motion.div
                        className="absolute inset-y-0 left-0 rounded-full bg-sage-400/60"
                        initial={{ width: '0%' }}
                        animate={{ width: '100%' }}
                        transition={{ delay: tileDelay, duration: 0.6, ease: 'easeOut' as const }}
                      />
                    )}
                    {isComplete && (
                      <motion.div
                        className="absolute inset-0 flex items-center justify-center"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: tileDelay + 0.1, ...SPRING.bouncy }}
                      >
                        <BrandIcon name="checkmark" className="w-3 h-3 text-sage-500" />
                      </motion.div>
                    )}
                  </div>

                  {/* Sage flash overlay on activation */}
                  {isActiveTile && (
                    <motion.div
                      className="absolute inset-0 bg-sage-400 pointer-events-none rounded-lg"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: [0, 0.12, 0] }}
                      transition={{ delay: tileDelay, duration: 0.3, ease: 'easeOut' as const }}
                    />
                  )}
                </motion.div>
              )
            }

            return (
              <div
                key={tile.name}
                className="rounded-lg border border-obsidian-200/30 bg-oatmeal-100/50 px-1.5 py-2 flex items-center justify-center opacity-30"
              >
                <span className="font-sans text-[9px] uppercase tracking-wider text-center leading-tight text-obsidian-400 line-through decoration-obsidian-200">
                  {tile.name}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Test counter */}
      <div className="flex items-center gap-2">
        <motion.p
          className="font-mono text-sm text-obsidian-700 font-medium tabular-nums"
          animate={phase >= 3 ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {testCount}/108 tests
        </motion.p>

        {/* Findings badge */}
        <motion.span
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-clay-50 border border-clay-200/50"
          animate={phase >= 4 ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.8 }}
          transition={SPRING.snappy}
        >
          <BrandIcon name="warning-triangle" className="w-3 h-3 text-clay-500" />
          <span className="font-sans text-[10px] font-medium text-clay-600">3 findings</span>
        </motion.span>
      </div>

      {/* Summary line */}
      <motion.p
        className="font-sans text-xs text-obsidian-500 text-center"
        animate={phase >= 5 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 0.3 }}
      >
        108 tests run across 9 tools &middot; 3 findings flagged
      </motion.p>
    </motion.div>
  )
}

// ── Export Layer — Progress Bar Download ─────────────────────────────

const EXPORT_PHASES = [0, 200, 500, 900, 2200, 2800] as const

function ExportLayer({ opacity, isActive }: { opacity: MotionValue<number>; isActive: boolean }) {
  const phase = usePhaseTimer(isActive, EXPORT_PHASES)
  const fileSize = useCountAnimation(2400, 1.2, phase >= 4)

  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-5"
      style={{ opacity }}
    >
      <div className="w-full max-w-[320px] flex flex-col gap-2.5">
        {/* Workpapers row — slides in from right */}
        <motion.div
          className="flex items-center gap-3 px-4 py-3 rounded-lg bg-white border border-obsidian-200/40 shadow-sm"
          animate={
            phase >= 1
              ? { x: 0, opacity: 1 }
              : { x: 50, opacity: 0 }
          }
          transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
        >
          <BrandIcon name="spreadsheet" className="w-5 h-5 text-sage-500 flex-shrink-0" />
          <span className="font-sans text-sm text-obsidian-800 font-medium flex-1 min-w-0 truncate">
            Your_Company_Workpapers.xlsx
          </span>
          <BrandIcon name="download-arrow" className="w-4 h-4 text-sage-500 flex-shrink-0" />
        </motion.div>

        {/* PDF memos row — slides in from right (staggered) */}
        <motion.div
          className="flex items-center gap-3 px-4 py-3 rounded-lg bg-white border border-obsidian-200/40 shadow-sm"
          animate={
            phase >= 2
              ? { x: 0, opacity: 1 }
              : { x: 50, opacity: 0 }
          }
          transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
        >
          <BrandIcon name="document-blank" className="w-5 h-5 text-obsidian-500 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <span className="font-sans text-sm text-obsidian-800 font-medium">
              17 PDF Memos
            </span>
            <p className="font-sans text-[11px] text-obsidian-400 truncate mt-0.5">
              JE Testing &middot; Revenue &middot; AP &middot; Sampling &middot; ...
            </p>
          </div>
          <BrandIcon name="download-arrow" className="w-4 h-4 text-sage-500 flex-shrink-0" />
        </motion.div>
      </div>

      {/* Download button with progress bar */}
      <div className="w-full max-w-[320px]">
        <motion.div
          className="relative w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg overflow-hidden"
          animate={
            phase >= 3
              ? { opacity: 1 }
              : { opacity: 0.5 }
          }
          transition={{ duration: 0.2 }}
        >
          {/* Background track */}
          <div className="absolute inset-0 bg-sage-100 rounded-lg" />

          {/* Progress fill */}
          <motion.div
            className="absolute inset-y-0 left-0 bg-sage-500 rounded-lg"
            initial={{ width: '0%' }}
            animate={phase >= 3 ? { width: '100%' } : { width: '0%' }}
            transition={
              phase >= 3
                ? { duration: 1.2, ease: [0.25, 0.1, 0.25, 1] }
                : { duration: 0 }
            }
          />

          {/* Button content */}
          <div className="relative z-10 flex items-center gap-2">
            {phase >= 5 ? (
              <motion.div
                initial={{ scale: 0, rotate: -90 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={SPRING.bouncy}
              >
                <BrandIcon name="checkmark" className="w-4 h-4 text-white" />
              </motion.div>
            ) : (
              <BrandIcon name="download-arrow" className="w-4 h-4 text-obsidian-700" />
            )}
            <span className={`font-sans text-sm font-medium transition-colors duration-300 ${
              phase >= 4 ? 'text-white' : 'text-obsidian-700'
            }`}>
              {phase >= 5 ? 'Download Complete' : 'Download Engagement File'}
            </span>
          </div>
        </motion.div>
      </div>

      {/* File size counter + checkmark */}
      <div className="flex items-center gap-3">
        <motion.p
          className="font-mono text-xs text-obsidian-500 tabular-nums"
          animate={phase >= 4 ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {(fileSize / 1000).toFixed(1)} MB
        </motion.p>

        {phase >= 5 && (
          <motion.div
            className="flex items-center gap-1"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={SPRING.bouncy}
          >
            <div className="w-1.5 h-1.5 rounded-full bg-sage-400" />
            <span className="font-sans text-[10px] text-sage-600 font-medium">Ready</span>
          </motion.div>
        )}
      </div>

      {/* Zero-storage whisper */}
      <motion.p
        className="font-sans text-[11px] text-obsidian-400 italic text-center"
        animate={phase >= 5 ? { opacity: 1 } : { opacity: 0 }}
        transition={{ delay: 0.3, duration: 0.4 }}
      >
        Processed in-memory and immediately destroyed. Raw financial data is never stored.
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
      <div className="rounded-2xl border border-obsidian-200/30 bg-white/90 backdrop-blur-xl overflow-hidden shadow-xl shadow-obsidian-200/20">
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

// ── Reduced Motion Fallback ──────────────────────────────────────────
// Kept for potential SSR/noscript use. The main HeroScrollSection always
// renders ScrubberHero, with MotionConfig handling reduced-motion gracefully.

function StaticFallback() {
  const { isAuthenticated } = useAuth()
  const mounted = useHasMounted()
  const [activeStep, setActiveStep] = useState<FilmStep>('export')

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

          {/* Static panel with step tabs */}
          <div className="w-full max-w-md mx-auto lg:max-w-none">
            <div className="rounded-2xl border border-obsidian-200/30 bg-white/90 backdrop-blur-xl overflow-hidden shadow-xl shadow-obsidian-200/20">
              {/* Tab navigation */}
              <div className="flex border-b border-obsidian-200/20">
                {STEPS.map((step) => (
                  <button
                    key={step}
                    onClick={() => setActiveStep(step)}
                    className={`flex-1 px-3 py-2.5 font-sans text-xs font-medium uppercase tracking-wider transition-colors ${
                      step === activeStep
                        ? 'text-obsidian-800 border-b-2 border-sage-500'
                        : 'text-obsidian-400 hover:text-obsidian-600'
                    }`}
                  >
                    {STEP_LABELS[step]}
                  </button>
                ))}
              </div>

              <div className="min-h-[280px] md:min-h-[260px] lg:min-h-[280px] bg-oatmeal-50 flex flex-col items-center justify-center gap-4 p-5">
                {activeStep === 'upload' && (
                  <div className="flex flex-col items-center gap-3">
                    <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-white border border-sage-400/40 shadow-sm">
                      <BrandIcon name="file-plus" className="w-6 h-6 text-sage-500" />
                      <div>
                        <p className="font-mono text-xs text-obsidian-800 font-medium">Your_Company_FY2025.xlsx</p>
                        <p className="font-mono text-[10px] text-obsidian-400">2.4 MB</p>
                      </div>
                      <BrandIcon name="checkmark" className="w-4 h-4 text-sage-500" />
                    </div>
                    <p className="font-mono text-sm text-obsidian-700">847 transactions &middot; 62 accounts &middot; FY 2025</p>
                  </div>
                )}

                {activeStep === 'analyze' && (
                  <div className="flex flex-col items-center gap-3">
                    <div className="grid grid-cols-3 gap-1.5 w-full max-w-[280px]">
                      {TOOL_TILES.slice(0, 9).map((tile) => (
                        <div
                          key={tile.name}
                          className={`rounded-lg border px-1.5 py-2 flex items-center justify-center ${
                            tile.activates
                              ? 'bg-white border-sage-400/50'
                              : 'bg-oatmeal-100/50 border-obsidian-200/30 opacity-30'
                          }`}
                        >
                          <span className="font-sans text-[9px] uppercase tracking-wider text-center leading-tight text-obsidian-700">
                            {tile.name}
                          </span>
                        </div>
                      ))}
                    </div>
                    <p className="font-sans text-xs text-obsidian-500">108 tests run across 9 tools &middot; 3 findings flagged</p>
                  </div>
                )}

                {activeStep === 'export' && (
                  <div className="flex flex-col items-center gap-3 w-full max-w-[320px]">
                    <div className="w-full flex flex-col gap-2.5">
                      <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-white border border-obsidian-200/40 shadow-sm">
                        <BrandIcon name="spreadsheet" className="w-5 h-5 text-sage-500 flex-shrink-0" />
                        <span className="font-sans text-sm text-obsidian-800 font-medium flex-1 min-w-0 truncate">
                          Your_Company_Workpapers.xlsx
                        </span>
                        <BrandIcon name="download-arrow" className="w-4 h-4 text-sage-500" />
                      </div>
                      <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-white border border-obsidian-200/40 shadow-sm">
                        <BrandIcon name="document-blank" className="w-5 h-5 text-obsidian-500 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <span className="font-sans text-sm text-obsidian-800 font-medium">17 PDF Memos</span>
                          <p className="font-sans text-[11px] text-obsidian-400 truncate mt-0.5">
                            JE Testing &middot; Revenue &middot; AP &middot; Sampling &middot; ...
                          </p>
                        </div>
                        <BrandIcon name="download-arrow" className="w-4 h-4 text-sage-500" />
                      </div>
                    </div>
                    <div className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-sage-500 text-white">
                      <BrandIcon name="download-arrow" className="w-4 h-4" />
                      <span className="font-sans text-sm font-medium">Download Engagement File</span>
                    </div>
                    <p className="font-sans text-[11px] text-obsidian-400 italic text-center">
                      Processed in-memory and immediately destroyed. Raw financial data is never stored.
                    </p>
                  </div>
                )}
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
  // Always render ScrubberHero — MotionConfig handles reduced-motion gracefully
  // by completing animations instantly instead of hiding the entire UI
  return (
    <MotionConfig reducedMotion="user">
      <ScrubberHero />
    </MotionConfig>
  )
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
