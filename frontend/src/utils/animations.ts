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

/** Fade in with 12px upward slide — most common entrance */
export const fadeInUp = {
  initial: { opacity: 0, y: 12 } as const,
  animate: { opacity: 1, y: 0 } as const,
}

/** Fade in with 20px upward slide + spring — for primary score cards */
export const fadeInUpSpring = {
  initial: { opacity: 0, y: 20 } as const,
  animate: { opacity: 1, y: 0 } as const,
  transition: { duration: 0.5, type: 'spring' as const },
}

/** Simple opacity fade — for conditional content with AnimatePresence */
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

/**
 * Standardized duration constants.
 * Prefer these over hardcoded inline values for consistency.
 */
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
