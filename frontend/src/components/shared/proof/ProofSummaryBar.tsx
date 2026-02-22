'use client'

import { motion } from 'framer-motion'
import type { ProofConfidenceLevel, ProofSummary } from '@/types/proof'
import { EASE } from '@/utils/motionTokens'

// =============================================================================
// Color semantics — calm by default, clay only for problematic metrics
// =============================================================================

const LEVEL_STYLES: Record<ProofConfidenceLevel, { bg: string; text: string; border: string }> = {
  strong: { bg: 'bg-sage-50', text: 'text-sage-700', border: 'border-sage-200' },
  adequate: { bg: 'bg-sage-50/60', text: 'text-sage-600', border: 'border-sage-200/60' },
  limited: { bg: 'bg-oatmeal-100', text: 'text-oatmeal-700', border: 'border-oatmeal-300' },
  insufficient: { bg: 'bg-clay-50', text: 'text-clay-700', border: 'border-clay-200' },
}

const METRIC_TEXT_COLOR: Record<ProofConfidenceLevel, string> = {
  strong: 'text-sage-700',
  adequate: 'text-sage-600',
  limited: 'text-oatmeal-700',
  insufficient: 'text-clay-700',
}

const DOT_COLOR: Record<ProofConfidenceLevel, string> = {
  strong: 'bg-sage-500',
  adequate: 'bg-sage-400',
  limited: 'bg-oatmeal-500',
  insufficient: 'bg-clay-500',
}

// =============================================================================
// Component
// =============================================================================

export interface ProofSummaryBarProps {
  proof: ProofSummary
}

export function ProofSummaryBar({ proof }: ProofSummaryBarProps) {
  const style = LEVEL_STYLES[proof.overallLevel]

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.3,
        ease: proof.overallLevel === 'insufficient' ? EASE.emphasis : ('easeOut' as const),
      }}
      className={`${style.bg} border ${style.border} rounded-xl p-4`}
      role="region"
      aria-label="Evidence summary"
    >
      {/* Header row */}
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-2 h-2 rounded-full ${DOT_COLOR[proof.overallLevel]}`} />
        <span className={`font-serif text-sm font-medium ${style.text}`}>
          Evidence Summary
        </span>
      </div>

      {/* Metrics strip */}
      <div className="flex items-center gap-4 flex-wrap mb-2">
        <MetricCell metric={proof.dataCompleteness} />
        <Separator />
        <MetricCell metric={proof.columnConfidence} />
        <Separator />
        <MetricCell metric={proof.testCoverage} />
        <Separator />
        <MetricCell metric={proof.unresolvedItems} />
      </div>

      {/* Narrative */}
      <p className="font-sans text-xs text-content-secondary leading-relaxed">
        {proof.narrativeCopy}
      </p>
    </motion.div>
  )
}

// =============================================================================
// Sub-components
// =============================================================================

function MetricCell({ metric }: { metric: { label: string; displayValue: string; level: ProofConfidenceLevel } }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="font-sans text-xs text-content-tertiary">{metric.label}:</span>
      <span className={`type-num-xs font-medium ${METRIC_TEXT_COLOR[metric.level]}`}>
        {metric.displayValue}
      </span>
    </div>
  )
}

function Separator() {
  return <div className="w-px h-3 bg-oatmeal-300/50" />
}
