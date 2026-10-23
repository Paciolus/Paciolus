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
