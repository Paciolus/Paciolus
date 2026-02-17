/**
 * EngagementCard component tests — Sprint 277
 *
 * Tests: client name rendering, fallback to Client #ID, status badge,
 * period dates, materiality display, tool run count, click handler.
 */
import { render, screen, fireEvent } from '@/test-utils'
import type { Engagement, MaterialityCascade } from '@/types/engagement'

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
  createCardStaggerVariants: jest.fn(() => ({ hidden: {}, visible: {} })),
}))

jest.mock('@/utils/formatting', () => ({
  formatCurrency: jest.fn((v: number) => '$' + v.toLocaleString()),
}))

jest.mock('@/types/engagement', () => ({
  ENGAGEMENT_STATUS_COLORS: {
    active: { bg: 'bg-sage-50', text: 'text-sage-700', border: 'border-sage-200' },
    archived: { bg: 'bg-oatmeal-100', text: 'text-oatmeal-700', border: 'border-oatmeal-300' },
  },
}))

import { EngagementCard } from '@/components/engagement/EngagementCard'

const baseEngagement: Engagement = {
  id: 10,
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

const baseMateriality: MaterialityCascade = {
  overall_materiality: 50000,
  performance_materiality: 37500,
  trivial_threshold: 2500,
  materiality_basis: 'revenue',
  materiality_percentage: 5,
  performance_materiality_factor: 0.75,
  trivial_threshold_factor: 0.05,
}

describe('EngagementCard', () => {
  const defaultProps = {
    engagement: baseEngagement,
    index: 0,
    onClick: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders client name when provided', () => {
    render(<EngagementCard {...defaultProps} clientName="Acme Corp" />)
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
  })

  it('renders "Client #ID" when no client name is provided', () => {
    render(<EngagementCard {...defaultProps} />)
    expect(screen.getByText('Client #42')).toBeInTheDocument()
  })

  it('renders Active status badge for active engagement', () => {
    render(<EngagementCard {...defaultProps} />)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('renders Archived status badge for archived engagement', () => {
    const archivedEngagement = { ...baseEngagement, status: 'archived' as const }
    render(<EngagementCard {...defaultProps} engagement={archivedEngagement} />)
    expect(screen.getByText('Archived')).toBeInTheDocument()
  })

  it('renders period dates', () => {
    render(<EngagementCard {...defaultProps} />)
    // The component formats dates with toLocaleDateString; look for ndash separator
    const periodElement = screen.getByText(/2025/)
    expect(periodElement).toBeInTheDocument()
  })

  it('renders materiality values when provided', () => {
    render(<EngagementCard {...defaultProps} materiality={baseMateriality} />)
    expect(screen.getByText(/Overall:/)).toBeInTheDocument()
    expect(screen.getByText(/PM:/)).toBeInTheDocument()
    expect(screen.getByText(/Trivial:/)).toBeInTheDocument()
  })

  it('renders tool run count text', () => {
    render(<EngagementCard {...defaultProps} toolRunCount={5} />)
    expect(screen.getByText('5 tool runs')).toBeInTheDocument()
  })

  it('renders "No tools run yet" when toolRunCount is 0', () => {
    render(<EngagementCard {...defaultProps} toolRunCount={0} />)
    expect(screen.getByText('No tools run yet')).toBeInTheDocument()
  })

  it('calls onClick with engagement when clicked', () => {
    const onClick = jest.fn()
    render(<EngagementCard {...defaultProps} onClick={onClick} clientName="Test" />)
    fireEvent.click(screen.getByText('Test').closest('div[class*="bg-surface-card"]')!)
    expect(onClick).toHaveBeenCalledWith(baseEngagement)
  })
})
