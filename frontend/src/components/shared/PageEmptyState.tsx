'use client'

import { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { fadeUp } from '@/lib/motion'

interface PageEmptyStateProps {
  /** Icon element — typically an SVG */
  icon: ReactNode
  /** Heading text */
  title: string
  /** Description text */
  description: string
  /** Primary CTA button */
  action?: {
    label: string
    onClick: () => void
    icon?: ReactNode
  }
  /** Optional trust badge text (e.g., Zero-Storage) */
  trustBadge?: string
}

/**
 * PageEmptyState — full-page empty state with CTA + optional trust badge.
 *
 * Used for Dashboard, Portfolio, and Workspaces when no data exists.
 * Distinct from EmptyStateCard (inline section-level empty states).
 *
 * Sprint 566: Design enrichment — consistent empty states across pages.
 */
export function PageEmptyState({ icon, title, description, action, trustBadge }: PageEmptyStateProps) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className="text-center py-16"
    >
      <div className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-surface-card-secondary border border-theme flex items-center justify-center">
        <span className="w-12 h-12 text-content-tertiary">{icon}</span>
      </div>

      <h2 className="text-2xl font-serif font-semibold text-content-primary mb-2">
        {title}
      </h2>
      <p className="text-content-secondary font-sans mb-8 max-w-md mx-auto">
        {description}
      </p>

      {action && (
        <motion.button
          initial={{ y: 0 }}
          whileHover={{ y: -2 }}
          whileTap={{ y: 0, scale: 0.98 }}
          onClick={action.onClick}
          className="inline-flex items-center gap-2 px-6 py-3.5 bg-sage-600 hover:bg-sage-700 text-white font-sans font-bold rounded-xl transition-colors shadow-theme-card"
        >
          {action.icon || (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          )}
          {action.label}
        </motion.button>
      )}

      {trustBadge && (
        <div className="mt-8 inline-flex items-center gap-2 bg-sage-50 border border-sage-200 rounded-full px-4 py-2">
          <svg className="w-4 h-4 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <span className="text-sage-700 text-sm font-sans">{trustBadge}</span>
        </div>
      )}
    </motion.div>
  )
}
