'use client'

import { useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { AbnormalBalanceExtended, AccountType, RiskSummary } from '@/types/mapping'
import { AnomalyCard } from './AnomalyCard'

interface RiskDashboardProps {
  anomalies: AbnormalBalanceExtended[]
  riskSummary?: RiskSummary
  materialityThreshold: number
  disabled?: boolean
  getMappingForAccount: (accountName: string) => {
    currentType: AccountType
    isManual: boolean
  }
  onTypeChange: (accountName: string, type: AccountType, detectedType: AccountType) => void
}

/**
 * RiskDashboard - Day 10 Component
 *
 * Displays anomalies detected during trial balance audit with animated
 * AnomalyCard components. Uses "premium restraint" design philosophy.
 *
 * Features:
 * - Staggered animations via framer-motion
 * - Collapsible low-severity (immaterial) section
 * - Risk summary header
 *
 * See: logs/dev-log.md for IP documentation
 */
export function RiskDashboard({
  anomalies,
  riskSummary,
  materialityThreshold,
  disabled = false,
  getMappingForAccount,
  onTypeChange,
}: RiskDashboardProps) {
  const [showLowSeverity, setShowLowSeverity] = useState(false)


  // Separate anomalies by severity
  const { highSeverity, lowSeverity } = useMemo(() => {
    const high: AbnormalBalanceExtended[] = []
    const low: AbnormalBalanceExtended[] = []

    anomalies.forEach((a) => {
      if (a.severity === 'high' || a.materiality === 'material') {
        high.push(a)
      } else {
        low.push(a)
      }
    })

    return { highSeverity: high, lowSeverity: low }
  }, [anomalies])

  // Container animation
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
        delayChildren: 0.1,
      },
    },
  }

  if (anomalies.length === 0) {
    return null
  }

  return (
    <div className="space-y-6 max-w-md mx-auto">
      {/* Risk Summary Header */}
      {riskSummary && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between bg-surface-card rounded-xl p-4 border border-theme"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-clay-500/10 flex items-center justify-center">
              <svg
                className="w-5 h-5 text-clay-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <div>
              <h3 className="text-content-primary font-serif font-semibold">
                Risk Dashboard
              </h3>
              <p className="text-content-tertiary text-xs font-sans">
                {riskSummary.total_anomalies} anomal{riskSummary.total_anomalies === 1 ? 'y' : 'ies'} detected
              </p>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="flex items-center gap-4 text-xs font-mono">
            {riskSummary.high_severity > 0 && (
              <div className="text-clay-400">
                <span className="text-lg font-bold">{riskSummary.high_severity}</span>
                <span className="block text-content-tertiary font-sans">High</span>
              </div>
            )}
            {riskSummary.low_severity > 0 && (
              <div className="text-content-secondary">
                <span className="text-lg font-bold">{riskSummary.low_severity}</span>
                <span className="block text-content-tertiary font-sans">Low</span>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* High Severity Section */}
      {highSeverity.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-clay-500" />
            <span className="text-clay-400 font-sans font-medium text-sm">
              Material Risks ({highSeverity.length})
            </span>
            <span className="text-content-tertiary text-xs font-sans">
              &ge; ${materialityThreshold.toLocaleString()}
            </span>
          </div>

          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="space-y-3"
          >
            {highSeverity.map((anomaly, index) => {
              const mapping = getMappingForAccount(anomaly.account)
              return (
                <AnomalyCard
                  key={`${anomaly.account}-${index}`}
                  anomaly={anomaly}
                  index={index}
                  currentType={mapping.currentType}
                  isManual={mapping.isManual}
                  disabled={disabled}
                  onTypeChange={onTypeChange}
                />
              )
            })}
          </motion.div>
        </div>
      )}

      {/* Low Severity Section (Collapsible) */}
      {lowSeverity.length > 0 && (
        <div className="border border-theme rounded-xl overflow-hidden">
          <button
            onClick={() => setShowLowSeverity(!showLowSeverity)}
            className="w-full flex items-center justify-between p-4 bg-surface-card-secondary hover:bg-surface-card transition-colors"
            aria-expanded={showLowSeverity}
          >
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-content-tertiary" />
              <span className="text-content-secondary font-sans font-medium text-sm">
                Indistinct Items ({lowSeverity.length})
              </span>
              <span className="text-content-tertiary text-xs font-sans">
                &lt; ${materialityThreshold.toLocaleString()}
              </span>
            </div>
            <motion.svg
              animate={{ rotate: showLowSeverity ? 180 : 0 }}
              transition={{ duration: 0.2 }}
              className="w-5 h-5 text-content-tertiary"
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

          <AnimatePresence>
            {showLowSeverity && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className="overflow-hidden"
              >
                <motion.div
                  variants={containerVariants}
                  initial="hidden"
                  animate="visible"
                  className="p-4 space-y-3"
                >
                  {lowSeverity.map((anomaly, index) => {
                    const mapping = getMappingForAccount(anomaly.account)
                    return (
                      <AnomalyCard
                        key={`${anomaly.account}-${index}`}
                        anomaly={anomaly}
                        index={index}
                        currentType={mapping.currentType}
                        isManual={mapping.isManual}
                        disabled={disabled}
                        onTypeChange={onTypeChange}
                      />
                    )
                  })}
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}

export default RiskDashboard
