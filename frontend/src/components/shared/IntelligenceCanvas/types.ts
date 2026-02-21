/**
 * IntelligenceCanvas — Type definitions
 *
 * Ambient computational background system with flow-field particles.
 * Three variants: marketing (dark), workspace (light), tool (light).
 */

export type CanvasVariant = 'marketing' | 'workspace' | 'tool'

export type AccentState = 'idle' | 'upload' | 'analyze' | 'validate' | 'export'

export interface IntelligenceCanvasProps {
  variant: CanvasVariant
  accentState?: AccentState
  className?: string
}

export interface ParticleConfig {
  count: [number, number]             // [min, max]
  color: string                       // RGB string e.g. "235, 233, 228"
  opacityRange: [number, number]      // per-particle opacity bounds
  sizeRange: [number, number]         // px radius
  speedRange: [number, number]        // px per frame
  trailAlpha: number                  // canvas clear alpha (1 = no trail, 0.92 = ghosting)
}

export interface VariantConfig {
  particle: ParticleConfig
  baseGradient: string                // CSS radial-gradient for DepthLayers
  glowGradients: string[]             // Additional glow gradient layers
  blendParticle: string               // mix-blend-mode for canvas
  blendGlow: string                   // mix-blend-mode for accent glow
  noiseOpacity: number                // grain overlay opacity
}

export interface AccentConfig {
  glowColor: string                   // RGB string
  opacity: number
  position: string                    // CSS background-position
  speedMultiplier: number
  pulse?: boolean
  scale?: number
}

export interface Particle {
  x: number
  y: number
  size: number
  opacity: number
  baseOpacity: number
  speed: number
  life: number
}
