/**
 * Canonical Entrance Motion Tokens — Sprint 476
 *
 * Single source of truth for entrance animations across
 * marketing, workspace, and tool pages. Replaces fragmented
 * tokens in animations.ts, themeUtils.ts, marketingMotion.tsx,
 * and motionTokens.ts for entrance-specific concerns.
 *
 * Non-entrance animations (hover, parallax, tool-state, line draws,
 * tab crossfades) remain in their original files.
 */

import { useReducedMotion as useFramerReducedMotion } from 'framer-motion'
import type { Variants, Transition } from 'framer-motion'

// =============================================================================
// DURATION — cubic-bezier entrance timing
// =============================================================================

export const duration = {
  /** Tooltips, micro-interactions */
  fast: 0.18,
  /** Standard entrance — cards, sections, modals */
  base: 0.28,
  /** Scroll-reveal, marketing hero */
  slow: 0.4,
} as const

// =============================================================================
// EASE — cubic-bezier curves
// =============================================================================

export const ease = {
  /** Standard deceleration — elements appearing */
  out: [0.16, 1, 0.3, 1] as readonly [number, number, number, number],
  /** Symmetric — modals, overlays */
  inOut: [0.45, 0, 0.55, 1] as readonly [number, number, number, number],
} as const

// =============================================================================
// STAGGER — child delay intervals
// =============================================================================

export const stagger = {
  /** Dashboard grids, card lists */
  tight: 0.06,
  /** Hero sections, marketing features */
  loose: 0.1,
} as const

// =============================================================================
// LIFT — Y-offset distances
// =============================================================================

export const lift = {
  /** Universal entrance offset */
  subtle: 10,
} as const

// =============================================================================
// VARIANTS — framer-motion Variants objects
// =============================================================================

/**
 * Fade up — universal entrance variant.
 * Opacity 0 → 1, y lift.subtle → 0.
 *
 * Embeds transition in `visible` so it works standalone or
 * inside a stagger container (container overrides delay).
 */
export const fadeUp: Variants = {
  hidden: { opacity: 0, y: lift.subtle },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: duration.base,
      ease: ease.out,
    } satisfies Transition,
  },
}

/**
 * Stagger container — loose (0.1s) for hero/marketing sections.
 * Children must use variant-based animations (e.g. fadeUp).
 */
export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: stagger.loose,
      delayChildren: 0.1,
    },
  },
}

/**
 * Stagger container — tight (0.06s) for grids/dashboards.
 * Children must use variant-based animations (e.g. fadeUp).
 */
export const staggerContainerTight: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: stagger.tight,
      delayChildren: 0.05,
    },
  },
}

/**
 * Fade + scale — modal/panel entrance.
 * Includes exit state for AnimatePresence.
 */
export const fadeScale: Variants = {
  hidden: { opacity: 0, scale: 0.97 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: duration.base,
      ease: ease.out,
    } satisfies Transition,
  },
  exit: {
    opacity: 0,
    scale: 0.97,
    transition: {
      duration: duration.fast,
      ease: ease.inOut,
    } satisfies Transition,
  },
}

// =============================================================================
// HOOK — reduced-motion preference
// =============================================================================

/**
 * Returns reduced-motion preference for entrance animations.
 * Wraps framer-motion's useReducedMotion for non-framer contexts
 * (e.g. Reveal component duration override).
 */
export function useMotionPreference() {
  const prefersReducedMotion = useFramerReducedMotion() ?? false

  return {
    /** True when the user prefers reduced motion */
    prefersReducedMotion,
    /** True when motion is safe to run */
    motionSafe: !prefersReducedMotion,
  }
}
