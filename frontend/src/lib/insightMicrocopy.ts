/**
 * Insight Microcopy — Sprint 408: Phase LVII
 *
 * Deterministic text generation from existing workspace insight data.
 * No AI inference, no API calls. Pure function from data → messages.
 *
 * Language guidelines (ISA-compliant, factual):
 * - Use: "surfaced", "observed", "detected", "identified", "noted"
 * - Never: "should", "must", "deficiency", "weakness", "recommend"
 */

import type { RiskSignal, ProofReadiness } from '@/hooks/useWorkspaceInsights'
import type { FollowUpSummary, ToolRunTrend } from '@/types/engagement'

export type InsightTone = 'attention' | 'neutral' | 'positive'

export interface InsightMessage {
  tone: InsightTone
  text: string
}

const TONE_ORDER: Record<InsightTone, number> = {
  attention: 0,
  neutral: 1,
  positive: 2,
}

const MAX_MESSAGES = 3

export interface InsightInputs {
  riskSignals: RiskSignal[]
  followUpSummary: FollowUpSummary | null
  toolRunTrends: ToolRunTrend[]
  toolsCovered: number
  totalTools: number
  proofReadiness: ProofReadiness
}

/**
 * Derive up to 3 intelligence-flavored insight messages from workspace data.
 * Sorted: attention → neutral → positive.
 */
export function deriveInsightMessages(inputs: InsightInputs): InsightMessage[] {
  const messages: InsightMessage[] = []

  const { riskSignals, followUpSummary, toolRunTrends, toolsCovered, totalTools, proofReadiness } = inputs

  // 1. High-severity risk signals → attention
  const highSignals = riskSignals.filter(s => s.level === 'high')
  if (highSignals.length > 0) {
    const clusterCount = highSignals.length
    messages.push({
      tone: 'attention',
      text: `${clusterCount} unusual cluster${clusterCount !== 1 ? 's' : ''} surfaced across active diagnostics`,
    })
  }

  // 2. Unreviewed follow-ups → attention
  if (followUpSummary) {
    const notReviewed = followUpSummary.by_disposition?.['not_reviewed'] ?? 0
    if (notReviewed > 0) {
      messages.push({
        tone: 'attention',
        text: `${notReviewed} follow-up item${notReviewed !== 1 ? 's' : ''} pending disposition`,
      })
    }
  }

  // 3. Evidence density below threshold → neutral
  if (proofReadiness.level === 'insufficient' || proofReadiness.level === 'limited') {
    messages.push({
      tone: 'neutral',
      text: `Evidence density below threshold \u2014 ${proofReadiness.percentage}% coverage observed`,
    })
  }

  // 4. Tool coverage gaps → neutral
  const uncovered = totalTools - toolsCovered
  if (uncovered > 0 && toolsCovered > 0) {
    messages.push({
      tone: 'neutral',
      text: `${uncovered} diagnostic lens${uncovered !== 1 ? 'es' : ''} remain${uncovered === 1 ? 's' : ''} unused`,
    })
  }

  // 5. Degrading trends → attention
  const degrading = toolRunTrends.filter(t => t.direction === 'degrading')
  if (degrading.length > 0) {
    messages.push({
      tone: 'attention',
      text: `Score regression detected in ${degrading.length} tool${degrading.length !== 1 ? 's' : ''}`,
    })
  }

  // 6. All tools covered + strong evidence → positive
  if (toolsCovered === totalTools && totalTools > 0 && proofReadiness.level === 'strong') {
    messages.push({
      tone: 'positive',
      text: 'Full diagnostic coverage achieved with strong evidence density',
    })
  }

  // 7. Improving trends → positive
  const improving = toolRunTrends.filter(t => t.direction === 'improving')
  if (improving.length >= 2) {
    messages.push({
      tone: 'positive',
      text: `${improving.length} tools showing score improvement across runs`,
    })
  }

  // Sort by tone priority and limit to MAX_MESSAGES
  messages.sort((a, b) => TONE_ORDER[a.tone] - TONE_ORDER[b.tone])

  return messages.slice(0, MAX_MESSAGES)
}
