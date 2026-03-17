// Animation state machine: all useState/useEffect/useRef managing the film's animation lifecycle.
'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import {
  useMotionValue,
  useTransform,
  animate,
} from 'framer-motion'
import type { MotionValue } from 'framer-motion'

// ── Types ────────────────────────────────────────────────────────────

export type FilmStep = 'upload' | 'analyze' | 'export'

export const STEPS: FilmStep[] = ['upload', 'analyze', 'export']

export const STEP_LABELS: Record<FilmStep, string> = {
  upload: 'Drop your file',
  analyze: 'See the findings',
  export: 'Take the workpapers',
}

export const STEP_SUBTITLES: Record<FilmStep, string> = {
  upload: 'One gesture. Instant recognition.',
  analyze: '108 tests. Your file, read in full.',
  export: 'Complete engagement package. Yours alone.',
}

// Normalized positions for each step on the 0-1 timeline
export const STEP_POSITIONS: Record<FilmStep, number> = {
  upload: 0.0,
  analyze: 0.5,
  export: 1.0,
}

// ── Auto-play constants ──────────────────────────────────────────────

/** Per-step dwell times (ms) before sweeping to the next */
const DWELL_BY_STEP: Record<FilmStep, number> = {
  upload: 6000,
  analyze: 11000,
  export: 4000,
}

/** Ordered auto-play cycle: upload → analyze → export → upload … */
const AUTO_CYCLE: FilmStep[] = ['upload', 'analyze', 'export']

// ── Hydration guard ─────────────────────────────────────────────────

export function useHasMounted() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  return mounted
}

// ── Phase Timer Hook ────────────────────────────────────────────────

/** Drives sequential animation phases. Resets on deactivation. */
export function usePhaseTimer(isActive: boolean, delays: readonly number[]): number {
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
export function useCountAnimation(target: number, durationSec: number, isActive: boolean): number {
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

// ── useScrubberFilm Return Type ──────────────────────────────────────

export interface ScrubberFilmState {
  progress: MotionValue<number>
  uploadOpacity: MotionValue<number>
  analyzeOpacity: MotionValue<number>
  exportOpacity: MotionValue<number>
  activeStep: FilmStep
  goToStep: (step: FilmStep) => void
  scrubTo: (value: number) => void
  animateTo: (value: number) => void
  isAutoPlaying: boolean
  pauseAutoPlay: () => void
  toggleAutoPlay: () => void
}

// ── Step-change callback type ────────────────────────────────────────

export type OnStepChange = (step: FilmStep) => void

// ── useScrubberFilm Hook ─────────────────────────────────────────────

export function useScrubberFilm(onStepChange?: OnStepChange): ScrubberFilmState {
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
        onStepChange?.(step)
      }
    })
    return unsubscribe
  }, [progress, onStepChange])

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
