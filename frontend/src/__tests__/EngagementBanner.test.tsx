/**
 * EngagementBanner component tests
 *
 * Tests: hidden when no engagement, visible with engagement data,
 * client name resolution, period formatting, Unlink action.
 */
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

const mockGetClient = jest.fn()
jest.mock('@/hooks/useClients', () => ({
  useClients: () => ({ getClient: mockGetClient }),
}))

import { EngagementBanner } from '@/components/engagement/EngagementBanner'
import type { Engagement } from '@/types/engagement'

const mockEngagement: Engagement = {
  id: 1,
  client_id: 42,
  period_start: '2025-01-01',
  period_end: '2025-12-31',
  status: 'active',
  materiality_basis: 'revenue',
  materiality_percentage: 5,
  materiality_amount: 50000,
  performance_materiality_factor: 0.75,
  trivial_threshold_factor: 0.05,
  created_by: 1,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
}

describe('EngagementBanner', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockGetClient.mockResolvedValue({ name: 'Acme Corp' })
  })

  it('renders nothing when no engagement is active', () => {
    const { container } = render(
      <EngagementBanner activeEngagement={null} onUnlink={jest.fn()} />
    )
    expect(container.textContent).toBe('')
  })

  it('shows "Linked to Diagnostic Workspace" when engagement is active', () => {
    render(<EngagementBanner activeEngagement={mockEngagement} onUnlink={jest.fn()} />)
    expect(screen.getByText('Linked to Diagnostic Workspace')).toBeInTheDocument()
  })

  it('resolves and displays client name', async () => {
    render(<EngagementBanner activeEngagement={mockEngagement} onUnlink={jest.fn()} />)
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })
    expect(mockGetClient).toHaveBeenCalledWith(42)
  })

  it('shows fallback client ID when client name is not resolved', () => {
    mockGetClient.mockResolvedValue(null)
    render(<EngagementBanner activeEngagement={mockEngagement} onUnlink={jest.fn()} />)
    expect(screen.getByText('Client #42')).toBeInTheDocument()
  })

  it('displays formatted period range', () => {
    render(<EngagementBanner activeEngagement={mockEngagement} onUnlink={jest.fn()} />)
    // Dates may shift by timezone in JSDOM; just verify the period span renders
    const periodSpan = screen.getByText(/\d{4}.*to.*\d{4}/)
    expect(periodSpan).toBeInTheDocument()
  })

  it('calls onUnlink when Unlink button is clicked', async () => {
    const onUnlink = jest.fn()
    const user = userEvent.setup()
    render(<EngagementBanner activeEngagement={mockEngagement} onUnlink={onUnlink} />)

    await user.click(screen.getByText('Unlink'))
    expect(onUnlink).toHaveBeenCalledTimes(1)
  })

  it('shows Unlink button', () => {
    render(<EngagementBanner activeEngagement={mockEngagement} onUnlink={jest.fn()} />)
    expect(screen.getByText('Unlink')).toBeInTheDocument()
  })
})
