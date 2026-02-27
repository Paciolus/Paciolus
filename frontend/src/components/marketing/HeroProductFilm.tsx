'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import {
  motion,
  useScroll,
  useTransform,
  useMotionValueEvent,
  AnimatePresence,
} from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { BrandIcon } from '@/components/shared'
import { useReducedMotion } from '@/hooks/useReducedMotion'
import { trackEvent } from '@/utils/telemetry'
import { SPRING } from '@/utils/themeUtils'
import type { MotionValue } from 'framer-motion'

// ── Hydration guard ─────────────────────────────────────────────────
// Auth state is client-only (localStorage). Defer auth-dependent UI
// until after hydration to prevent server/client HTML mismatch.
function useHasMounted() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  return mounted
}

// ── Types ────────────────────────────────────────────────────────────

type FilmStep = 'upload' | 'analyze' | 'export'

const STEPS: FilmStep[] = ['upload', 'analyze', 'export']

const STEP_SUBTITLES: Record<FilmStep, string> = {
  upload: 'Drop your trial balance. CSV, TSV, TXT, or Excel. Parsed in under a second.',
  analyze: '47 accounts. 12 ratios. 3 anomalies flagged. Zero data stored.',
  export: 'Audit-ready PDF memos and Excel workpapers. One-click download.',
}

// ── useScrollFilm Hook ───────────────────────────────────────────────

interface ScrollFilmReturn {
  containerRef: React.RefObject<HTMLDivElement | null>
  scrollYProgress: MotionValue<number>
  uploadOpacity: MotionValue<number>
  analyzeOpacity: MotionValue<number>
  exportOpacity: MotionValue<number>
  uploadProgress: MotionValue<number>
  overallProgress: MotionValue<number>
  activeStep: FilmStep
}

function useScrollFilm(): ScrollFilmReturn {
  const containerRef = useRef<HTMLDivElement>(null)
  const [activeStep, setActiveStep] = useState<FilmStep>('upload')
  const scrollStartedRef = useRef(false)
  const lastStepRef = useRef<FilmStep>('upload')

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  })

  // Three crossfading opacity transforms with 10% overlap windows
  const uploadOpacity = useTransform(scrollYProgress, [0, 0.28, 0.38], [1, 1, 0])
  const analyzeOpacity = useTransform(scrollYProgress, [0.28, 0.38, 0.58, 0.68], [0, 1, 1, 0])
  const exportOpacity = useTransform(scrollYProgress, [0.58, 0.68, 1.0], [0, 1, 1])

  // Upload progress bar driven by scroll
  const uploadProgress = useTransform(scrollYProgress, [0.05, 0.25], [0, 1])

  // Overall footer progress bar
  const overallProgress = useTransform(scrollYProgress, [0, 1], [0, 1])

  // Track active step for left-column indicator + analytics
  useMotionValueEvent(scrollYProgress, 'change', (v) => {
    // Scroll start event — fire once
    if (!scrollStartedRef.current && v > 0.02) {
      scrollStartedRef.current = true
      trackEvent('hero_scroll_start')
    }

    // Determine active step from scroll position
    let step: FilmStep = 'upload'
    if (v >= 0.58) step = 'export'
    else if (v >= 0.28) step = 'analyze'

    if (step !== lastStepRef.current) {
      lastStepRef.current = step
      setActiveStep(step)
      trackEvent('hero_step_reached', { step })
    }
  })

  return {
    containerRef,
    scrollYProgress,
    uploadOpacity,
    analyzeOpacity,
    exportOpacity,
    uploadProgress,
    overallProgress,
    activeStep,
  }
}

// ── Step Indicator ───────────────────────────────────────────────────

