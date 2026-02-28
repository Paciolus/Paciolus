'use client'

/**
 * Marketing Motion Presets — Sprint 337
 *
 * Centralized animation vocabulary for marketing components.
 * Replaces 6 different Y-offsets, 5+ spring configs, 4 viewport margins,
 * and 3 duplicate CountUp implementations with semantic presets.
 *
 * All springs reference SPRING from themeUtils.ts.
 * All durations reference DURATION from animations.ts.
 *
 * Reduced-motion: handled globally by <MotionConfig reducedMotion="user">
 * in providers.tsx — no per-component checks needed.
 */

import { useRef, useState, useEffect } from 'react'
import { motion, useInView, useScroll, useTransform } from 'framer-motion'
import { useReducedMotion } from '@/hooks/useReducedMotion'
import { DURATION } from './animations'
import { SPRING } from './themeUtils'
import type { Variants, Transition } from 'framer-motion'

// =============================================================================
// SEMANTIC OFFSETS
// =============================================================================

/** Semantic Y-offset tiers (consolidates 6 values → 3) */
export const OFFSET = {
  /** Labels, badges, lightweight items */
  subtle: 12,
  /** Section headers, cards, default entrance */
  standard: 24,
  /** Hero features, timeline steps */
  dramatic: 40,
} as const

// =============================================================================
// VIEWPORT CONFIGS
// =============================================================================

/** Viewport intersection margins (consolidates 4 → 2) */
export const VIEWPORT = {
  /** Most sections */
  default: { once: true, margin: '-80px' as const },
  /** Small elements, pills */
  eager: { once: true, margin: '-40px' as const },
} as const

// =============================================================================
// STAGGER CONTAINERS
// =============================================================================

/** Stagger container variants (consolidates 4 speeds → 2) */
export const STAGGER = {
  /** Badges, pills, small items */
  fast: {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.06, delayChildren: 0.1 },
    },
  },
  /** Cards, feature grids, steps */
  standard: {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.15 },
    },
  },
} as const satisfies Record<string, Variants>

// =============================================================================
// ENTRANCE VARIANTS
// =============================================================================

/** Core entrance animation presets */
export const ENTER = {
  /** Standard fade-up — cards, headers, default entrance */
  fadeUp: {
    hidden: { opacity: 0, y: OFFSET.standard },
    visible: {
      opacity: 1,
      y: 0,
      transition: SPRING.snappy,
    },
  },
  /** Subtle fade-up — labels, badges, lightweight items */
  fadeUpSubtle: {
    hidden: { opacity: 0, y: OFFSET.subtle },
    visible: {
      opacity: 1,
      y: 0,
      transition: SPRING.gentle,
    },
  },
  /** Dramatic fade-up — hero features, timeline steps */
  fadeUpDramatic: {
    hidden: { opacity: 0, y: OFFSET.dramatic, scale: 0.93 },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: SPRING.snappy,
    },
  },
  /** Slide from left — directional section entrance */
  slideFromLeft: {
    hidden: { opacity: 0, x: -30 },
    visible: {
      opacity: 1,
      x: 0,
      transition: SPRING.snappy,
    },
  },
  /** Slide from right — directional section entrance */
  slideFromRight: {
    hidden: { opacity: 0, x: 30 },
    visible: {
      opacity: 1,
      x: 0,
      transition: SPRING.snappy,
    },
  },
  /** Clip-path reveal — wipes in top-down */
  clipReveal: {
    hidden: { clipPath: 'inset(0 0 100% 0)' },
    visible: {
      clipPath: 'inset(0 0 0% 0)',
      transition: { duration: DURATION.hero, ease: 'easeOut' as const },
    },
  },
} as const satisfies Record<string, Variants>

// =============================================================================
// DRAW VARIANTS (line animations)
// =============================================================================

/** Factory functions for line-draw animations */
export const DRAW = {
  /** Horizontal line draw — scaleX 0→1 */
  lineHorizontal(delay: number): Variants {
    return {
      hidden: { scaleX: 0, originX: 0 },
      visible: {
        scaleX: 1,
        transition: { duration: 0.8, ease: 'easeOut' as const, delay },
      },
    }
  },
  /** Vertical line draw — scaleY 0→1 */
  lineVertical(delay: number): Variants {
    return {
      hidden: { scaleY: 0, originY: 0 },
      visible: {
        scaleY: 1,
        transition: { duration: 1.2, ease: 'easeOut' as const, delay },
      },
    }
  },
}

