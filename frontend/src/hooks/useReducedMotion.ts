/**
 * useReducedMotion — Sprint 401: Phase LVI
 *
 * Wraps framer-motion's useReducedMotion hook for non-framer animations
 * (Canvas rAF, CountUp setInterval) that can't rely on
 * <MotionConfig reducedMotion="user">.
 */

import { useReducedMotion as useFramerReducedMotion } from 'framer-motion'

export function useReducedMotion() {
  const prefersReducedMotion = useFramerReducedMotion() ?? false

  return {
    /** True when the user prefers reduced motion */
    prefersReducedMotion,
    /** True when motion is safe to run (inverse convenience) */
    motionSafe: !prefersReducedMotion,
  }
}
