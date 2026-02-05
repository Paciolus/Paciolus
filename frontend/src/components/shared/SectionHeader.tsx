'use client'

import { memo, ReactNode } from 'react'
import { motion } from 'framer-motion'

type AccentColor = 'sage' | 'clay' | 'obsidian' | 'oatmeal'

interface SectionHeaderProps {
  /** Section title displayed in serif font */
  title: string
  /** Optional subtitle displayed below the title */
  subtitle?: string
  /** Icon element - can be SVG, emoji, or any ReactNode */
  icon?: ReactNode
  /** Background color for the icon container */
  accentColor?: AccentColor
  /** Optional badge/status element on the right side */
  badge?: ReactNode
  /** Whether to animate the header entrance */
  animate?: boolean
  /** Additional CSS classes */
  className?: string
}

// Color mappings for icon backgrounds
const ACCENT_BG_CLASSES: Record<AccentColor, string> = {
  sage: 'bg-sage-500/10',
  clay: 'bg-clay-500/10',
  obsidian: 'bg-obsidian-700/50',
  oatmeal: 'bg-oatmeal-500/10',
}

const ACCENT_TEXT_CLASSES: Record<AccentColor, string> = {
  sage: 'text-sage-400',
  clay: 'text-clay-400',
  obsidian: 'text-oatmeal-400',
  oatmeal: 'text-oatmeal-600',
}

/**
 * SectionHeader - Shared section header component
 *
 * Provides consistent header styling across analytics sections:
 * KeyMetricsSection, TrendSection, IndustryMetricsSection, RollingWindowSection
 *
 * Design: Oat & Obsidian theme compliant
 * - Title uses font-serif (Merriweather)
 * - Subtitle uses font-sans (Lato)
 * - Icon container with accent color background
 *
 * Sprint 41: Performance Quick Wins - Shared Component Extraction
 */
export const SectionHeader = memo(function SectionHeader({
  title,
  subtitle,
  icon,
  accentColor = 'sage',
  badge,
  animate = true,
  className = '',
}: SectionHeaderProps) {
  const content = (
    <div className={`flex items-center justify-between mb-4 ${className}`}>
      <div className="flex items-center gap-3">
        {/* Icon Container */}
        {icon && (
          <div
            className={`w-8 h-8 rounded-lg ${ACCENT_BG_CLASSES[accentColor]} flex items-center justify-center`}
          >
            <span className={ACCENT_TEXT_CLASSES[accentColor]}>{icon}</span>
          </div>
        )}

        {/* Title and Subtitle */}
        <div>
          <h3 className="font-serif font-semibold text-oatmeal-200 text-lg">
            {title}
          </h3>
          {subtitle && (
            <p className="text-oatmeal-500 text-xs font-sans">{subtitle}</p>
          )}
        </div>
      </div>

      {/* Badge/Status Area */}
      {badge && <div className="flex items-center gap-3">{badge}</div>}
    </div>
  )

  if (animate) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {content}
      </motion.div>
    )
  }

  return content
})

SectionHeader.displayName = 'SectionHeader'

export default SectionHeader
