'use client'

import type { ARCompositeScore } from '@/types/arAging'
import { TestingScoreCard } from '@/components/shared/testing/TestingScoreCard'

interface ARScoreCardProps {
  score: ARCompositeScore
}

export function ARScoreCard({ score }: ARScoreCardProps) {
  return (
    <TestingScoreCard
      score={score.score}
      risk_tier={score.risk_tier}
      tests_run={score.tests_run}
      total_entries={0}
      total_flagged={score.total_flagged}
      flag_rate={0}
      flags_by_severity={score.flags_by_severity}
      top_findings={score.top_findings}
      entity_label="items"
      title="AR Aging Risk Score"
      subtitle_override={
        <p className="font-sans text-content-secondary text-sm mb-4">
          {score.tests_run} tests run{score.tests_skipped > 0 && `, ${score.tests_skipped} skipped`}
          {' \u2014 '}
          {score.has_subledger ? 'Full analysis (TB + Sub-Ledger)' : 'TB-only analysis'}
        </p>
      }
      stats_override={
        <div className="grid grid-cols-3 gap-4">
          <div>
            <span className="font-mono text-lg text-content-primary">{score.total_flagged.toLocaleString()}</span>
            <p className="text-content-secondary text-xs font-sans">Flagged</p>
          </div>
          <div>
            <span className="font-mono text-lg text-content-primary">
              {score.has_subledger ? 'Full' : 'TB-Only'}
            </span>
            <p className="text-content-secondary text-xs font-sans">Mode</p>
          </div>
          <div>
            <span className="font-mono text-lg text-clay-600">{score.flags_by_severity.high}</span>
            <span className="font-mono text-sm text-content-secondary"> / {score.flags_by_severity.medium}</span>
            <span className="font-mono text-sm text-content-tertiary"> / {score.flags_by_severity.low}</span>
            <p className="text-content-secondary text-xs font-sans">H / M / L</p>
          </div>
        </div>
      }
    />
  )
}
