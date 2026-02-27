'use client'

/**
 * IntelligenceCanvas — Ambient background system orchestrator
 *
 * Assembles four layers: DepthLayers (CSS gradients), ParticleField (Canvas 2D),
 * AccentGlow (framer-motion), and noise grain (CSS).
 *
 * Three variants: marketing (dark), workspace (light), tool (light).
 * Accent state shifts glow color/position and particle speed.
 *
 * All layers are fixed, pointer-events-none, aria-hidden.
 * Content sits above at z-10+.
 */

import { AccentGlow } from './AccentGlow'
import { VARIANT_CONFIGS, NOISE_SVG } from './canvasConfig'
import { DepthLayers } from './DepthLayers'
import { ParticleField } from './ParticleField'
import type { IntelligenceCanvasProps } from './types'

export function IntelligenceCanvas({
  variant,
  accentState = 'idle',
  className = '',
}: IntelligenceCanvasProps) {
  const config = VARIANT_CONFIGS[variant]

  return (
    <div className={`fixed inset-0 pointer-events-none overflow-hidden ${className}`} aria-hidden="true">
      {/* z-0: Base gradient depth layers */}
      <DepthLayers variant={variant} />

      {/* z-1: Canvas 2D particle field */}
      <ParticleField variant={variant} accentState={accentState} />

      {/* z-2: Accent glow overlay */}
      <AccentGlow variant={variant} accentState={accentState} />

      {/* z-3: Noise grain (marketing only) */}
      {config.noiseOpacity > 0 && (
        <div
          className="fixed inset-0 pointer-events-none mix-blend-overlay"
          style={{
            zIndex: 3,
            opacity: config.noiseOpacity,
            backgroundImage: NOISE_SVG,
            backgroundSize: '512px 512px',
          }}
          aria-hidden="true"
        />
      )}
    </div>
  )
}
