'use client'

import type { PayrollCompositeScore } from '@/types/payrollTesting'
import { TestingScoreCard } from '@/components/shared/testing/TestingScoreCard'

interface PayrollScoreCardProps {
  score: PayrollCompositeScore
}

export function PayrollScoreCard({ score }: PayrollScoreCardProps) {
  // Payroll has structured top_findings — render as "employee: issue"
  const findingStrings = score.top_findings.map(
    (f) => `${f.employee}: ${f.issue}`
  )

  return (
    <TestingScoreCard
      score={score.score}
      risk_tier={score.risk_tier}
      tests_run={score.tests_run}
      total_entries={score.total_entries}
      total_flagged={score.total_flagged}
      flag_rate={score.flag_rate}
      flags_by_severity={score.flags_by_severity}
      top_findings={findingStrings}
      entity_label="employees"
      findings_renderer={(findings) => (
        <div className="space-y-1.5">
          {score.top_findings.slice(0, 3).map((finding, i) => (
            <p key={i} className="font-sans text-sm text-content-primary">
              <span className="text-content-tertiary mr-2">{i + 1}.</span>
              <span className="text-content-secondary">{finding.employee}</span>
              <span className="text-content-tertiary mx-1">&mdash;</span>
              {finding.issue}
            </p>
          ))}
        </div>
      )}
    />
  )
}
