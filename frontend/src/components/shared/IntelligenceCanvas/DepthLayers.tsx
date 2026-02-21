'use client'

/**
 * DepthLayers — CSS gradient depth layers per variant
 *
 * Static radial gradients that provide atmospheric depth.
 * GPU-free — pure CSS background-image stacking.
 * The marketing variant reproduces GradientMesh's 3 radial glows identically.
 */

import type { CanvasVariant } from './types'
import { VARIANT_CONFIGS } from './canvasConfig'

interface DepthLayersProps {
  variant: CanvasVariant
}

export function DepthLayers({ variant }: DepthLayersProps) {
  const config = VARIANT_CONFIGS[variant]

  return (
    <>
      {/* Base gradient */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          zIndex: 0,
          background: config.baseGradient,
          opacity: variant === 'marketing' ? 1 : 0.6,
        }}
        aria-hidden="true"
      />

      {/* Additional glow layers */}
      {config.glowGradients.map((gradient, i) => (
        <div
          key={i}
          className="fixed inset-0 pointer-events-none"
          style={{
            zIndex: 0,
            background: gradient,
          }}
          aria-hidden="true"
        />
      ))}
    </>
  )
}
