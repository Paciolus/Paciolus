'use client'

import type { InvCompositeScore } from '@/types/inventoryTesting'
import { TestingScoreCard } from '@/components/shared/testing/TestingScoreCard'

interface InventoryScoreCardProps {
  score: InvCompositeScore
}

export function InventoryScoreCard({ score }: InventoryScoreCardProps) {
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
      entity_label="inventory items"
      title="Inventory Risk Score"
    />
  )
}
