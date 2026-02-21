/**
 * IntelligenceCanvas — Configuration
 *
 * Variant configs, particle parameters, and accent color maps.
 * All opacity values are kept within strict budgets:
 *   marketing: 8% max, workspace: 4% max, tool: 3% max
 */

import type { VariantConfig, AccentConfig, AccentState, CanvasVariant } from './types'

// ─── Noise SVG (reused from globals.css grain-overlay) ─────────────────
export const NOISE_SVG = `url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='g'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23g)'/%3E%3C/svg%3E")`

// ─── Variant Configurations ────────────────────────────────────────────

export const VARIANT_CONFIGS: Record<CanvasVariant, VariantConfig> = {
  marketing: {
    particle: {
      count: [60, 80],
      color: '235, 233, 228',            // oatmeal ghost
      opacityRange: [0.06, 0.12],
      sizeRange: [1.5, 3],
      speedRange: [0.15, 0.3],
      trailAlpha: 0.92,                   // 2-frame ghosting
    },
    baseGradient: 'radial-gradient(ellipse 80% 60% at 50% 0%, #1a1f1c 0%, #121212 50%, #0d0d0d 100%)',
    glowGradients: [
      'radial-gradient(circle at 85% 15%, rgba(74,124,89,0.08) 0%, rgba(74,124,89,0.02) 50%, transparent 70%)',
      'radial-gradient(circle at 15% 80%, rgba(235,233,228,0.04) 0%, rgba(235,233,228,0.01) 50%, transparent 70%)',
      'radial-gradient(circle at 20% 45%, rgba(74,124,89,0.05) 0%, transparent 60%)',
    ],
    blendParticle: 'soft-light',
    blendGlow: 'screen',
    noiseOpacity: 0.035,
  },

  workspace: {
    particle: {
      count: [30, 40],
      color: '74, 124, 89',              // sage whisper
      opacityRange: [0.03, 0.06],
      sizeRange: [1, 2],
      speedRange: [0.08, 0.15],
      trailAlpha: 1,                      // no trail
    },
    baseGradient: 'radial-gradient(ellipse 90% 70% at 50% 30%, rgba(74,124,89,0.03) 0%, transparent 70%)',
    glowGradients: [
      'radial-gradient(circle at 70% 20%, rgba(74,124,89,0.02) 0%, transparent 60%)',
    ],
    blendParticle: 'multiply',
    blendGlow: 'multiply',
    noiseOpacity: 0,
  },

  tool: {
    particle: {
      count: [25, 35],
      color: '74, 124, 89',              // sage faint
      opacityRange: [0.02, 0.05],
      sizeRange: [0.8, 1.5],
      speedRange: [0.06, 0.12],
      trailAlpha: 1,                      // no trail
    },
    baseGradient: 'radial-gradient(ellipse 80% 60% at 50% 20%, rgba(74,124,89,0.02) 0%, transparent 60%)',
    glowGradients: [],
    blendParticle: 'multiply',
    blendGlow: 'multiply',
    noiseOpacity: 0,
  },
}

// ─── Accent State Configurations ───────────────────────────────────────

export const ACCENT_CONFIGS: Record<AccentState, AccentConfig> = {
  idle: {
    glowColor: '74, 124, 89',
    opacity: 0.02,
    position: '50% 50%',
    speedMultiplier: 1.0,
  },
  upload: {
    glowColor: '74, 124, 89',
    opacity: 0.06,
    position: '50% 20%',
    speedMultiplier: 1.2,
  },
  analyze: {
    glowColor: '74, 124, 89',
    opacity: 0.04,
    position: '50% 50%',
    speedMultiplier: 1.5,
    pulse: true,
    scale: 1.1,
  },
  validate: {
    glowColor: '74, 124, 89',
    opacity: 0.05,
    position: '50% 80%',
    speedMultiplier: 0.8,
  },
  export: {
    glowColor: '235, 233, 228',
    opacity: 0.03,
    position: '80% 80%',
    speedMultiplier: 0.6,
  },
}

// ─── Flow Field ────────────────────────────────────────────────────────

/**
 * Sine-based flow field angle. Three overlapping sine/cosine waves
 * produce organic directional flow without a noise library.
 */
export function flowAngle(x: number, y: number, time: number): number {
  return (
    Math.sin(x * 0.003 + time * 0.2) * Math.PI +
    Math.cos(y * 0.004 + time * 0.15) * Math.PI * 0.5 +
    Math.sin((x + y) * 0.002 + time * 0.1) * Math.PI * 0.3
  )
}

// ─── Helpers ───────────────────────────────────────────────────────────

/** Random float in range [min, max] */
export function randomInRange(min: number, max: number): number {
  return min + Math.random() * (max - min)
}

/** Get particle count, reduced ~40% on mobile */
export function getParticleCount(config: VariantConfig): number {
  const [min, max] = config.particle.count
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768
  const base = Math.round(randomInRange(min, max))
  return isMobile ? Math.round(base * 0.6) : base
}
