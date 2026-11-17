/**
 * Sprint 879b (DH-04): proposed actuals are saved only by an explicit action.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { ProposedActualsPanel } from '@/components/engagement/ProposedActualsPanel'
import type { ProposedActual } from '@/types/analytical-expectations'

const mockApiPost = jest.fn()
jest.mock('@/utils', () => ({
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  formatCurrency: (n: number) => `$${n.toFixed(2)}`,
}))

const proposals: ProposedActual[] = [
  { expectation_id: 1, target_type: 'account', target_label: 'Cash', actual: 5500, variance: 0, status: 'within_threshold', capture_token: 'tok-cash' },
  { expectation_id: 2, target_type: 'balance', target_label: 'Revenue', actual: -1020, variance: -20, status: 'within_threshold', capture_token: 'tok-rev' },
]

describe('ProposedActualsPanel', () => {
  beforeEach(() => {
    mockApiPost.mockReset()
  })

  it('saves nothing on render and says so', () => {
    render(<ProposedActualsPanel engagementId={7} proposals={proposals} token="t" />)
    expect(mockApiPost).not.toHaveBeenCalled()
    expect(screen.getByText(/Nothing from this run has been saved/)).toBeInTheDocument()
  })

  it('captures one account with its own token', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: { results: [{ expectation_id: 1, status: 'captured', reason: null }] } })
    render(<ProposedActualsPanel engagementId={7} proposals={proposals} token="t" />)
    fireEvent.click(screen.getByRole('button', { name: 'Save actual value for Cash' }))
    await waitFor(() => expect(screen.getByText('Saved')).toBeInTheDocument())
    expect(mockApiPost).toHaveBeenCalledWith(
      '/engagements/7/analytical-expectations/capture-actuals',
      't',
      { capture_tokens: ['tok-cash'] },
    )
    expect(screen.getByRole('button', { name: 'Save actual value for Revenue' })).toBeInTheDocument()
  })

  it('captures every proposal from the run at once', async () => {
    mockApiPost.mockResolvedValue({
      ok: true,
      data: { results: [
        { expectation_id: 1, status: 'captured', reason: null },
        { expectation_id: 2, status: 'skipped', reason: 'already_captured' },
      ] },
    })
    render(<ProposedActualsPanel engagementId={7} proposals={proposals} token="t" />)
    fireEvent.click(screen.getByRole('button', { name: 'Save all 2 actual values from this run' }))
    await waitFor(() => expect(screen.getByText('Already captured')).toBeInTheDocument())
    expect(mockApiPost.mock.calls[0][2]).toEqual({ capture_tokens: ['tok-cash', 'tok-rev'] })
  })

  it('shows an error and keeps the buttons when saving fails', async () => {
    mockApiPost.mockResolvedValue({ ok: false, error: 'Plan required' })
    render(<ProposedActualsPanel engagementId={7} proposals={proposals} token="t" />)
    fireEvent.click(screen.getByRole('button', { name: 'Save actual value for Cash' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Plan required'))
    expect(screen.getByRole('button', { name: 'Save actual value for Cash' })).toBeInTheDocument()
  })

  it('renders nothing when there are no proposals', () => {
    const { container } = render(<ProposedActualsPanel engagementId={7} proposals={[]} token="t" />)
    expect(container).toBeEmptyDOMElement()
  })
})