function StepIndicator({ activeStep }: { activeStep: FilmStep }) {
  return (
    <div className="flex items-center gap-3 mb-6">
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

// ── Scroll Caption (above FilmStage) ─────────────────────────────────

function ScrollCaption({ activeStep }: { activeStep: FilmStep }) {
  return (
    <div className="mb-4">
      {/* Step indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <StepIndicator activeStep={activeStep} />
      </motion.div>

      {/* Crossfading subtitle */}
      <div className="h-12 relative">
        <AnimatePresence mode="wait">
          <motion.p
            key={activeStep}
            className="type-body text-oatmeal-400 max-w-md absolute inset-0"
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
        className="w-full max-w-[260px] border-2 border-dashed border-oatmeal-400/30 rounded-xl p-6 flex flex-col items-center gap-3 relative overflow-hidden"
        initial={{ opacity: 0, borderColor: 'rgba(235,233,228,0.15)' }}
        whileInView={{ opacity: 1, borderColor: 'rgba(74,124,89,0.4)' }}
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
          <BrandIcon name="file-plus" className="w-10 h-10 text-sage-400" />
        </motion.div>

        {/* Filename + size */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.7 }}
        >
          <p className="font-mono text-sm text-oatmeal-200">trial_balance_2025.csv</p>
          <span className="font-mono text-xs text-oatmeal-500">245 KB</span>
        </motion.div>

        {/* Progress ribbon — scroll-driven */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-obsidian-600/50">
          <motion.div
            className="h-full bg-sage-500/70 origin-left"
            style={{ scaleX: progress }}
          />
        </div>

        {/* Sage glow overlay on completion */}
        <motion.div
          className="absolute inset-0 rounded-xl bg-sage-500/5 pointer-events-none"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 1.2, duration: 0.6 }}
        />
      </motion.div>

      {/* Column labels — appear after upload completes */}
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
            className="px-2 py-0.5 bg-obsidian-700/40 rounded-sm text-oatmeal-500 text-[10px] font-mono"
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
      {/* Status indicator: spinner → check */}
      <div className="flex items-center gap-3">
        <motion.div
          className="w-8 h-8 rounded-full flex items-center justify-center bg-sage-500/15"
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
            <div className="w-5 h-5 border-2 border-sage-400 border-t-transparent rounded-full animate-spin" />
          </motion.div>
          <motion.svg
            className="w-5 h-5 text-sage-400"
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
            whileInView={{ opacity: 1, color: ['#EBE9E4', '#EBE9E4', '#8FBF9F'] }}
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
              className="text-sage-400"
            >
              Complete
            </motion.span>
          </motion.p>
          <motion.p
            className="text-oatmeal-500 text-xs font-sans"
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
          { label: 'Current Ratio', value: '1.82', color: 'text-sage-400' },
          { label: 'Accounts', value: '47', color: 'text-oatmeal-300' },
          { label: 'Anomalies', value: '3', color: 'text-clay-400' },
        ].map((metric, i) => (
          <motion.div
            key={metric.label}
            className="p-2.5 rounded-lg bg-obsidian-700/50 border border-obsidian-500/30 text-center"
            initial={{ opacity: 0, y: 8 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 1.0 + i * 0.15, duration: 0.3, ease: 'easeOut' as const }}
          >
            <p className={`font-mono text-lg font-bold tabular-nums ${metric.color}`}>
              {metric.value}
            </p>
            <p className="text-oatmeal-600 text-[10px] font-sans">{metric.label}</p>
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
        {/* PDF doc */}
        <motion.div
          className="absolute left-4 top-0 w-20 h-24 rounded-lg bg-obsidian-700/60 border border-clay-500/30 flex flex-col items-center justify-center gap-1.5"
          initial={{ opacity: 0, x: -20, rotate: -4 }}
          whileInView={{ opacity: 1, x: 0, rotate: -4 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2, duration: 0.4, ease: 'easeOut' as const }}
        >
          <BrandIcon name="document-blank" className="w-6 h-6 text-clay-400" />
          <span className="font-mono text-[9px] text-clay-400">PDF</span>
        </motion.div>

        {/* Excel doc */}
        <motion.div
          className="absolute right-4 top-2 w-20 h-24 rounded-lg bg-obsidian-700/60 border border-sage-500/30 flex flex-col items-center justify-center gap-1.5"
          initial={{ opacity: 0, x: 20, rotate: 3 }}
          whileInView={{ opacity: 1, x: 0, rotate: 3 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4, duration: 0.4, ease: 'easeOut' as const }}
        >
          <BrandIcon name="spreadsheet" className="w-6 h-6 text-sage-400" />
          <span className="font-mono text-[9px] text-sage-400">XLSX</span>
        </motion.div>
      </div>

      {/* Filenames */}
      <div className="flex flex-col items-center gap-1">
        <motion.p
          className="font-mono text-xs text-oatmeal-300"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.7 }}
        >
          diagnostic_memo.pdf
        </motion.p>
        <motion.p
          className="font-mono text-xs text-oatmeal-500"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.9 }}
        >
          workpapers_export.xlsx
        </motion.p>
      </div>

      {/* Download arrow with bounce */}
      <motion.div
        initial={{ opacity: 0, y: -6 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 1.1, ...SPRING.gentle }}
      >
        <motion.p
          className="text-sage-400 text-xs font-sans font-medium mb-1 text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 1.3 }}
        >
          Ready for workpapers
        </motion.p>
        <div className="flex justify-center">
          <BrandIcon name="download-arrow" className="w-6 h-6 text-sage-400" />
        </div>
      </motion.div>
    </motion.div>
  )
}

