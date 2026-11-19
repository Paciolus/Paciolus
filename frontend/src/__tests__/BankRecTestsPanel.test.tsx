/**
 * Sprint 886 (review OUT-10): the bank rec screen shows the run's tests, score
 * and aging — the figures the memo and CSV carry — with the same labels and a
 * one-decimal score. A block the response did not carry says "Not available".
 */
import { BankRecTestsPanel } from '@/components/bankRec/BankRecTestsPanel'
import type { BankRecResult } from '@/types/bankRec'
import { render, screen, within } from '@/test-utils'

const base: BankRecResult = {
  summary: { matched_count: 1, matched_amount: 5000, bank_only_count: 2, bank_only_amount: 19975, ledger_only_count: 2, ledger_only_amount: 500, reconciling_difference: 19475, total_bank: 24975, total_ledger: 5500, matches: [] },
  bank_column_detection: { requires_mapping: false, detection_notes: [] } as never,
  ledger_column_detection: { requires_mapping: false, detection_notes: [] } as never,
}

const full: BankRecResult = {
  ...base,
  composite_score: { score: 40, risk_tier: 'elevated', total_flagged: 4, flag_rate: 0.8, flags_by_severity: { high: 1, medium: 2, low: 1 }, tests_run: 5, total_entries: 5, top_findings: [] },
  rec_tests: [
    { test_name: 'Stale Deposits (>10 days)', flagged_count: 1, severity: 'medium' },
    { test_name: 'Stale Checks (>90 days)', flagged_count: 1, severity: 'medium' },
    { test_name: 'High Value (>Materiality)', flagged_count: 2, severity: 'high' },
  ],
  outstanding_aging: [
    { category: 'bank_only', total_count: 2, over_10_days: 0, over_30_days: 0, oldest_item_days: 0, oldest_item_date: '2026-03-31', oldest_item_amount: -25 },
    { category: 'ledger_only', total_count: 2, over_10_days: 2, over_30_days: 1, oldest_item_days: 131, oldest_item_date: '2025-11-20', oldest_item_amount: -300 },
  ],
}

describe('BankRecTestsPanel', () => {
  it('shows the score with one decimal and the tier', () => {
    render(<BankRecTestsPanel result={full} />)
    const score = screen.getByTestId('bank-rec-score')
    expect(score).toHaveTextContent('40.0 / 100')
    expect(score).toHaveTextContent('ELEVATED')
  })

  it('lists each test with its flagged count', () => {
    render(<BankRecTestsPanel result={full} />)
    const rows = within(screen.getByTestId('bank-rec-tests')).getAllByRole('row').slice(1)
    expect(rows.map((r) => r.textContent)).toEqual([
      'Stale Deposits (>10 days)1MEDIUM',
      'Stale Checks (>90 days)1MEDIUM',
      'High Value (>Materiality)2HIGH',
    ])
  })

  it('shows the aging per category as the engine aged it', () => {
    render(<BankRecTestsPanel result={full} />)
    const rows = within(screen.getByTestId('bank-rec-aging')).getAllByRole('row').slice(1)
    expect(rows[0]).toHaveTextContent('Bank only2000 days (2026-03-31), $25.00')
    expect(rows[1]).toHaveTextContent('Ledger only221131 days (2025-11-20), $300.00')
  })

  it('says Not available — never 0 or LOW — when the response carried none of it', () => {
    render(<BankRecTestsPanel result={base} />)
    expect(screen.getByTestId('bank-rec-score')).toHaveTextContent('Not available')
    expect(screen.getByTestId('bank-rec-score')).toHaveTextContent('Not evaluated')
    expect(screen.getByTestId('bank-rec-score')).not.toHaveTextContent('LOW')
    expect(screen.getByText('Reconciliation tests: Not available')).toBeInTheDocument()
    expect(screen.getByText('Aging: Not available')).toBeInTheDocument()
  })
})
