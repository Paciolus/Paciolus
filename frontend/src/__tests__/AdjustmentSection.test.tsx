/**
 * AdjustmentSection component tests
 *
 * Tests: collapsed state, expand/collapse, new entry button,
 * statistics display, error display, zero-storage notice.
 */
import { AdjustmentSection } from '@/components/adjustments/AdjustmentSection'
import { render, screen, fireEvent } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
    span: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <span {...rest}>{children}</span>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

const mockUseAdjustments = jest.fn()
jest.mock('@/hooks/useAdjustments', () => ({
  useAdjustments: () => mockUseAdjustments(),
}))

jest.mock('@/components/adjustments/AdjustmentEntryForm', () => ({
  AdjustmentEntryForm: () => <div data-testid="entry-form">EntryForm</div>,
}))

jest.mock('@/components/adjustments/AdjustmentList', () => ({
  AdjustmentList: () => <div data-testid="entry-list">EntryList</div>,
}))

const defaultHook = {
  entries: [],
  adjustedTB: null,
  isLoading: false,
  isSaving: false,
  error: null,
  stats: { total: 0, proposed: 0, approved: 0, rejected: 0, posted: 0, totalAmount: 0 },
  fetchEntries: jest.fn(),
  createEntry: jest.fn(),
  updateStatus: jest.fn(),
  deleteEntry: jest.fn(),
  clearAll: jest.fn(),
  getNextReference: jest.fn().mockResolvedValue('AJE-001'),
  applyAdjustments: jest.fn(),
  clearError: jest.fn(),
  clearAdjustedTB: jest.fn(),
}

describe('AdjustmentSection', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAdjustments.mockReturnValue({ ...defaultHook })
  })

  it('renders section header with title', () => {
    render(<AdjustmentSection />)
    expect(screen.getByText('Adjusting Entries')).toBeInTheDocument()
  })

  it('shows "Propose journal adjustments" when no entries', () => {
    render(<AdjustmentSection />)
    expect(screen.getByText('Propose journal adjustments')).toBeInTheDocument()
  })

  it('shows entry count when entries exist', () => {
    mockUseAdjustments.mockReturnValue({
      ...defaultHook,
      stats: { total: 3, proposed: 1, approved: 2, rejected: 0, posted: 0, totalAmount: 10000 },
    })
    render(<AdjustmentSection />)
    expect(screen.getByText(/3 entries/)).toBeInTheDocument()
  })

  it('expands section on click and shows New Entry button', () => {
    render(<AdjustmentSection />)
    // Click to expand
    fireEvent.click(screen.getByText('Adjusting Entries'))
    expect(screen.getByText('+ New Entry')).toBeInTheDocument()
  })

  it('shows entry list when expanded', () => {
    render(<AdjustmentSection />)
    fireEvent.click(screen.getByText('Adjusting Entries'))
    expect(screen.getByTestId('entry-list')).toBeInTheDocument()
  })

  it('shows zero-storage notice when expanded', () => {
    render(<AdjustmentSection />)
    fireEvent.click(screen.getByText('Adjusting Entries'))
    expect(screen.getByText(/stored in your session only/)).toBeInTheDocument()
  })

  it('shows error message when error exists', () => {
    mockUseAdjustments.mockReturnValue({
      ...defaultHook,
      error: 'Something went wrong',
    })
    render(<AdjustmentSection />)
    fireEvent.click(screen.getByText('Adjusting Entries'))
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('applies disabled styling when disabled prop is true', () => {
    const { container } = render(<AdjustmentSection disabled={true} />)
    const section = container.querySelector('section')
    expect(section?.className).toContain('opacity-50')
  })
})