// ── Stage Footer ─────────────────────────────────────────────────────

function StageFooter({ progress }: { progress: MotionValue<number> }) {
  return (
    <div className="px-4 py-3 border-t border-obsidian-500/30 bg-obsidian-800/40 flex items-center gap-3">
      {/* Scroll-driven progress bar */}
      <div className="flex-1 h-1 bg-obsidian-600/50 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-sage-500/60 rounded-full origin-left"
          style={{ scaleX: progress }}
        />
      </div>

      {/* Zero-Storage badge */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <BrandIcon name="padlock" className="w-3.5 h-3.5 text-sage-500" />
        <span className="text-oatmeal-600 text-[10px] font-sans font-medium">Zero-Storage</span>
      </div>
    </div>
  )
}

// ── Film Stage (Glass Panel) ─────────────────────────────────────────

function FilmStage({
  uploadOpacity,
  analyzeOpacity,
  exportOpacity,
  uploadProgress,
  overallProgress,
}: {
  uploadOpacity: MotionValue<number>
  analyzeOpacity: MotionValue<number>
  exportOpacity: MotionValue<number>
  uploadProgress: MotionValue<number>
  overallProgress: MotionValue<number>
}) {
  return (
    <div className="w-full max-w-md mx-auto lg:max-w-none">
      <div className="rounded-2xl border border-obsidian-500/30 bg-obsidian-800/60 backdrop-blur-xl overflow-hidden shadow-2xl shadow-obsidian-900/50">
        {/* Panel header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-obsidian-500/30">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-clay-400/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-oatmeal-500/40" />
            <div className="w-2.5 h-2.5 rounded-full bg-sage-400/60" />
          </div>
          <span className="text-oatmeal-500 text-xs font-sans font-medium uppercase tracking-wider">
            Paciolus
          </span>
        </div>

        {/* Layer container — all three rendered simultaneously */}
        <div
          className="relative min-h-[280px] md:min-h-[320px] lg:min-h-[380px]"
          aria-label="Product workflow demonstration: upload, analyze, export"
          role="img"
        >
          <UploadLayer opacity={uploadOpacity} progress={uploadProgress} />
          <AnalyzeLayer opacity={analyzeOpacity} />
          <ExportLayer opacity={exportOpacity} />
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
          {/* Left — static headline */}
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

          {/* Right — static export state */}
          <div className="w-full max-w-md mx-auto lg:max-w-none">
            {/* Static subtitle above panel */}
            <p className="type-body text-oatmeal-400 max-w-md mb-4">
              {STEP_SUBTITLES.export}
            </p>
            <div className="rounded-2xl border border-obsidian-500/30 bg-obsidian-800/60 backdrop-blur-xl overflow-hidden shadow-2xl shadow-obsidian-900/50">
              <div className="flex items-center justify-between px-4 py-3 border-b border-obsidian-500/30">
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-clay-400/60" />
                  <div className="w-2.5 h-2.5 rounded-full bg-oatmeal-500/40" />
                  <div className="w-2.5 h-2.5 rounded-full bg-sage-400/60" />
                </div>
                <span className="text-oatmeal-500 text-xs font-sans font-medium uppercase tracking-wider">
                  Paciolus
                </span>
              </div>
              <div className="min-h-[280px] md:min-h-[320px] lg:min-h-[380px] flex flex-col items-center justify-center gap-4 p-6">
                {/* Static export state */}
                <div className="relative h-24 w-48">
                  <div className="absolute left-4 top-0 w-20 h-24 rounded-lg bg-obsidian-700/60 border border-clay-500/30 flex flex-col items-center justify-center gap-1.5 -rotate-[4deg]">
                    <BrandIcon name="document-blank" className="w-6 h-6 text-clay-400" />
                    <span className="font-mono text-[9px] text-clay-400">PDF</span>
                  </div>
                  <div className="absolute right-4 top-2 w-20 h-24 rounded-lg bg-obsidian-700/60 border border-sage-500/30 flex flex-col items-center justify-center gap-1.5 rotate-[3deg]">
                    <BrandIcon name="spreadsheet" className="w-6 h-6 text-sage-400" />
                    <span className="font-mono text-[9px] text-sage-400">XLSX</span>
                  </div>
                </div>
                <div className="flex flex-col items-center gap-1">
                  <p className="font-mono text-xs text-oatmeal-300">diagnostic_memo.pdf</p>
                  <p className="font-mono text-xs text-oatmeal-500">workpapers_export.xlsx</p>
                </div>
                <p className="text-sage-400 text-xs font-sans font-medium">Ready for workpapers</p>
              </div>
              <div className="px-4 py-3 border-t border-obsidian-500/30 bg-obsidian-800/40 flex items-center gap-3">
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
 * HeroScrollSection — Sprint 383
 *
 * Scroll-linked cinematic product film for the homepage hero.
 * User scrolls through a 300vh section; a sticky visual stage
 * progressively crossfades Upload → Analyze → Export steps.
 *
 * Architecture:
 * - 300vh scroll runway (250vh on mobile) with sticky inner viewport
 * - Three opacity layers driven by framer-motion useTransform (60fps, no React re-renders)
 * - Event-triggered spring animations fire once per layer via whileInView
 * - Left column: headline, step indicator, crossfading subtitle, CTAs
 * - Reduced motion: renders static fallback (no scroll container, export state shown)
 *
 * Replaces timer-based HeroProductFilm (Sprint 330).
 */
export function HeroScrollSection() {
  const { prefersReducedMotion } = useReducedMotion()

  if (prefersReducedMotion) {
    return <StaticFallback />
  }

  return <ScrollHero />
}

function ScrollHero() {
  const {
    containerRef,
    uploadOpacity,
    analyzeOpacity,
    exportOpacity,
    uploadProgress,
    overallProgress,
    activeStep,
  } = useScrollFilm()

  return (
    <div
      ref={containerRef as React.RefObject<HTMLDivElement>}
      className="relative z-10 h-[250vh] lg:h-[300vh]"
      role="region"
      aria-label="Product demonstration"
    >
      <div className="sticky top-0 h-screen flex items-center pt-16 px-6">
        <div className="max-w-7xl mx-auto w-full">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-8 items-center">
            <LeftColumn />
            <div>
              <ScrollCaption activeStep={activeStep} />
              <FilmStage
                uploadOpacity={uploadOpacity}
                analyzeOpacity={analyzeOpacity}
                exportOpacity={exportOpacity}
                uploadProgress={uploadProgress}
                overallProgress={overallProgress}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/** @deprecated Use HeroScrollSection instead */
export const HeroProductFilm = HeroScrollSection
