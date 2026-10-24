/**
 * Sprint 833: bank-rec split matches are rendered, and the bounded
 * split-match search is disclosed (a Paciolus convention).
 */
import { render, screen } from '@testing-library/react'
import { BankRecMatchTable } from '@/components/bankRec/BankRecMatchTable'
import { SplitSearchNotice } from '@/components/bankRec/SplitSearchNotice'
import type { ReconciliationMatchData } from '@/types/bankRec'

jest.mock('framer-motion', () => ({
  motion: {
    tr: ({ initial, animate, exit, transition, children, ...rest }: any) => <tr {...rest}>{children}</tr>,
  },
}))

const txn = (row: number, amount: number, description: string) => ({
  date: '2026-03-15', description, amount, reference: null, row_number: row,
})

describe('SplitSearchNotice', () => {
  it('emphasises open bank items that were not searched exhaustively', () => {
    render(
      <SplitSearchNotice
        disclosure={{ date_window_days: 0, max_candidates: 20, max_set_size: 4, limited_count: 3, note: 'Bounded search note.' }}
      />,
    )
    expect(screen.getByText('Split matching was limited for 3 open bank items')).toBeInTheDocument()
    expect(screen.getByText('Bounded search note.')).toBeInTheDocument()
  })

  it('still shows the bounds when nothing was limited', () => {
    render(
      <SplitSearchNotice
        disclosure={{ date_window_days: 0, max_candidates: 20, max_set_size: 4, limited_count: 0, note: 'No open bank item exceeded the candidate limit.' }}
      />,
    )
    expect(screen.getByText('Split matching search bounds')).toBeInTheDocument()
  })
})

describe('BankRecMatchTable split rows', () => {
  it('shows a split with the summed ledger amount and flags a capped bank-only item', () => {
    const matches: ReconciliationMatchData[] = [
      {
        match_type: 'split',
        bank_txn: txn(1, 1000, 'Deposit'),
        ledger_txn: txn(1, 600, 'Receipt A'),
        ledger_txns: [txn(1, 600, 'Receipt A'), txn(2, 400, 'Receipt B')],
        match_confidence: 0.85,
      },
      { match_type: 'bank_only', bank_txn: txn(3, 777, 'Unexplained'), match_confidence: 0, split_search_limited: true },
    ]
    render(<BankRecMatchTable matches={matches} />)
    expect(screen.getAllByText('Split Match').length).toBeGreaterThan(0)
    expect(screen.getByText('Split · 2 ledger items')).toBeInTheDocument()
    expect(screen.getAllByText('$1,000.00')).toHaveLength(2) // bank side and summed ledger side
    expect(screen.getByText('Split search not exhaustive')).toBeInTheDocument()
  })
})
