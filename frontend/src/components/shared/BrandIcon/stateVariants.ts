/**
 * State Variants — Sprint 384
 *
 * Framer-motion variants for icon states: idle, hover, active, complete.
 * Only applied when the `state` prop is provided (zero overhead for static icons).
 */

import type { Variants } from 'framer-motion'

export const iconStateVariants: Variants = {
  idle: {
    scale: 1,
    rotate: 0,
    opacity: 1,
    transition: { type: 'spring' as const, stiffness: 300, damping: 20 },
  },
  hover: {
    scale: 1.08,
    rotate: 0,
    opacity: 1,
    transition: { type: 'spring' as const, stiffness: 400, damping: 15 },
  },
  active: {
    scale: 0.92,
    rotate: 0,
    opacity: 0.85,
    transition: { type: 'spring' as const, stiffness: 500, damping: 20 },
  },
  complete: {
    scale: 1,
    rotate: 0,
    opacity: 1,
    transition: { type: 'spring' as const, stiffness: 300, damping: 20 },
  },
}
