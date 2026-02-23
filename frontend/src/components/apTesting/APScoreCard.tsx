'use client'

import { TestingScoreCard } from '@/components/shared/testing/TestingScoreCard'
import type { APCompositeScore } from '@/types/apTesting'

interface APScoreCardProps {
  score: APCompositeScore
}

export function APScoreCard({ score }: APScoreCardProps) {
  return (
    <TestingScoreCard
      score={score.score}
      risk_tier={score.risk_tier}
      tests_run={score.tests_run}
      total_entries={score.total_entries}
      total_flagged={score.total_flagged}
      flag_rate={score.flag_rate}
      flags_by_severity={score.flags_by_severity}
      top_findings={score.top_findings}
      entity_label="payments"
    />
  )
}
