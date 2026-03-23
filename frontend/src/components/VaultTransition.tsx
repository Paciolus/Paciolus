'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

interface VaultTransitionProps {
  onComplete: () => void
}

/**
 * VaultTransition — "Light Bleeding Through the Seam"
 *
 * A cinematic transition for successful login. Two obsidian panels split
 * apart from a hairline crack of pure white light at the viewport center,
 * revealing the warm oat interior of the software.
 *
 * Timeline (~1.8s):
 *   Hold    (0–300ms):      Dark screen. Tension builds.
 *   Seam    (300ms):        1px white line appears at center, glow blooms.
 *   Split   (400–1500ms):   Panels slide apart, light floods through.
 *   Reveal  (1200–1800ms):  Oat background fully saturates.
 *   Done    (1800ms):       onComplete fires → redirect.
 *
 * Skippable via click or keypress.
 * Reduced motion: plays a brief opacity crossfade instead of the full animation.
 * GPU-accelerated: only transform and opacity are animated.
 */
export default function VaultTransition({ onComplete }: VaultTransitionProps) {
  const [phase, setPhase] = useState<'hold' | 'seam' | 'split' | 'reveal'>('hold')
  const [reducedPhase, setReducedPhase] = useState<'dark' | 'light'>('dark')
  const [skipped, setSkipped] = useState(false)
  const completedRef = useRef(false)

  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const complete = useCallback(() => {
    if (!completedRef.current) {
      completedRef.current = true
      onComplete()
    }
  }, [onComplete])

  const handleSkip = useCallback(() => {
    if (!skipped) {
      setSkipped(true)
      complete()
    }
  }, [skipped, complete])

  // Keyboard skip
  useEffect(() => {
    const handler = () => handleSkip()
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [handleSkip])

  // Reduced motion: simple crossfade (dark → light → done)
  useEffect(() => {
    if (!prefersReducedMotion || skipped) return

    const timers: ReturnType<typeof setTimeout>[] = []
    timers.push(setTimeout(() => setReducedPhase('light'), 150))
    timers.push(setTimeout(complete, 600))
    return () => timers.forEach(clearTimeout)
  }, [prefersReducedMotion, skipped, complete])

  // Full animation phase timeline
  useEffect(() => {
    if (prefersReducedMotion || skipped) return

    const timers: ReturnType<typeof setTimeout>[] = []

    // The Seam — hairline crack of light
    timers.push(setTimeout(() => {
      setPhase('seam')
      playVaultSound()
    }, 300))

    // Panels begin splitting (brief dramatic beat after seam appears)
    timers.push(setTimeout(() => setPhase('split'), 400))

    // Oat background fully saturates
    timers.push(setTimeout(() => setPhase('reveal'), 1200))

    // Complete
    timers.push(setTimeout(complete, 1800))

    return () => timers.forEach(clearTimeout)
  }, [prefersReducedMotion, skipped, complete])

  if (skipped) return null

  // Reduced motion: simple dark-to-light crossfade, no transforms or glow
  if (prefersReducedMotion) {
    return (
      <div
        className="fixed inset-0 z-50 cursor-pointer"
        onClick={handleSkip}
        role="presentation"
        aria-hidden="true"
      >
        <div
          className="absolute inset-0"
          style={{
            background: reducedPhase === 'light'
              ? 'radial-gradient(ellipse at center, #FDFAF5 0%, #F5F0E8 50%, #EBE9E4 100%)'
              : '#0D0D0D',
            transition: 'background 400ms ease-out',
          }}
        />
      </div>
    )
  }

  const isSplitting = phase === 'split' || phase === 'reveal'
  const isRevealing = phase === 'reveal'
  const seamVisible = phase !== 'hold'

  // Vault door easing: slow start, confident middle, gentle finish
  const vaultEasing = 'cubic-bezier(0.25, 0.1, 0.15, 1.0)'

  return (
    <div
      className="fixed inset-0 z-50 cursor-pointer"
      onClick={handleSkip}
      role="presentation"
      aria-hidden="true"
    >
      {/* Oat background — the warm vault interior revealed behind the door */}
      <div
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse at center, #FDFAF5 0%, #F5F0E8 50%, #EBE9E4 100%)',
          opacity: isRevealing ? 1 : 0.1,
          transition: isRevealing ? 'opacity 600ms ease-out' : 'none',
        }}
      />

      {/* Top panel — obsidian vault door (upper half) */}
      <div
        className="absolute inset-x-0 top-0 h-1/2"
        style={{
          background: 'linear-gradient(to bottom, #0D0D0D, #1A1A1A)',
          transform: isSplitting ? 'translateY(-100%)' : 'translateY(0)',
          transition: isSplitting
            ? `transform 1100ms ${vaultEasing}`
            : 'none',
          willChange: 'transform',
        }}
      />

      {/* Bottom panel — obsidian vault door (lower half) */}
      <div
        className="absolute inset-x-0 bottom-0 h-1/2"
        style={{
          background: 'linear-gradient(to top, #0D0D0D, #1A1A1A)',
          transform: isSplitting ? 'translateY(100%)' : 'translateY(0)',
          transition: isSplitting
            ? `transform 1100ms ${vaultEasing}`
            : 'none',
          willChange: 'transform',
        }}
      />

      {/* The Seam — hairline crack of pure white light */}
      {seamVisible && (
        <div
          className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-px bg-oatmeal-50"
          style={{
            animation: `vault-seam-glow 1500ms ${vaultEasing} forwards`,
            willChange: 'opacity, box-shadow',
          }}
        />
      )}

      {/* Gold accent edges — gilded trim on the vault door junction */}
      {seamVisible && !isRevealing && (
        <>
          <div
            className="absolute left-0 right-0 top-1/2 h-px pointer-events-none"
            style={{
              transform: 'translateY(-1px)',
              background: 'linear-gradient(to right, transparent 5%, rgba(201, 168, 76, 0.2) 25%, rgba(201, 168, 76, 0.35) 50%, rgba(201, 168, 76, 0.2) 75%, transparent 95%)',
              opacity: isSplitting ? 0 : 1,
              transition: 'opacity 400ms ease-out',
            }}
          />
          <div
            className="absolute left-0 right-0 top-1/2 h-px pointer-events-none"
            style={{
              transform: 'translateY(1px)',
              background: 'linear-gradient(to right, transparent 5%, rgba(201, 168, 76, 0.2) 25%, rgba(201, 168, 76, 0.35) 50%, rgba(201, 168, 76, 0.2) 75%, transparent 95%)',
              opacity: isSplitting ? 0 : 1,
              transition: 'opacity 400ms ease-out',
            }}
          />
        </>
      )}

      {/* Skip hint — subtle, late-appearing */}
      {isSplitting && (
        <div
          className="absolute bottom-8 left-0 right-0 text-center pointer-events-none"
          style={{ opacity: 0.35 }}
        >
          <p className="text-xs font-sans" style={{ color: '#9A9486' }}>
            Press any key to skip
          </p>
        </div>
      )}
    </div>
  )
}

/**
 * Subtle vault-unsealing sound via Web Audio API.
 * A barely-audible low-frequency tone — almost felt more than heard.
 * Like the release of pressurized air from a heavy door.
 * User-gesture-gated (triggered after login click).
 */
function playVaultSound() {
  try {
    const ctx = new AudioContext()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()

    // Sub-bass tone that descends
    osc.type = 'sine'
    osc.frequency.setValueAtTime(80, ctx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(35, ctx.currentTime + 0.4)

    // Very subtle — rewarding to those who notice
    gain.gain.setValueAtTime(0.035, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5)

    osc.connect(gain)
    gain.connect(ctx.destination)

    osc.start(ctx.currentTime)
    osc.stop(ctx.currentTime + 0.5)

    setTimeout(() => ctx.close(), 600)
  } catch {
    // Sound is a grace note, not a requirement
  }
}
