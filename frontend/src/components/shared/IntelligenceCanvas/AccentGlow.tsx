'use client'

/**
 * AccentGlow — framer-motion glow overlay keyed to accent state
 *
 * A single motion.div radial gradient that shifts color, opacity,
 * position, and scale based on accent state transitions.
 * Transitions use SPRING.gentle for smooth, non-jarring shifts.
 */

import { motion } from 'framer-motion'
import { SPRING } from '@/utils/themeUtils'
import { ACCENT_CONFIGS, VARIANT_CONFIGS } from './canvasConfig'
import type { CanvasVariant, AccentState } from './types'

interface AccentGlowProps {
  variant: CanvasVariant
  accentState: AccentState
}

export function AccentGlow({ variant, accentState }: AccentGlowProps) {
  const accent = ACCENT_CONFIGS[accentState]
  const config = VARIANT_CONFIGS[variant]

  const [posX, posY] = accent.position.split(' ')

  return (
    <motion.div
      className="fixed inset-0 pointer-events-none"
      style={{
        zIndex: 2,
        mixBlendMode: config.blendGlow as React.CSSProperties['mixBlendMode'],
      }}
      animate={{
        background: `radial-gradient(ellipse 60% 50% at ${posX} ${posY}, rgba(${accent.glowColor}, ${accent.opacity}) 0%, transparent 70%)`,
        scale: accent.scale ?? 1,
        opacity: accent.pulse ? [0.6, 1, 0.6] : 1,
      }}
      transition={
        accent.pulse
          ? {
              opacity: {
                duration: 3,
                repeat: Infinity,
                repeatType: 'reverse' as const,
                ease: 'easeInOut' as const,
              },
              default: SPRING.gentle,
            }
          : SPRING.gentle
      }
      aria-hidden="true"
    />
  )
}
