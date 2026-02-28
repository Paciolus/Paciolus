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
  upload: 'Drop your trial balance. CSV, TSV, TXT, or Excel. Parsed in under a second.',
  analyze: '47 accounts. 12 ratios. 3 anomalies flagged. Zero data stored.',
  export: 'Audit-ready PDF memos and Excel workpapers. One-click download.',
}

// Normalized positions for each step on the 0-1 timeline
const STEP_POSITIONS: Record<FilmStep, number> = {
  upload: 0.0,
  analyze: 0.5,
  export: 1.0,
}

// ── useScrubberFilm Hook ─────────────────────────────────────────────

function useScrubberFilm() {
  const progress = useMotionValue(0)
  const [activeStep, setActiveStep] = useState<FilmStep>('upload')
  const lastStepRef = useRef<FilmStep>('upload')

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
  }
}

// ── Timeline Scrubber ────────────────────────────────────────────────

function TimelineScrubber({
  progress,
  activeStep,
  goToStep,
  scrubTo,
  animateTo,
}: {
  progress: MotionValue<number>
  activeStep: FilmStep
  goToStep: (step: FilmStep) => void
  scrubTo: (value: number) => void
  animateTo: (value: number) => void
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
    isDragging.current = true
    const value = getProgressFromEvent(e.clientX)
    scrubTo(value)
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
  }, [getProgressFromEvent, scrubTo])

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
    const value = getProgressFromEvent(e.clientX)
    animateTo(value)
  }, [getProgressFromEvent, animateTo])

  // Keyboard navigation for the slider
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    const step = 0.05
    if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
      e.preventDefault()
      animateTo(Math.min(1, progress.get() + step))
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
      e.preventDefault()
      animateTo(Math.max(0, progress.get() - step))
    } else if (e.key === 'Home') {
      e.preventDefault()
      animateTo(0)
    } else if (e.key === 'End') {
      e.preventDefault()
      animateTo(1)
    }
  }, [animateTo, progress])

  // Handle position driven by progress
  const handleX = useTransform(progress, (v) => `${v * 100}%`)

  // Filled track width
  const filledWidth = useTransform(progress, (v) => `${v * 100}%`)

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Step labels above the track */}
      <div className="relative flex justify-between mb-3 px-1">
        {STEPS.map((step) => {
          const isActive = step === activeStep
          const isPast = STEPS.indexOf(activeStep) > STEPS.indexOf(step)

          return (
            <button
              key={step}
              onClick={() => goToStep(step)}
              className="group relative flex flex-col items-center gap-1.5"
              aria-label={`Go to ${STEP_LABELS[step]} step`}
            >
              {/* Step dot */}
              <div className={`
                w-3 h-3 rounded-full border-2 transition-all duration-300
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

// ── Step Indicator ───────────────────────────────────────────────────

function StepIndicator({ activeStep }: { activeStep: FilmStep }) {
  return (
    <div className="flex items-center gap-3 mb-3">
      {STEPS.map((step, i) => {
        const isActive = step === activeStep
        const isPast = STEPS.indexOf(activeStep) > i
        return (
          <div key={step} className="flex items-center gap-3">
            {i > 0 && (
              <div
                className={`w-8 h-px transition-colors duration-500 ${
                  isPast ? 'bg-sage-400' : 'bg-obsidian-500/40'
                }`}
              />
            )}
            <div className="flex items-center gap-2">
              <div
                className={`w-2.5 h-2.5 rounded-full transition-all duration-500 ${
                  isActive
                    ? 'bg-sage-400 shadow-xs shadow-sage-400/50'
                    : isPast
                      ? 'bg-sage-500/60'
                      : 'bg-obsidian-500/40'
                }`}
              />
              <span
                className={`text-xs font-sans font-medium uppercase tracking-wider transition-colors duration-500 ${
                  isActive ? 'text-oatmeal-200' : 'text-oatmeal-600'
                }`}
              >
                {step}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── Left Column ──────────────────────────────────────────────────────

function LeftColumn() {
  const { isAuthenticated } = useAuth()
  const mounted = useHasMounted()

  return (
    <div className="flex flex-col justify-center editorial-hero">
      <motion.h1
        className="type-display-xl text-oatmeal-100 mb-6"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.7, delay: 0.15 }}
      >
        The Complete Audit
        <br />
        <span className="bg-gradient-to-r from-sage-400 via-sage-300 to-oatmeal-300 bg-clip-text text-transparent">
          Intelligence Suite
        </span>
      </motion.h1>

      {/* Trust indicators */}
      <motion.div
        className="flex items-center justify-center lg:justify-start gap-6 mb-10"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.7, delay: 0.45 }}
      >
        <div className="flex items-center gap-2 text-oatmeal-600">
          <BrandIcon name="shield-check" className="w-4 h-4 text-sage-500" />
          <span className="text-xs font-sans">ISA/PCAOB Standards</span>
        </div>
        <div className="w-px h-4 bg-obsidian-600" />
        <div className="flex items-center gap-2 text-oatmeal-600">
          <BrandIcon name="padlock" className="w-4 h-4 text-sage-500" />
          <span className="text-xs font-sans">Zero-Storage</span>
        </div>
        <div className="w-px h-4 bg-obsidian-600" />
        <div className="flex items-center gap-2 text-oatmeal-600">
          <span className="text-xs font-sans font-mono">12 Tools</span>
        </div>
      </motion.div>

      {/* CTAs */}
      <motion.div
        className="flex items-center justify-center lg:justify-start gap-4"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.7, delay: 0.7 }}
      >
        <Link
          href="/tools/trial-balance"
          className="group relative px-8 py-3.5 bg-sage-600 rounded-xl text-white font-sans font-medium hover:bg-sage-500 transition-all shadow-lg shadow-sage-600/25 hover:shadow-xl hover:shadow-sage-600/30"
          onClick={() => trackEvent('hero_cta_click', { cta: 'explore_tools' })}
        >
          <span className="relative z-10">Explore Our Tools</span>
        </Link>
        {mounted && !isAuthenticated && (
          <Link
            href="/register"
            className="px-8 py-3.5 bg-transparent border border-oatmeal-400/30 rounded-xl text-oatmeal-300 font-sans font-medium hover:border-oatmeal-400/50 hover:bg-oatmeal-200/5 transition-all"
            onClick={() => trackEvent('hero_cta_click', { cta: 'get_started' })}
          >
            Start Free Trial
          </Link>
        )}
      </motion.div>
    </div>
  )
}

// ── Upload Layer ─────────────────────────────────────────────────────

function UploadLayer({
  opacity,
  progress,
}: {
  opacity: MotionValue<number>
  progress: MotionValue<number>
}) {
  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-6"
      style={{ opacity }}
    >
      {/* Drop zone */}
      <motion.div
        className="w-full max-w-[260px] border-2 border-dashed border-obsidian-300/40 rounded-xl p-6 flex flex-col items-center gap-3 relative overflow-hidden"
        initial={{ opacity: 0, borderColor: 'rgba(33,33,33,0.2)' }}
        whileInView={{ opacity: 1, borderColor: 'rgba(74,124,89,0.5)' }}
        viewport={{ once: true }}
        transition={{ duration: 1.5 }}
      >
        {/* File icon */}
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.8 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3, ...SPRING.gentle }}
        >
          <BrandIcon name="file-plus" className="w-10 h-10 text-sage-600" />
        </motion.div>

        {/* Filename + size */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.7 }}
        >
          <p className="font-mono text-sm text-obsidian-700">trial_balance_2025.csv</p>
          <span className="font-mono text-xs text-obsidian-400">245 KB</span>
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
          transition={{ delay: 1.2, duration: 0.6 }}
        />
      </motion.div>

      {/* Column labels */}
      <motion.div
        className="flex gap-3"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 1.0 }}
      >
        {['Account', 'Debit', 'Credit'].map((col) => (
          <span
            key={col}
            className="px-2 py-0.5 bg-obsidian-800/10 rounded-sm text-obsidian-500 text-[10px] font-mono"
          >
            {col}
          </span>
        ))}
      </motion.div>
    </motion.div>
  )
}

// ── Analyze Layer ────────────────────────────────────────────────────

const CHART_BARS = [
  { height: 45, delay: 1.6 },
  { height: 70, delay: 1.7 },
  { height: 55, delay: 1.8 },
  { height: 85, delay: 1.9 },
  { height: 50, delay: 2.0 },
]

function AnalyzeLayer({ opacity }: { opacity: MotionValue<number> }) {
  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-6"
      style={{ opacity }}
    >
      {/* Status indicator */}
      <div className="flex items-center gap-3">
        <motion.div
          className="w-8 h-8 rounded-full flex items-center justify-center bg-sage-500/20"
          initial={{ scale: 0.8, opacity: 0 }}
          whileInView={{ scale: 1, opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.3 }}
        >
          <motion.div
            initial={{ opacity: 1 }}
            whileInView={{ opacity: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.8, duration: 0.2 }}
            className="absolute"
          >
            <div className="w-5 h-5 border-2 border-sage-600 border-t-transparent rounded-full animate-spin" />
          </motion.div>
          <motion.svg
            className="w-5 h-5 text-sage-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            initial={{ opacity: 0, scale: 0.5 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 1.0, ...SPRING.snappy }}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2.5}
              d="M5 13l4 4L19 7"
            />
          </motion.svg>
        </motion.div>

        <div>
          <motion.p
            className="font-sans text-sm font-medium"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1, color: ['#303030', '#303030', '#4A7C59'] }}
            viewport={{ once: true }}
            transition={{ duration: 1.2, color: { delay: 0.8, duration: 0.3 } }}
          >
            <motion.span
              initial={{ opacity: 1 }}
              whileInView={{ opacity: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.8, duration: 0.15 }}
              className="absolute"
            >
              Analyzing...
            </motion.span>
            <motion.span
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.95 }}
              className="text-sage-600"
            >
              Complete
            </motion.span>
          </motion.p>
          <motion.p
            className="text-obsidian-400 text-xs font-sans"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 1.1 }}
          >
            47 accounts processed
          </motion.p>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-3 gap-2.5 w-full max-w-[300px]">
        {[
          { label: 'Current Ratio', value: '1.82', color: 'text-sage-600' },
          { label: 'Accounts', value: '47', color: 'text-obsidian-700' },
          { label: 'Anomalies', value: '3', color: 'text-clay-500' },
        ].map((metric, i) => (
          <motion.div
            key={metric.label}
            className="p-2.5 rounded-lg bg-white/60 border border-obsidian-200/40 text-center"
            initial={{ opacity: 0, y: 8 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 1.0 + i * 0.15, duration: 0.3, ease: 'easeOut' as const }}
          >
            <p className={`font-mono text-lg font-bold tabular-nums ${metric.color}`}>
              {metric.value}
            </p>
            <p className="text-obsidian-400 text-[10px] font-sans">{metric.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Mini bar chart */}
      <motion.div
        className="flex items-end gap-1.5 h-12 mt-1"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 1.4 }}
      >
        {CHART_BARS.map((bar, i) => (
          <motion.div
            key={i}
            className="w-3 rounded-t bg-gradient-to-t from-sage-600 to-sage-400"
            initial={{ height: 0 }}
            whileInView={{ height: `${bar.height}%` }}
            viewport={{ once: true }}
            transition={{ delay: bar.delay, duration: 0.5, ease: 'easeOut' as const }}
          />
        ))}
      </motion.div>
    </motion.div>
  )
}

// ── Export Layer ──────────────────────────────────────────────────────

function ExportLayer({ opacity }: { opacity: MotionValue<number> }) {
  return (
    <motion.div
      className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-6"
      style={{ opacity }}
    >
      {/* Document shapes */}
      <div className="relative h-24 w-48">
        <motion.div
          className="absolute left-4 top-0 w-20 h-24 rounded-lg bg-white/70 border border-clay-400/30 flex flex-col items-center justify-center gap-1.5 shadow-sm"
          initial={{ opacity: 0, x: -20, rotate: -4 }}
          whileInView={{ opacity: 1, x: 0, rotate: -4 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2, duration: 0.4, ease: 'easeOut' as const }}
        >
          <BrandIcon name="document-blank" className="w-6 h-6 text-clay-500" />
          <span className="font-mono text-[9px] text-clay-500">PDF</span>
        </motion.div>

        <motion.div
          className="absolute right-4 top-2 w-20 h-24 rounded-lg bg-white/70 border border-sage-500/30 flex flex-col items-center justify-center gap-1.5 shadow-sm"
          initial={{ opacity: 0, x: 20, rotate: 3 }}
          whileInView={{ opacity: 1, x: 0, rotate: 3 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4, duration: 0.4, ease: 'easeOut' as const }}
        >
          <BrandIcon name="spreadsheet" className="w-6 h-6 text-sage-600" />
          <span className="font-mono text-[9px] text-sage-600">XLSX</span>
        </motion.div>
      </div>

      {/* Filenames */}
      <div className="flex flex-col items-center gap-1">
        <motion.p
          className="font-mono text-xs text-obsidian-700"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.7 }}
        >
          diagnostic_memo.pdf
        </motion.p>
        <motion.p
          className="font-mono text-xs text-obsidian-400"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.9 }}
        >
          workpapers_export.xlsx
        </motion.p>
      </div>

      {/* Download arrow */}
      <motion.div
        initial={{ opacity: 0, y: -6 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 1.1, ...SPRING.gentle }}
      >
        <motion.p
          className="text-sage-600 text-xs font-sans font-medium mb-1 text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 1.3 }}
        >
          Ready for workpapers
        </motion.p>
        <div className="flex justify-center">
          <BrandIcon name="download-arrow" className="w-6 h-6 text-sage-600" />
        </div>
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
}: {
  uploadOpacity: MotionValue<number>
  analyzeOpacity: MotionValue<number>
  exportOpacity: MotionValue<number>
  uploadProgress: MotionValue<number>
  overallProgress: MotionValue<number>
  activeStep: FilmStep
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
          <span className="text-oatmeal-500 text-xs font-sans font-medium uppercase tracking-wider">
            Paciolus
          </span>
        </div>

        {/* Layer container */}
        <div
          className="relative min-h-[220px] md:min-h-[240px] lg:min-h-[260px] bg-oatmeal-200"
          aria-label="Product workflow demonstration: upload, analyze, export"
          role="img"
        >
          <UploadLayer opacity={uploadOpacity} progress={uploadProgress} />
          <AnalyzeLayer opacity={analyzeOpacity} />
          <ExportLayer opacity={exportOpacity} />
        </div>

        {/* Caption */}
        <div className="px-5 pt-2 pb-1">
          <StepIndicator activeStep={activeStep} />
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
            <h1 className="type-display-xl text-oatmeal-100 mb-6">
              The Complete Audit
              <br />
              <span className="bg-gradient-to-r from-sage-400 via-sage-300 to-oatmeal-300 bg-clip-text text-transparent">
                Intelligence Suite
              </span>
            </h1>

            <div className="flex items-center justify-center lg:justify-start gap-6 mb-10">
              <div className="flex items-center gap-2 text-oatmeal-600">
                <BrandIcon name="shield-check" className="w-4 h-4 text-sage-500" />
                <span className="text-xs font-sans">ISA/PCAOB Standards</span>
              </div>
              <div className="w-px h-4 bg-obsidian-600" />
              <div className="flex items-center gap-2 text-oatmeal-600">
                <BrandIcon name="padlock" className="w-4 h-4 text-sage-500" />
                <span className="text-xs font-sans">Zero-Storage</span>
              </div>
              <div className="w-px h-4 bg-obsidian-600" />
              <div className="flex items-center gap-2 text-oatmeal-600">
                <span className="text-xs font-sans font-mono">12 Tools</span>
              </div>
            </div>

            <div className="flex items-center justify-center lg:justify-start gap-4">
              <Link
                href="/tools/trial-balance"
                className="group relative px-8 py-3.5 bg-sage-600 rounded-xl text-white font-sans font-medium hover:bg-sage-500 transition-all shadow-lg shadow-sage-600/25 hover:shadow-xl hover:shadow-sage-600/30"
                onClick={() => trackEvent('hero_cta_click', { cta: 'explore_tools' })}
              >
                <span className="relative z-10">Explore Our Tools</span>
              </Link>
              {mounted && !isAuthenticated && (
                <Link
                  href="/register"
                  className="px-8 py-3.5 bg-transparent border border-oatmeal-400/30 rounded-xl text-oatmeal-300 font-sans font-medium hover:border-oatmeal-400/50 hover:bg-oatmeal-200/5 transition-all"
                  onClick={() => trackEvent('hero_cta_click', { cta: 'get_started' })}
                >
                  Start Free Trial
                </Link>
              )}
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

              <div className="min-h-[220px] md:min-h-[240px] lg:min-h-[260px] bg-oatmeal-200 flex flex-col items-center justify-center gap-4 p-6">
                <div className="relative h-24 w-48">
                  <div className="absolute left-4 top-0 w-20 h-24 rounded-lg bg-white/70 border border-clay-400/30 flex flex-col items-center justify-center gap-1.5 shadow-sm -rotate-[4deg]">
                    <BrandIcon name="document-blank" className="w-6 h-6 text-clay-500" />
                    <span className="font-mono text-[9px] text-clay-500">PDF</span>
                  </div>
                  <div className="absolute right-4 top-2 w-20 h-24 rounded-lg bg-white/70 border border-sage-500/30 flex flex-col items-center justify-center gap-1.5 shadow-sm rotate-[3deg]">
                    <BrandIcon name="spreadsheet" className="w-6 h-6 text-sage-600" />
                    <span className="font-mono text-[9px] text-sage-600">XLSX</span>
                  </div>
                </div>
                <div className="flex flex-col items-center gap-1">
                  <p className="font-mono text-xs text-obsidian-700">diagnostic_memo.pdf</p>
                  <p className="font-mono text-xs text-obsidian-400">workpapers_export.xlsx</p>
                </div>
                <p className="text-sage-600 text-xs font-sans font-medium">Ready for workpapers</p>
              </div>

              <div className="px-5 pt-2 pb-1">
                <StepIndicator activeStep="export" />
                <p className="font-sans text-sm italic text-oatmeal-400">
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
          />
        </div>

        {/* Timeline Scrubber — user-controlled */}
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
          />
        </motion.div>
      </div>
    </section>
  )
}

/** @deprecated Use HeroScrollSection instead */
export const HeroProductFilm = HeroScrollSection
