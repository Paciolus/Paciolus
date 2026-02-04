'use client'

import { useCallback } from 'react'
import { motion } from 'framer-motion'
import type { AbnormalBalanceExtended, AccountType } from '@/types/mapping'
import { ACCOUNT_TYPE_LABELS } from '@/types/mapping'
import { AccountTypeDropdown, MappingIndicator } from '@/components/mapping'

interface AnomalyCardProps {
  anomaly: AbnormalBalanceExtended
  index: number
  currentType: AccountType
  isManual: boolean
  disabled?: boolean
  onTypeChange: (accountName: string, newType: AccountType, detectedType: AccountType) => void
}

/**
 * AnomalyCard - Day 10 Risk Dashboard Component
 *
 * Design: "Premium Restraint" - Clay Red accent via left border,
 * not overwhelming solid red blocks. Maintains fintech elegance.
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */
export function AnomalyCard({
  anomaly,
  index,
  currentType,
  isManual,
  disabled = false,
  onTypeChange,
}: AnomalyCardProps) {
  const isHighSeverity = anomaly.severity === 'high' || anomaly.materiality === 'material'

  // Memoized handler to prevent AccountTypeDropdown re-renders
  const handleTypeChange = useCallback(
    (newType: AccountType) => {
      onTypeChange(anomaly.account, newType, (anomaly.category as AccountType) || 'unknown')
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

  // Subtle glow effect for high severity
  const glowVariants = {
    initial: { boxShadow: '0 0 0 0 rgba(188, 71, 73, 0)' },
    animate: {
      boxShadow: isHighSeverity
        ? [
            '0 0 0 0 rgba(188, 71, 73, 0)',
            '0 0 8px 2px rgba(188, 71, 73, 0.15)',
            '0 0 0 0 rgba(188, 71, 73, 0)',
          ]
        : '0 0 0 0 rgba(188, 71, 73, 0)',
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut' as const,
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
        bg-obsidian-800/50
        ${isHighSeverity ? 'border-l-4 border-l-clay-500' : 'border-l-4 border-l-oatmeal-500/30'}
        border border-obsidian-600/50
      `}
    >
      {/* Subtle glow overlay for high severity */}
      {isHighSeverity && (
        <motion.div
          className="absolute inset-0 pointer-events-none rounded-lg"
          variants={glowVariants}
          initial="initial"
          animate="animate"
        />
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
                  className="w-5 h-5 text-oatmeal-500"
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
              <p className={`font-sans font-medium text-sm truncate ${isHighSeverity ? 'text-oatmeal-200' : 'text-oatmeal-300'}`}>
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
            <span className={`font-mono text-sm ${isHighSeverity ? 'text-clay-400' : 'text-oatmeal-400'}`}>
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
        <p className="text-oatmeal-500 text-xs font-sans mt-2 ml-8">
          {anomaly.issue}
        </p>

        {/* Balance Detail (expandable info) */}
        <div className="mt-2 ml-8 flex items-center gap-4 text-xs font-mono text-oatmeal-500">
          <span>Dr: ${anomaly.debit.toLocaleString()}</span>
          <span>Cr: ${anomaly.credit.toLocaleString()}</span>
          {anomaly.expected_balance && anomaly.actual_balance && (
            <span className="text-clay-400/70">
              Expected: {anomaly.expected_balance} / Actual: {anomaly.actual_balance}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export default AnomalyCard
