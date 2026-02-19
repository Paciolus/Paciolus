'use client'

import { motion } from 'framer-motion'

/**
 * GradientMesh — Sprint 320
 *
 * Layered atmospheric background for the dark homepage.
 * Replaces flat obsidian with depth through radial gradients,
 * subtle sage-tinted glows, and parallax-lite scroll behavior.
 *
 * Pure CSS gradients + framer-motion — no images needed.
 * Respects prefers-reduced-motion via framer-motion MotionConfig.
 */
export function GradientMesh() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
      {/* Base gradient — deep obsidian with subtle warm undertone */}
      <div
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse 80% 60% at 50% 0%, #1a1f1c 0%, #121212 50%, #0d0d0d 100%)',
        }}
      />

      {/* Sage ambient glow — top right */}
      <motion.div
        className="absolute -top-[20%] -right-[10%] w-[800px] h-[800px] rounded-full"
        style={{
          background: 'radial-gradient(circle, rgba(74,124,89,0.08) 0%, rgba(74,124,89,0.02) 50%, transparent 70%)',
        }}
        animate={{
          scale: [1, 1.05, 1],
          opacity: [0.6, 0.8, 0.6],
        }}
        transition={{
          duration: 12,
          repeat: Infinity,
          repeatType: 'reverse' as const,
          ease: 'easeInOut' as const,
        }}
      />

      {/* Warm oatmeal glow — bottom left */}
      <motion.div
        className="absolute -bottom-[30%] -left-[15%] w-[700px] h-[700px] rounded-full"
        style={{
          background: 'radial-gradient(circle, rgba(235,233,228,0.04) 0%, rgba(235,233,228,0.01) 50%, transparent 70%)',
        }}
        animate={{
          scale: [1, 1.08, 1],
          opacity: [0.5, 0.7, 0.5],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          repeatType: 'reverse' as const,
          ease: 'easeInOut' as const,
          delay: 3,
        }}
      />

      {/* Subtle sage accent — center-left, smaller */}
      <motion.div
        className="absolute top-[40%] -left-[5%] w-[400px] h-[400px] rounded-full"
        style={{
          background: 'radial-gradient(circle, rgba(74,124,89,0.05) 0%, transparent 60%)',
        }}
        animate={{
          x: [0, 20, 0],
          y: [0, -15, 0],
          opacity: [0.4, 0.6, 0.4],
        }}
        transition={{
          duration: 18,
          repeat: Infinity,
          repeatType: 'reverse' as const,
          ease: 'easeInOut' as const,
          delay: 6,
        }}
      />

      {/* Noise grain overlay */}
      <div
        className="absolute inset-0 opacity-[0.035] mix-blend-overlay"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='g'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23g)'/%3E%3C/svg%3E")`,
        }}
      />
    </div>
  )
}
