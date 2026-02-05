'use client'

import { memo, ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface CollapsibleSectionProps {
  /** Label for the toggle button */
  label: string
  /** Number of items (displayed as "X available") */
  itemCount?: number
  /** Whether the section is expanded */
  isExpanded: boolean
  /** Callback when toggle is clicked */
  onToggle: () => void
  /** Content to show when expanded */
  children: ReactNode
  /** Optional className for the expanded content container */
  contentClassName?: string
  /** Whether to show border-top on expanded content */
  showBorder?: boolean
}

/**
 * CollapsibleSection - Shared collapsible toggle pattern
 *
 * Provides consistent expand/collapse behavior across analytics sections:
 * KeyMetricsSection (Advanced Ratios), TrendSection (Category Trends),
 * RollingWindowSection (Financial Ratios)
 *
 * Design: Oat & Obsidian theme compliant
 * - Toggle button with animated chevron
 * - AnimatePresence for smooth height transitions
 * - Consistent styling across all sections
 *
 * Sprint 41: High Priority - Shared Component Extraction
 */
export const CollapsibleSection = memo(function CollapsibleSection({
  label,
  itemCount,
  isExpanded,
  onToggle,
  children,
  contentClassName = '',
  showBorder = true,
}: CollapsibleSectionProps) {
  return (
    <div className="mt-4">
      {/* Toggle Button */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-center gap-2 py-2 px-4
                   bg-obsidian-800/30 hover:bg-obsidian-800/50
                   border border-obsidian-700/50 hover:border-obsidian-600/50
                   rounded-lg transition-all group"
      >
        <span className="text-xs font-sans text-oatmeal-400 group-hover:text-oatmeal-300">
          {isExpanded ? 'Hide' : 'Show'} {label}
        </span>
        {itemCount !== undefined && (
          <span className="text-oatmeal-500 text-xs">
            ({itemCount} available)
          </span>
        )}
        <motion.svg
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="w-4 h-4 text-oatmeal-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </motion.svg>
      </button>

      {/* Collapsible Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' as const }}
            className="overflow-hidden"
          >
            <div
              className={`mt-4 pt-4 ${showBorder ? 'border-t border-obsidian-700/30' : ''} ${contentClassName}`}
            >
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
})

CollapsibleSection.displayName = 'CollapsibleSection'

export default CollapsibleSection
