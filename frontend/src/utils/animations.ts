/**
 * Shared Framer-Motion Animation Utilities
 *
 * Non-deprecated animation presets for specific UI patterns.
 * For general entrance animations, use '@/lib/motion' instead.
 */

/** Data quality bar fill transition */
export const dataFillTransition = {
  duration: 0.8,
  ease: 'easeOut' as const,
}

/** Score circle draw transition */
export const scoreCircleTransition = {
  duration: 1.2,
  ease: 'easeOut' as const,
}
