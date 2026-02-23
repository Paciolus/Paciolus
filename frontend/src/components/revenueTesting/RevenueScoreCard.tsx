'use client'

import { TestingScoreCard } from '@/components/shared/testing/TestingScoreCard'
import type { RevenueCompositeScore } from '@/types/revenueTesting'

interface RevenueScoreCardProps {
  score: RevenueCompositeScore
}

export function RevenueScoreCard({ score }: RevenueScoreCardProps) {
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
      entity_label="revenue entries"
      title="Revenue Risk Score"
    />
  )
}
