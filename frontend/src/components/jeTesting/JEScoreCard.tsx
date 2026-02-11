'use client'

import type { JECompositeScore } from '@/types/jeTesting'
import { TestingScoreCard } from '@/components/shared/testing/TestingScoreCard'

interface JEScoreCardProps {
  score: JECompositeScore
}

export function JEScoreCard({ score }: JEScoreCardProps) {
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
      entity_label="journal entries"
    />
  )
}
