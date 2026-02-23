'use client'

import { useState, useCallback, memo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AccountTypeDropdown, MappingIndicator } from '@/components/mapping'
import type { AbnormalBalanceExtended, AccountType, ClassificationSuggestion } from '@/types/mapping'
import { ACCOUNT_TYPE_LABELS } from '@/types/mapping'

interface AnomalyCardProps {
  anomaly: AbnormalBalanceExtended
  index: number
  currentType: AccountType
  isManual: boolean
  disabled?: boolean
  onTypeChange: (accountName: string, newType: AccountType, detectedType: AccountType) => void
}

// Sprint 31: Confidence threshold for showing suggestions
const SUGGESTION_DISPLAY_THRESHOLD = 0.5

/**
 * AnomalyCard - Day 10 Risk Dashboard Component
 *
 * Design: "Premium Restraint" - Clay Red accent via left border,
 * not overwhelming solid red blocks. Maintains fintech elegance.
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */
/**
 * AnomalyCard wrapped with React.memo() to prevent unnecessary re-renders.
 * Only re-renders when props change (anomaly, currentType, isManual, disabled).
 */
export const AnomalyCard = memo(function AnomalyCard({
  anomaly,
  index,
  currentType,
  isManual,
  disabled = false,
  onTypeChange,
}: AnomalyCardProps) {
  const [showSuggestions, setShowSuggestions] = useState(false)
  const isHighSeverity = anomaly.severity === 'high' || anomaly.materiality === 'material'

  // Sprint 31: Check if we should show suggestions
  const hasSuggestions = anomaly.suggestions && anomaly.suggestions.length > 0
  const isLowConfidence = (anomaly.confidence ?? 1) < SUGGESTION_DISPLAY_THRESHOLD

  // Memoized handler to prevent AccountTypeDropdown re-renders
  const handleTypeChange = useCallback(
    (newType: AccountType) => {
      onTypeChange(anomaly.account, newType, (anomaly.category as AccountType) || 'unknown')
    },
    [onTypeChange, anomaly.account, anomaly.category]
  )

  // Sprint 31: Handle suggestion acceptance
  const handleSuggestionAccept = useCallback(
    (suggestion: ClassificationSuggestion) => {
      onTypeChange(anomaly.account, suggestion.category, (anomaly.category as AccountType) || 'unknown')
      setShowSuggestions(false)
    },
    [onTypeChange, anomaly.account, anomaly.category]
  )

  // Stagger animation: each card appears 50ms after the previous
  const cardVariants = {
    hidden: {
      opacity: 0,
      x: -20,
      scale: 0.95,
    },
    visible: {
      opacity: 1,
      x: 0,
      scale: 1,
      transition: {
        type: 'spring' as const,
        stiffness: 300,
        damping: 24,
        delay: index * 0.05,
      },
    },
  }

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      className={`
        relative rounded-lg overflow-hidden
        bg-surface-card
        ${isHighSeverity ? 'border-l-4 border-l-clay-500' : 'border-l-4 border-l-oatmeal-400'}
        border border-theme
      `}
    >
      {/* Subtle glow overlay for high severity — CSS animation, 3 cycles */}
      {isHighSeverity && (
        <div className="absolute inset-0 pointer-events-none rounded-lg animate-clay-pulse" />
      )}

      <div className="p-4 relative">
        {/* Header Row */}
        <div className="flex justify-between items-start gap-3">
          <div className="flex items-start gap-3 min-w-0 flex-1">
            {/* Severity Icon */}
            {isHighSeverity ? (
              <div className="mt-0.5 flex-shrink-0">
                <svg
                  className="w-5 h-5 text-clay-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            ) : (
              <div className="mt-0.5 flex-shrink-0">
                <svg
                  className="w-5 h-5 text-content-tertiary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            )}

            {/* Account Info */}
            <div className="min-w-0 flex-1">
              <p className={`font-sans font-medium text-sm truncate ${isHighSeverity ? 'text-content-primary' : 'text-content-primary'}`}>
                {anomaly.account}
              </p>

              {/* Type and Mapping Controls */}
              <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                <AccountTypeDropdown
                  accountName={anomaly.account}
                  currentType={currentType}
                  isManual={isManual}
                  disabled={disabled}
                  onChange={handleTypeChange}
                />
                <MappingIndicator
                  isManual={isManual}
                  confidence={anomaly.confidence}
                  accountName={anomaly.account}
                />
              </div>
            </div>
          </div>

          {/* Amount */}
          <div className="text-right flex-shrink-0">
            <span className={`font-mono text-sm ${isHighSeverity ? 'text-clay-400' : 'text-content-secondary'}`}>
              ${anomaly.amount.toLocaleString()}
            </span>
            {isHighSeverity && (
              <span className="block text-xs text-clay-500 font-sans mt-0.5">
                Material
              </span>
            )}
          </div>
        </div>

        {/* Issue Description */}
        <p className="text-content-tertiary text-xs font-sans mt-2 ml-8">
          {anomaly.issue}
        </p>

        {/* Balance Detail (expandable info) */}
        <div className="mt-2 ml-8 flex items-center gap-4 text-xs font-mono text-content-tertiary">
          <span>Dr: ${anomaly.debit.toLocaleString()}</span>
          <span>Cr: ${anomaly.credit.toLocaleString()}</span>
          {anomaly.expected_balance && anomaly.actual_balance && (
            <span className="text-clay-400/70">
              Expected: {anomaly.expected_balance} / Actual: {anomaly.actual_balance}
            </span>
          )}
        </div>

        {/* Sprint 31: Classification Suggestions for Low-Confidence Accounts */}
        {hasSuggestions && isLowConfidence && !isManual && (
          <div className="mt-3 ml-8">
            <button
              onClick={() => setShowSuggestions(!showSuggestions)}
              disabled={disabled}
              className="flex items-center gap-1.5 text-xs text-sage-400 hover:text-sage-300
                         font-sans transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg
                className={`w-3.5 h-3.5 transition-transform ${showSuggestions ? 'rotate-90' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span>Did you mean? ({anomaly.suggestions?.length} suggestions)</span>
            </button>

            <AnimatePresence>
              {showSuggestions && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="mt-2 space-y-1.5">
                    {anomaly.suggestions?.map((suggestion, idx) => (
                      <button
                        key={`${suggestion.category}-${idx}`}
                        onClick={() => handleSuggestionAccept(suggestion)}
                        disabled={disabled}
                        className="w-full flex items-center justify-between gap-2 p-2
                                   bg-surface-card-secondary hover:bg-surface-card
                                   border border-theme hover:border-sage-500/30
                                   rounded-md transition-all text-left group
                                   disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-sans font-medium text-content-primary">
                              {ACCOUNT_TYPE_LABELS[suggestion.category] || suggestion.category}
                            </span>
                            <span className="text-[10px] font-mono text-content-tertiary">
                              {Math.round(suggestion.confidence * 100)}%
                            </span>
                          </div>
                          <p className="text-[10px] text-content-tertiary truncate mt-0.5">
                            {suggestion.reason}
                          </p>
                        </div>
                        <span className="text-sage-400 text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                          Apply
                        </span>
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>
    </motion.div>
  )
})

// Display name for React DevTools
AnomalyCard.displayName = 'AnomalyCard'

export default AnomalyCard
