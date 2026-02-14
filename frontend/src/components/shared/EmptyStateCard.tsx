'use client'

import { memo, ReactNode } from 'react'
import { motion } from 'framer-motion'

interface EmptyStateCardProps {
  /** Icon to display - typically an SVG element */
  icon: ReactNode
  /** Title text */
  title: string
  /** Description/message text */
  message: string
  /** Whether to animate entrance */
  animate?: boolean
  /** Additional className */
  className?: string
}

/**
 * EmptyStateCard - Shared empty/error state display
 *
 * Provides consistent empty state messaging across analytics sections:
 * KeyMetricsSection, TrendSection, IndustryMetricsSection, RollingWindowSection
 *
 * Design: Oat & Obsidian theme compliant
 * - Centered layout with icon, title, message
 * - Subtle background with border
 * - Optional entrance animation
 *
 * Sprint 41: High Priority - Shared Component Extraction
 */
export const EmptyStateCard = memo(function EmptyStateCard({
  icon,
  title,
  message,
  animate = true,
  className = '',
}: EmptyStateCardProps) {
  const content = (
    <div
      className={`bg-surface-card rounded-xl border border-theme p-6 text-center ${className}`}
    >
      {/* Icon Container */}
      <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-surface-card-secondary flex items-center justify-center">
        <span className="w-6 h-6 text-content-tertiary">{icon}</span>
      </div>

      {/* Title */}
      <h4 className="font-sans font-medium text-content-primary mb-1">{title}</h4>

      {/* Message */}
      <p className="text-content-tertiary text-sm font-sans max-w-sm mx-auto">
        {message}
      </p>
    </div>
  )

  if (animate) {
    return (
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        {content}
      </motion.div>
    )
  }

  return content
})

EmptyStateCard.displayName = 'EmptyStateCard'

// Common icons for empty states (as SVG components)
export const ChartIcon = (): JSX.Element => (
  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-6 h-6">
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
    />
  </svg>
)

export const TrendIcon = (): JSX.Element => (
  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-6 h-6">
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
    />
  </svg>
)

export const IndustryIcon = (): JSX.Element => (
  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-6 h-6">
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
    />
  </svg>
)

export const RollingIcon = (): JSX.Element => (
  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-6 h-6">
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
    />
  </svg>
)

export default EmptyStateCard
