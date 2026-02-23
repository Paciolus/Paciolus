/**
 * EngagementList component tests — Sprint 277
 *
 * Tests: card rendering, empty state, loading skeleton,
 * status filter tabs, client filter dropdown, filter callbacks.
 */
import React from 'react'
import { render, screen, fireEvent } from '@/test-utils'
import type { Client } from '@/types/client'
import type { Engagement } from '@/types/engagement'

jest.mock('framer-motion', () => {
  const R = require('react')
  return {
    motion: new Proxy(
      {},
      {
        get: (_: unknown, tag: string) =>
          R.forwardRef(
            (
              {
                initial,
                animate,
                exit,
                transition,
                variants,
                whileHover,
                whileInView,
                whileTap,
                viewport,
                layout,
                layoutId,
                ...rest
              }: any,
              ref: any,
            ) => R.createElement(tag, { ...rest, ref }),
          ),
      },
    ),
    AnimatePresence: ({ children }: any) => children,
  }
})

jest.mock('@/utils/themeUtils', () => ({
  CONTAINER_VARIANTS: { fast: { hidden: {}, visible: {} } },
  createCardStaggerVariants: jest.fn(() => ({ hidden: {}, visible: {} })),
}))

jest.mock('@/utils/formatting', () => ({
  formatCurrency: jest.fn((v: number) => '$' + v.toLocaleString()),
}))

jest.mock('@/types/engagement', () => ({
  ENGAGEMENT_STATUS_COLORS: {
    active: { bg: '', text: '', border: '' },
    archived: { bg: '', text: '', border: '' },
  },
}))

jest.mock('@/components/engagement/EngagementCard', () => ({
  EngagementCard: ({ engagement, onClick }: any) => (
    <div data-testid={`card-${engagement.id}`} onClick={() => onClick(engagement)}>
      {engagement.id}
    </div>
  ),
}))

import { EngagementList } from '@/components/engagement/EngagementList'

const mockEngagements: Engagement[] = [
  {
    id: 1,
    client_id: 10,
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
  },
  {
    id: 2,
    client_id: 20,
    period_start: '2025-01-01',
    period_end: '2025-12-31',
    status: 'archived',
    materiality_basis: 'assets',
    materiality_percentage: 3,
    materiality_amount: 30000,
    performance_materiality_factor: 0.75,
    trivial_threshold_factor: 0.05,
    created_by: 1,
    created_at: '2025-02-01T00:00:00Z',
    updated_at: '2025-02-01T00:00:00Z',
  },
]

const mockClients: Client[] = [
  { id: 10, user_id: 1, name: 'Acme Corp', industry: 'manufacturing', fiscal_year_end: '12-31', created_at: '2025-01-01', updated_at: '2025-01-01' },
  { id: 20, user_id: 1, name: 'Beta Inc', industry: 'technology', fiscal_year_end: '12-31', created_at: '2025-01-01', updated_at: '2025-01-01' },
]

describe('EngagementList', () => {
  const defaultProps = {
    engagements: mockEngagements,
    clients: mockClients,
    materialityMap: {},
    toolRunCountMap: {},
    selectedId: null,
    isLoading: false,
    onSelect: jest.fn(),
    onFilterClient: jest.fn(),
    onFilterStatus: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders engagement cards when data exists', () => {
    render(<EngagementList {...defaultProps} />)
    expect(screen.getByTestId('card-1')).toBeInTheDocument()
    expect(screen.getByTestId('card-2')).toBeInTheDocument()
  })

  it('shows "No Workspaces Yet" empty state when no engagements', () => {
    render(<EngagementList {...defaultProps} engagements={[]} />)
    expect(screen.getByText('No Workspaces Yet')).toBeInTheDocument()
  })

  it('shows loading skeleton when loading with no data', () => {
    const { container } = render(
      <EngagementList {...defaultProps} engagements={[]} isLoading={true} />,
    )
    const pulseElements = container.querySelectorAll('.animate-pulse')
    expect(pulseElements.length).toBeGreaterThan(0)
  })

  it('renders status filter tabs (All, Active, Archived)', () => {
    render(<EngagementList {...defaultProps} />)
    expect(screen.getByText('All')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByText('Archived')).toBeInTheDocument()
  })

  it('renders client filter dropdown with all clients', () => {
    render(<EngagementList {...defaultProps} />)
    expect(screen.getByText('All Clients')).toBeInTheDocument()
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Beta Inc')).toBeInTheDocument()
  })

  it('calls onFilterStatus when status tab is clicked', () => {
    render(<EngagementList {...defaultProps} />)
    fireEvent.click(screen.getByText('Active'))
    expect(defaultProps.onFilterStatus).toHaveBeenCalledWith('active')
  })
})
