'use client'

/**
 * InsightMicrocopy — Sprint 408: Phase LVII
 *
 * Renders intelligence-flavored contextual messages in the InsightRail.
 * Deterministic: derived from existing workspace data, no AI inference.
 * Feature-flag gated via INSIGHT_MICROCOPY.
 */

import { motion, AnimatePresence } from 'framer-motion'
import { isFeatureEnabled } from '@/lib/featureFlags'
import { deriveInsightMessages, type InsightMessage, type InsightInputs, type InsightTone } from '@/lib/insightMicrocopy'
import { TIMING, EASE, EMPHASIS_SETTLE } from '@/utils/motionTokens'

const TONE_BORDER: Record<InsightTone, string> = {
  attention: 'border-l-clay-400',
  neutral: 'border-l-oatmeal-400',
  positive: 'border-l-sage-400',
}

interface InsightMicrocopyProps extends InsightInputs {
  isLoading: boolean
}

export function InsightMicrocopy(props: InsightMicrocopyProps) {
  if (!isFeatureEnabled('INSIGHT_MICROCOPY')) return null

  const { isLoading, ...inputs } = props

  if (isLoading) return null

  const messages = deriveInsightMessages(inputs)

  if (messages.length === 0) return null

  return (
    <div>
      <span className="text-[10px] font-sans font-medium text-content-tertiary uppercase tracking-wider block mb-2">
        Intelligence Briefing
      </span>
      <div className="space-y-2">
        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={`${msg.tone}-${i}`}
              variants={EMPHASIS_SETTLE}
              initial="initial"
              animate="animate"
              className={`rounded-lg border-l-[3px] ${TONE_BORDER[msg.tone]} bg-surface-card-secondary/60 px-3 py-2`}
            >
              <p className="text-[10px] font-sans text-content-secondary leading-relaxed">
                {msg.text}
              </p>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
