'use client'

/**
 * Reveal — Scroll-triggered entrance wrapper.
 *
 * Lightweight replacement for SectionReveal. Uses useInView
 * for scroll-triggered fadeUp with optional delay for cascading.
 * Respects prefers-reduced-motion by zeroing duration.
 */

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { fadeUp, duration, ease, lift, useMotionPreference } from '@/lib/motion'

interface RevealProps {
  children: React.ReactNode
  /** Extra delay in seconds for cascade sequencing */
  delay?: number
  className?: string
}

export function Reveal({ children, delay = 0, className }: RevealProps) {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true, margin: '0px 0px 400px 0px' })
  const { prefersReducedMotion } = useMotionPreference()

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      variants={fadeUp}
      transition={
        prefersReducedMotion
          ? { duration: 0 }
          : {
              duration: duration.base,
              ease: ease.out,
              delay,
            }
      }
      className={className}
    >
      {children}
    </motion.div>
  )
}
