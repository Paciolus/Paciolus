/**
 * SODResults — Sprint 827 (D2): permissions no rule recognises are surfaced,
 * so a clean result built from unmatched spellings does not read as clean.
 */
import { render, screen } from '@testing-library/react'
import { SODResults } from '@/components/sod/SODResults'
import type { SODAnalysisResponse } from '@/types/sod'

const base: SODAnalysisResponse = {
  conflicts: [],
  user_summaries: [],
  rules_evaluated: 12,
  users_evaluated: 1,
  users_with_conflicts: 0,
  high_risk_users: 0,
}

describe('SODResults unmatched permissions', () => {
  it('lists permissions that no rule recognises', () => {
    render(<SODResults result={{ ...base, unmatched_permissions: ['ap-invoice-create', 'ap.payment.release'] }} />)
    expect(screen.getByText('2 permissions not recognised by any rule')).toBeInTheDocument()
    expect(screen.getByText('ap-invoice-create, ap.payment.release')).toBeInTheDocument()
  })

  it('shows nothing extra when every permission is recognised', () => {
    render(<SODResults result={{ ...base, unmatched_permissions: [] }} />)
    expect(screen.queryByText(/not recognised by any rule/)).not.toBeInTheDocument()
  })
})

describe('SODResults tier basis (Sprint 833)', () => {
  it('shows why a single-HIGH-conflict user is tiered high', () => {
    render(
      <SODResults
        result={{
          ...base,
          users_with_conflicts: 1,
          high_risk_users: 1,
          user_summaries: [
            {
              user_id: 'u1',
              user_name: 'Poster',
              conflict_count: 1,
              high_severity_count: 1,
              medium_severity_count: 0,
              low_severity_count: 0,
              risk_score: 3,
              risk_tier: 'high',
              risk_tier_reason: 'Tiered high: at least one HIGH-severity conflict',
            },
          ],
        }}
      />,
    )
    expect(screen.getByText('Tiered high: at least one HIGH-severity conflict')).toBeInTheDocument()
  })
})
