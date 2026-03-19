/**
 * ProofTraceBar component tests
 *
 * Tests: rendering with test data, empty state, legend display,
 * proportion segments, aria label.
 */
import { ProofTraceBar } from '@/components/shared/proof/ProofTraceBar'
import { render, screen } from '@/test-utils'

describe('ProofTraceBar', () => {
  it('renders nothing when no test details', () => {
    const { container } = render(<ProofTraceBar testDetails={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders bar with clear/flagged counts', () => {
    const details = [
      { test_key: 't1', test_name: 'Test 1', status: 'clear' as const, description: '' },
      { test_key: 't2', test_name: 'Test 2', status: 'flagged' as const, description: '' },
    ]
    render(<ProofTraceBar testDetails={details} />)
    expect(screen.getByText('clear: 1')).toBeInTheDocument()
    expect(screen.getByText('flagged: 1')).toBeInTheDocument()
  })

  it('shows skipped count when present', () => {
    const details = [
      { test_key: 't1', test_name: 'Test 1', status: 'clear' as const, description: '' },
      { test_key: 't2', test_name: 'Test 2', status: 'skipped' as const, description: '' },
    ]
    render(<ProofTraceBar testDetails={details} />)
    expect(screen.getByText('skipped: 1')).toBeInTheDocument()
  })

  it('does not show skipped legend when no skipped tests', () => {
    const details = [
      { test_key: 't1', test_name: 'Test 1', status: 'clear' as const, description: '' },
      { test_key: 't2', test_name: 'Test 2', status: 'flagged' as const, description: '' },
    ]
    render(<ProofTraceBar testDetails={details} />)
    expect(screen.queryByText(/skipped/)).not.toBeInTheDocument()
  })

  it('has accessible aria-label', () => {
    const details = [
      { test_key: 't1', test_name: 'Test 1', status: 'clear' as const, description: '' },
      { test_key: 't2', test_name: 'Test 2', status: 'flagged' as const, description: '' },
      { test_key: 't3', test_name: 'Test 3', status: 'clear' as const, description: '' },
    ]
    render(<ProofTraceBar testDetails={details} />)
    const bar = screen.getByRole('img')
    expect(bar).toHaveAttribute('aria-label', 'Test results: 2 clear, 1 flagged, 0 skipped out of 3')
  })

  it('renders all clear segments correctly', () => {
    const details = [
      { test_key: 't1', test_name: 'Test 1', status: 'clear' as const, description: '' },
      { test_key: 't2', test_name: 'Test 2', status: 'clear' as const, description: '' },
    ]
    render(<ProofTraceBar testDetails={details} />)
    expect(screen.getByText('clear: 2')).toBeInTheDocument()
    expect(screen.getByText('flagged: 0')).toBeInTheDocument()
  })
})
