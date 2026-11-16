'use client'

import { TestingScoreCard } from '@/components/shared/testing/TestingScoreCard'
import type { JECompositeScore } from '@/types/jeTesting'

interface JEScoreCardProps {
  score: JECompositeScore
}

// Sprint 869: total_entries counts GL lines (one per row), not journal entries.
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
      score_basis={score.score_basis}
      entity_label="GL lines"
    />
  )
}
