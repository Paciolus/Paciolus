'use client'

/**
 * ScanlineOverlay — Sprint 707 demo signature moment.
 *
 * Sage-tinted horizontal sweep that runs once across a wrapped region
 * on mount. Sells the "under three seconds" analysis claim viscerally
 * — the user sees the instrument "scan" the data before results resolve.
 *
 * Usage:
 *   <ScanlineOverlay>
 *     <TrialBalanceTable data={...} />
 *   </ScanlineOverlay>
 *
 * The scan runs once per mount, 1.2s duration, with a 0.2s delay so
 * the wrapped content has time to paint. `prefers-reduced-motion: reduce`
 * suppresses the animation entirely — the wrapped content renders
 * immediately with no overlay.
 *
 * Demo-surface-only: this component lives under `components/demo/` and
 * must not leak into real product views (Sprint 707 isolation rule).
 */

import { useEffect, useRef, useState, type ReactNode } from 'react'

interface ScanlineOverlayProps {
  children: ReactNode
  /** Override the default 1.2s duration (in ms). */
  durationMs?: number
  /** Override the default 200ms start delay (in ms). */
  delayMs?: number
  /** Extra classes merged onto the outer wrapper for spacing / layout. */
  className?: string
}

export function ScanlineOverlay({
  children,
  durationMs = 1200,
  delayMs = 200,
  className = '',
}: ScanlineOverlayProps) {
  const [active, setActive] = useState(false)
  const prefersReduced = usePrefersReducedMotion()

  useEffect(() => {
    if (prefersReduced) return
    const start = setTimeout(() => setActive(true), delayMs)
    const stop = setTimeout(() => setActive(false), delayMs + durationMs)
    return () => {
      clearTimeout(start)
      clearTimeout(stop)
    }
  }, [prefersReduced, delayMs, durationMs])

  return (
    <div className={`relative overflow-hidden ${className}`}>
      {children}
      {active && (
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 top-0 h-10"
          style={{
            background: 'linear-gradient(180deg, rgba(74,124,89,0) 0%, rgba(74,124,89,0.18) 50%, rgba(74,124,89,0) 100%)',
            animation: `paciolus-scanline-sweep ${durationMs}ms ease-in-out 1 forwards`,
          }}
        />
      )}
      {/* Keyframes are keyed to the component so mounting a second overlay
          doesn't collide with an earlier instance's transform. */}
      <style jsx>{`
        @keyframes paciolus-scanline-sweep {
          from { transform: translateY(0); opacity: 0.0; }
          10%  { opacity: 1; }
          90%  { opacity: 1; }
          to   { transform: translateY(calc(100cqh + 100%)); opacity: 0.0; }
        }
      `}</style>
    </div>
  )
}

/** Hook: returns true if the user has requested reduced motion. */
function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false)
  const mq = useRef<MediaQueryList | null>(null)

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    mq.current = window.matchMedia('(prefers-reduced-motion: reduce)')
    setReduced(mq.current.matches)
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches)
    mq.current.addEventListener('change', handler)
    return () => mq.current?.removeEventListener('change', handler)
  }, [])

  return reduced
}
