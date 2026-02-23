'use client'

/**
 * ParticleField — Canvas 2D particle system
 *
 * Renders 25-80 particles driven by a sine-based flow field.
 * All animation is imperative (ref-based) — React never re-renders per frame.
 */

import { useRef } from 'react'
import { VARIANT_CONFIGS } from './canvasConfig'
import { useParticleField } from './useParticleField'
import type { CanvasVariant, AccentState } from './types'

interface ParticleFieldProps {
  variant: CanvasVariant
  accentState: AccentState
}

export function ParticleField({ variant, accentState }: ParticleFieldProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useParticleField(canvasRef, { variant, accentState })

  const config = VARIANT_CONFIGS[variant]

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none"
      style={{
        zIndex: 1,
        mixBlendMode: config.blendParticle as React.CSSProperties['mixBlendMode'],
      }}
      aria-hidden="true"
    />
  )
}