// =============================================================================
// HOVER VARIANTS
// =============================================================================

/** Hover interaction presets */
export const HOVER = {
  /** Subtle lift — cards, containers */
  lift: {
    rest: { y: 0 },
    hover: {
      y: -6,
      transition: SPRING.snappy,
    },
  },
  /** Icon pulse — decorative icon bounce */
  iconPulse: {
    rest: { scale: 1, rotate: 0 },
    hover: {
      scale: 1.1,
      rotate: 3,
      transition: SPRING.bouncy,
    },
  },
} as const satisfies Record<string, Variants>

// =============================================================================
// SHARED-AXIS TRANSITIONS (for AnimatePresence)
// =============================================================================

/** Shared-axis transitions for tab/panel crossfades */
export const AXIS = {
  /** Horizontal tab switch — enter from right, exit to left */
  horizontal: {
    initial: { opacity: 0, x: 20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 },
    transition: { duration: 0.25, ease: 'easeOut' as const } satisfies Transition,
  },
  /** Vertical content switch */
  vertical: {
    initial: { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -8 },
    transition: { duration: 0.25, ease: 'easeOut' as const } satisfies Transition,
  },
} as const

// =============================================================================
// SHARED COMPONENTS
// =============================================================================

/**
 * CountUp — Animated number counter.
 *
 * Consolidates 3 duplicate implementations across marketing components.
 * Uses `useInView` + `setInterval` (40 frames, 30ms ≈ 33fps).
 * Respects `prefers-reduced-motion` by showing final value immediately.
 */
export function CountUp({
  target,
  suffix = '',
  pad,
}: {
  target: number
  suffix?: string
  pad?: number
}) {
  const ref = useRef<HTMLSpanElement>(null)
  const isVisible = useInView(ref, { once: true })
  const [count, setCount] = useState(0)
  const { prefersReducedMotion } = useReducedMotion()

  useEffect(() => {
    if (!isVisible) return

    if (prefersReducedMotion) {
      setCount(target)
      return
    }

    let frame = 0
    const totalFrames = 40
    const interval = setInterval(() => {
      frame++
      setCount(Math.round((frame / totalFrames) * target))
      if (frame >= totalFrames) {
        clearInterval(interval)
        setCount(target)
      }
    }, 30)

    return () => clearInterval(interval)
  }, [isVisible, target, prefersReducedMotion])

  const display = pad ? String(count).padStart(pad, '0') : count.toLocaleString()

  return <span ref={ref}>{display}{suffix}</span>
}

/**
 * SectionReveal — Wrapper for homepage sections.
 *
 * Creates section-to-section directional continuity by
 * allowing consecutive sections to enter from different directions.
 */
export function SectionReveal({
  children,
  direction = 'up',
  className,
}: {
  children: React.ReactNode
  direction?: 'up' | 'left' | 'right'
  className?: string
}) {
  const variants =
    direction === 'left'
      ? ENTER.slideFromLeft
      : direction === 'right'
        ? ENTER.slideFromRight
        : ENTER.fadeUp

  return (
    <motion.div
      variants={variants}
      initial="hidden"
      whileInView="visible"
      viewport={VIEWPORT.default}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/**
 * ParallaxSection — Subtle scroll-linked parallax wrapper.
 *
 * Phase LXVII: Visual Polish — C1.
 * Translates children along the Y-axis as the section scrolls into view.
 * Offset range is intentionally small (±20px) for elegance.
 * Respects `prefers-reduced-motion` by disabling transform.
 */
export function ParallaxSection({
  children,
  className,
  speed = 0.08,
}: {
  children: React.ReactNode
  className?: string
  /** Parallax intensity (0–1). Default 0.08 = very subtle. */
  speed?: number
}) {
  const ref = useRef<HTMLDivElement>(null)
  const { prefersReducedMotion } = useReducedMotion()
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start end', 'end start'],
  })
  const y = useTransform(scrollYProgress, [0, 1], [speed * 250, speed * -250])

  return (
    <div ref={ref} className={className}>
      <motion.div style={prefersReducedMotion ? undefined : { y }}>
        {children}
      </motion.div>
    </div>
  )
}
