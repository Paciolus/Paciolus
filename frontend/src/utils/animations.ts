/**
 * Shared Framer-Motion Animation Variants — Sprint 161
 *
 * Centralizes the most common animation patterns used across tool pages.
 * Import these instead of redeclaring inline { initial, animate, transition }.
 *
 * Usage:
 *   <motion.div {...fadeInUp}>
 *   <motion.div {...fadeIn} transition={{ delay: 0.2 }}>
 */

/** @deprecated Use fadeUp from '@/lib/motion' instead */
export const fadeInUp = {
  initial: { opacity: 0, y: 12 } as const,
  animate: { opacity: 1, y: 0 } as const,
}

/** @deprecated Use fadeUp from '@/lib/motion' instead */
export const fadeInUpSpring = {
  initial: { opacity: 0, y: 20 } as const,
  animate: { opacity: 1, y: 0 } as const,
  transition: { duration: 0.5, type: 'spring' as const },
}

/** @deprecated Use fadeScale from '@/lib/motion' for modals, or inline opacity for state transitions */
export const fadeIn = {
  initial: { opacity: 0 } as const,
  animate: { opacity: 1 } as const,
  exit: { opacity: 0 } as const,
}

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

/** @deprecated Use duration from '@/lib/motion' for entrance timing. Tool-state timing lives in motionTokens.ts TIMING */
export const DURATION = {
  /** Tooltips, micro-interactions */
  instant: 0.15,
  /** Collapsibles, toggles, interactive UI */
  fast: 0.2,
  /** Standard entrances, exits */
  normal: 0.3,
  /** Scroll-reveal, marketing sections */
  slow: 0.5,
  /** Page hero sections */
  hero: 0.6,
} as const
