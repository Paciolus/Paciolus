/**
 * Sprint 886 (review OUT-11): three-way match shows the engine's own
 * classification, worded as the memo and CSV word it ("Risk assessment: MEDIUM"),
 * and no score.
 */
import { MatchSummaryCard } from '@/components/threeWayMatch/MatchSummaryCard'
import type { ThreeWayMatchSummaryData } from '@/types/threeWayMatch'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, children, ...rest }: any) => <div {...rest}>{children}</div> },
}))

const summary = (risk: 'low' | 'medium' | 'high') =>
  ({
    total_pos: 10, total_invoices: 10, total_receipts: 10, full_match_count: 10, partial_match_count: 0,
    full_match_rate: 1, partial_match_rate: 0, total_po_amount: 10000, total_invoice_amount: 10000,
    total_receipt_amount: 0, net_variance: 0, material_variances_count: 0, risk_assessment: risk,
  }) as unknown as ThreeWayMatchSummaryData

describe('MatchSummaryCard risk assessment', () => {
  it.each(['low', 'medium', 'high'] as const)('shows %s in the engine wording, with no score', (risk) => {
    const { container } = render(<MatchSummaryCard summary={summary(risk)} />)
    expect(screen.getByText(`Risk assessment: ${risk.toUpperCase()}`)).toBeInTheDocument()
    expect(container).not.toHaveTextContent('/100')
    expect(container).not.toHaveTextContent(/MODERATE|ELEVATED/)
  })
})
