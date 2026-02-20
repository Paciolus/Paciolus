'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

/**
 * HeroProductFilm — Sprint 330
 *
 * Cinematic product narrative for the lobby hero. Auto-cycles through
 * Upload → Analyze → Export on a 4-second timer, pauses on hover.
 * Replaces decorative HeroVisualization with a "what this does" story.
 *
 * Glass-morphism panel, visible on all breakpoints.
 * Respects prefers-reduced-motion via MotionConfig in providers.tsx.
 */

type FilmStep = 'upload' | 'analyze' | 'export'

const STEPS: FilmStep[] = ['upload', 'analyze', 'export']
const STEP_DURATION = 4000

const STEP_LABELS: Record<FilmStep, string> = {
  upload: 'Upload',
  analyze: 'Analyze',
  export: 'Export',
}

const stepTransition = {
  enter: { opacity: 0, y: 12 },
  center: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
}

// ── Upload State ────────────────────────────────────────────────────

function UploadState() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 py-4">
      {/* Drop zone */}
      <motion.div
        className="w-full max-w-[260px] border-2 border-dashed border-oatmeal-400/30 rounded-xl p-6 flex flex-col items-center gap-3 relative overflow-hidden"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1, borderColor: 'rgba(74,124,89,0.4)' }}
        transition={{ duration: 1.5 }}
      >
        {/* File icon dropping in */}
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.8 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ delay: 0.3, type: 'spring' as const, stiffness: 200, damping: 18 }}
        >
          <svg className="w-10 h-10 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6" />
          </svg>
        </motion.div>

        {/* Filename */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
        >
          <p className="font-mono text-sm text-oatmeal-200">trial_balance_2025.csv</p>
          <motion.span
            className="font-mono text-xs text-oatmeal-500"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.9 }}
          >
            245 KB
          </motion.span>
        </motion.div>

        {/* Sage glow overlay on completion */}
        <motion.div
          className="absolute inset-0 rounded-xl bg-sage-500/5"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2, duration: 0.6 }}
        />
      </motion.div>

      <motion.p
        className="text-oatmeal-500 text-xs font-sans"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.0 }}
      >
        CSV or Excel — instantly parsed
      </motion.p>
    </div>
  )
}

// ── Analyze State ───────────────────────────────────────────────────

const CHART_BARS = [
  { height: 45, delay: 1.6 },
  { height: 70, delay: 1.7 },
  { height: 55, delay: 1.8 },
  { height: 85, delay: 1.9 },
  { height: 50, delay: 2.0 },
]

function AnalyzeState() {
  return (
    <div className="flex flex-col items-center gap-4 py-4">
      {/* Status indicator */}
      <div className="flex items-center gap-3">
        {/* Spinner → Checkmark */}
        <motion.div
          className="w-8 h-8 rounded-full flex items-center justify-center bg-sage-500/15"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <motion.div
            initial={{ opacity: 1 }}
            animate={{ opacity: 0 }}
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
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1.0, type: 'spring' as const, stiffness: 300 }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
          </motion.svg>
        </motion.div>

        <div>
          <motion.p
            className="font-sans text-sm font-medium"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, color: ['#EBE9E4', '#EBE9E4', '#8FBF9F'] }}
            transition={{ duration: 1.2, color: { delay: 0.8, duration: 0.3 } }}
          >
            <motion.span
              initial={{ opacity: 1 }}
              animate={{ opacity: 0 }}
              transition={{ delay: 0.8, duration: 0.15 }}
              className="absolute"
            >
              Analyzing...
            </motion.span>
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.95 }}
              className="text-sage-400"
            >
              Complete
            </motion.span>
          </motion.p>
          <motion.p
            className="text-oatmeal-500 text-xs font-sans"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.1 }}
          >
            47 accounts processed in 1.2s
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
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.0 + i * 0.15, duration: 0.3, ease: 'easeOut' as const }}
          >
            <p className={`font-mono text-lg font-bold tabular-nums ${metric.color}`}>{metric.value}</p>
            <p className="text-oatmeal-600 text-[10px] font-sans">{metric.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Mini bar chart */}
      <motion.div
        className="flex items-end gap-1.5 h-12 mt-1"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.4 }}
      >
        {CHART_BARS.map((bar, i) => (
          <motion.div
            key={i}
            className="w-3 rounded-t bg-gradient-to-t from-sage-600 to-sage-400"
            initial={{ height: 0 }}
            animate={{ height: `${bar.height}%` }}
            transition={{ delay: bar.delay, duration: 0.5, ease: 'easeOut' as const }}
          />
        ))}
      </motion.div>
    </div>
  )
}

// ── Export State ─────────────────────────────────────────────────────

