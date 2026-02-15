'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Image from 'next/image'

interface VaultTransitionProps {
  userName?: string | null
  onComplete: () => void
}

/**
 * VaultTransition — "The Vault Crack"
 *
 * A 4-phase light-leak transition that plays on successful login:
 *   Phase 1 (0-300ms):   Form fades out (opacity)
 *   Phase 2 (300-800ms): Horizontal light-leak expands from center
 *   Phase 3 (800-1800ms): Welcome screen — logo, name, date
 *   Phase 4 (1800-2200ms): Fade out to reveal target page
 *
 * Skippable: click or keypress instantly completes.
 * prefers-reduced-motion: skips animation entirely.
 */
export default function VaultTransition({ userName, onComplete }: VaultTransitionProps) {
  const [phase, setPhase] = useState<1 | 2 | 3 | 4>(1)
  const [skipped, setSkipped] = useState(false)

  // Check reduced motion preference
  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  // Skip handler — click or keypress
  const handleSkip = useCallback(() => {
    if (!skipped) {
      setSkipped(true)
      onComplete()
    }
  }, [skipped, onComplete])

  // Keyboard skip
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Any key skips
      if (e.key) handleSkip()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [handleSkip])

  // If reduced motion, skip immediately
  useEffect(() => {
    if (prefersReducedMotion) {
      onComplete()
    }
  }, [prefersReducedMotion, onComplete])

  // Phase timeline
  useEffect(() => {
    if (prefersReducedMotion || skipped) return

    const timers: ReturnType<typeof setTimeout>[] = []

    // Phase 2: Light-leak begins
    timers.push(setTimeout(() => setPhase(2), 300))

    // Phase 3: Welcome screen
    timers.push(setTimeout(() => setPhase(3), 800))

    // Phase 4: Fade out
    timers.push(setTimeout(() => setPhase(4), 1800))

    // Complete
    timers.push(setTimeout(() => {
      if (!skipped) onComplete()
    }, 2200))

    return () => timers.forEach(clearTimeout)
  }, [prefersReducedMotion, skipped, onComplete])

  if (prefersReducedMotion) return null

  const displayName = userName || 'Auditor'
  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return (
    <AnimatePresence>
      {!skipped && (
        <motion.div
          className="fixed inset-0 z-50 cursor-pointer"
          onClick={handleSkip}
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' as const }}
        >
          {/* Phase 1: Dark overlay (form already fading) */}
          <motion.div
            className="absolute inset-0 bg-obsidian-900"
            initial={{ opacity: 1 }}
            animate={{ opacity: phase >= 2 ? 0 : 1 }}
            transition={{ duration: 0.5, ease: 'easeInOut' as const }}
          />

          {/* Phase 2: Horizontal light-leak from center */}
          <motion.div
            className="absolute inset-0 flex items-center justify-center overflow-hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: phase >= 2 ? 1 : 0 }}
            transition={{ duration: 0.3, ease: 'easeOut' as const }}
          >
            {/* Central light beam expanding horizontally */}
            <motion.div
              className="absolute bg-gradient-to-r from-transparent via-oatmeal-100 to-transparent"
              style={{ height: '200vh', top: '-50vh', width: '200vw', transformOrigin: 'center' }}
              initial={{ scaleX: 0, opacity: 0.8 }}
              animate={{
                scaleX: phase >= 2 ? 1 : 0,
                opacity: phase >= 3 ? 0 : 0.95,
              }}
              transition={{ duration: 0.6, ease: 'easeOut' as const }}
            />

            {/* Warm ambient fill */}
            <motion.div
              className="absolute inset-0"
              style={{
                background: 'radial-gradient(ellipse at center, #F5F4F2 0%, #EBE9E4 50%, #F5F4F2 100%)',
              }}
              initial={{ opacity: 0 }}
              animate={{ opacity: phase >= 3 ? 1 : 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' as const }}
            />
          </motion.div>

          {/* Phase 3: Welcome screen */}
          <motion.div
            className="absolute inset-0 flex items-center justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: phase >= 3 && phase < 4 ? 1 : 0 }}
            transition={{ duration: 0.4, ease: 'easeOut' as const }}
          >
            <div className="text-center">
              {/* Logo */}
              <motion.div
                className="mb-6"
                initial={{ opacity: 0, y: 10 }}
                animate={{
                  opacity: phase >= 3 ? 1 : 0,
                  y: phase >= 3 ? 0 : 10,
                }}
                transition={{ duration: 0.4, delay: 0.1, ease: 'easeOut' as const }}
              >
                <Image
                  src="/PaciolusLogo_LightBG.png"
                  alt="Paciolus"
                  width={180}
                  height={60}
                  className="mx-auto"
                  priority
                />
              </motion.div>

              {/* Welcome text */}
              <motion.h2
                className="text-2xl font-serif font-bold text-obsidian-800 mb-2"
                initial={{ opacity: 0, y: 8 }}
                animate={{
                  opacity: phase >= 3 ? 1 : 0,
                  y: phase >= 3 ? 0 : 8,
                }}
                transition={{ duration: 0.4, delay: 0.2, ease: 'easeOut' as const }}
              >
                Welcome back, {displayName}
              </motion.h2>

              {/* Date */}
              <motion.p
                className="text-sm font-sans text-obsidian-400"
                initial={{ opacity: 0 }}
                animate={{ opacity: phase >= 3 ? 1 : 0 }}
                transition={{ duration: 0.3, delay: 0.3, ease: 'easeOut' as const }}
              >
                {today}
              </motion.p>

              {/* Skip hint */}
              <motion.p
                className="mt-8 text-xs font-sans text-oatmeal-500"
                initial={{ opacity: 0 }}
                animate={{ opacity: phase >= 3 ? 0.6 : 0 }}
                transition={{ duration: 0.3, delay: 0.5, ease: 'easeOut' as const }}
              >
                Click or press any key to continue
              </motion.p>
            </div>
          </motion.div>

          {/* Phase 4: Final fade-out handled by exit animation */}
        </motion.div>
      )}
    </AnimatePresence>
  )
}
