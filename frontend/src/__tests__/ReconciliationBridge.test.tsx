/**
 * ReconciliationBridge — Sprint 829
 *
 * Reconciling items adjust the side that has not recorded them: outstanding
 * checks and deposits in transit adjust the bank; bank charges and credits not
 * yet booked adjust the GL. With the populations crossed the bridge did not tie.
 */

import { ReconciliationBridge } from '@/components/bankRec/ReconciliationBridge'
import type { ReconciliationSummaryData } from '@/types/bankRec'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

const txn = (amount: number, description: string) => ({ date: '2026-09-30', description, amount, reference: null, row_number: 1 })

describe('ReconciliationBridge', () => {
  it('ties when every item is placed on the side that has not recorded it', () => {
    const summary: ReconciliationSummaryData = {
      matched_count: 1,
      matched_amount: 1000,
      bank_only_count: 2,
      bank_only_amount: 37,
      ledger_only_count: 2,
      ledger_only_amount: 9200,
      reconciling_difference: 0,
      // Transaction totals: matched 1000 + bank-only (−25, +12); matched 1000 + ledger-only (−1200, +8000)
      total_bank: 987,
      total_ledger: 7800,
      matches: [
        { match_type: 'matched', bank_txn: txn(1000, 'Deposit'), ledger_txn: txn(1000, 'Deposit'), match_confidence: 1 },
        { match_type: 'bank_only', bank_txn: txn(-25, 'Service charge'), match_confidence: 0 },
        { match_type: 'bank_only', bank_txn: txn(12, 'Interest'), match_confidence: 0 },
        { match_type: 'ledger_only', ledger_txn: txn(-1200, 'Check 1003'), match_confidence: 0 },
        { match_type: 'ledger_only', ledger_txn: txn(8000, 'Deposit in transit'), match_confidence: 0 },
      ],
    }
    render(<ReconciliationBridge summary={summary} />)

    expect(screen.getByText('Less: Outstanding Checks').nextSibling).toHaveTextContent('-$1,200.00')
    expect(screen.getByText('Plus: Deposits in Transit').nextSibling).toHaveTextContent('$8,000.00')
    expect(screen.getByText('Less: Bank Charges Not Yet Recorded').nextSibling).toHaveTextContent('-$25.00')
    expect(screen.getByText('Reconciling Difference').nextSibling).toHaveTextContent('$0.00')
  })
})