function ExportState() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 py-4">
      {/* Document shapes */}
      <div className="relative h-24 w-48">
        {/* PDF doc */}
        <motion.div
          className="absolute left-4 top-0 w-20 h-24 rounded-lg bg-obsidian-700/60 border border-clay-500/30 flex flex-col items-center justify-center gap-1.5"
          initial={{ opacity: 0, x: -20, rotate: -4 }}
          animate={{ opacity: 1, x: 0, rotate: -4 }}
          transition={{ delay: 0.2, duration: 0.4, ease: 'easeOut' as const }}
        >
          <svg className="w-6 h-6 text-clay-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <span className="font-mono text-[9px] text-clay-400">PDF</span>
        </motion.div>

        {/* Excel doc */}
        <motion.div
          className="absolute right-4 top-2 w-20 h-24 rounded-lg bg-obsidian-700/60 border border-sage-500/30 flex flex-col items-center justify-center gap-1.5"
          initial={{ opacity: 0, x: 20, rotate: 3 }}
          animate={{ opacity: 1, x: 0, rotate: 3 }}
          transition={{ delay: 0.4, duration: 0.4, ease: 'easeOut' as const }}
        >
          <svg className="w-6 h-6 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <span className="font-mono text-[9px] text-sage-400">XLSX</span>
        </motion.div>
      </div>

      {/* Filenames */}
      <div className="flex flex-col items-center gap-1">
        <motion.p
          className="font-mono text-xs text-oatmeal-300"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
        >
          diagnostic_memo.pdf
        </motion.p>
        <motion.p
          className="font-mono text-xs text-oatmeal-500"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9 }}
        >
          workpapers_export.xlsx
        </motion.p>
      </div>

      {/* Download arrow with bounce */}
      <motion.div
        initial={{ opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.1, type: 'spring' as const, stiffness: 200, damping: 12 }}
      >
        <svg className="w-6 h-6 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      </motion.div>
    </div>
  )
}

// ── Main Component ──────────────────────────────────────────────────

const STEP_COMPONENTS: Record<FilmStep, React.ReactNode> = {
  upload: <UploadState />,
  analyze: <AnalyzeState />,
  export: <ExportState />,
}

export function HeroProductFilm() {
  const [activeStep, setActiveStep] = useState<FilmStep>('upload')
  const isPausedRef = useRef(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const advance = useCallback(() => {
    if (isPausedRef.current) return
    setActiveStep((prev) => {
      const idx = STEPS.indexOf(prev)
      const next = STEPS[(idx + 1) % STEPS.length]
      return next ?? 'upload'
    })
  }, [])

  useEffect(() => {
    intervalRef.current = setInterval(advance, STEP_DURATION)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [advance])

  return (
    <div
      className="w-full max-w-md mx-auto lg:max-w-none"
      onMouseEnter={() => { isPausedRef.current = true }}
      onMouseLeave={() => { isPausedRef.current = false }}
      aria-label="Product workflow demonstration: upload, analyze, export"
      role="img"
    >
      {/* Glass container */}
      <div className="rounded-2xl border border-obsidian-500/30 bg-obsidian-800/60 backdrop-blur-xl overflow-hidden shadow-2xl shadow-obsidian-900/50">
        {/* Panel header — step indicators + label */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-obsidian-500/30">
          {/* Step dots */}
          <div className="flex items-center gap-2">
            {STEPS.map((step) => (
              <button
                key={step}
                onClick={() => setActiveStep(step)}
                className={`w-2.5 h-2.5 rounded-full transition-colors duration-300 ${
                  step === activeStep
                    ? 'bg-sage-400'
                    : 'bg-obsidian-500/60 hover:bg-obsidian-400/60'
                }`}
                aria-label={`Go to ${STEP_LABELS[step]} step`}
              />
            ))}
          </div>

          {/* Current step label */}
          <span className="text-oatmeal-500 text-xs font-sans font-medium uppercase tracking-wider">
            {STEP_LABELS[activeStep]}
          </span>
        </div>

        {/* Step content */}
        <div className="px-4 py-2 min-h-[280px] md:min-h-[320px] lg:min-h-[380px] flex items-center justify-center">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeStep}
              variants={stepTransition}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3, ease: 'easeOut' as const }}
              className="w-full"
            >
              {STEP_COMPONENTS[activeStep]}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Panel footer — progress bar + Zero-Storage badge */}
        <div className="px-4 py-3 border-t border-obsidian-500/30 bg-obsidian-800/40 flex items-center gap-3">
          {/* Progress bar */}
          <div className="flex-1 h-1 bg-obsidian-600/50 rounded-full overflow-hidden">
            <motion.div
              key={activeStep}
              className="h-full bg-sage-500/60 rounded-full origin-left"
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: STEP_DURATION / 1000, ease: 'linear' }}
            />
          </div>

          {/* Zero-Storage badge */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <svg className="w-3.5 h-3.5 text-sage-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span className="text-oatmeal-600 text-[10px] font-sans font-medium">Zero-Storage</span>
          </div>
        </div>
      </div>
    </div>
  )
}
