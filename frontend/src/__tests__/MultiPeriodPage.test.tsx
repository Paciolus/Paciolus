/**
 * Sprint 129: Multi-Period Comparison page tests (10 tests)
 *
 * Sprint 750: page is now a composition root over usePeriodUploads +
 * useMultiPeriodComparison + useMultiPeriodMemoExport. Tests mock all
 * three hooks to keep this suite fast and focused on render/interaction.
 */
import MultiPeriodPage from '@/app/tools/multi-period/page'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useMultiPeriodComparison } from '@/hooks'
import { render, screen } from '@/test-utils'

const mockCompareResults = jest.fn()
const mockExportCsv = jest.fn()
const mockClear = jest.fn()
const mockHandlePriorFile = jest.fn()
const mockHandleCurrentFile = jest.fn()
const mockHandleBudgetFile = jest.fn()
const mockToggleBudget = jest.fn()
const mockUploadsReset = jest.fn()
const mockExportMemo = jest.fn()

const idlePeriod = { file: null, status: 'idle' as const, result: null, error: null }

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/contexts/EngagementContext', () => ({
  useOptionalEngagementContext: jest.fn(() => null),
}))

jest.mock('@/hooks', () => ({
  useMultiPeriodComparison: jest.fn(() => ({
    comparison: null, isComparing: false, isExporting: false, error: null,
    compareResults: mockCompareResults, exportCsv: mockExportCsv, clear: mockClear,
  })),
  usePeriodUploads: jest.fn(() => ({
    prior: idlePeriod,
    current: idlePeriod,
    budget: idlePeriod,
    showBudget: false,
    anyLoading: false,
    canCompare: false,
    handlePriorFile: mockHandlePriorFile,
    handleCurrentFile: mockHandleCurrentFile,
    handleBudgetFile: mockHandleBudgetFile,
    toggleBudget: mockToggleBudget,
    reset: mockUploadsReset,
  })),
  useMultiPeriodMemoExport: jest.fn(() => ({
    exporting: false,
    exportMemo: mockExportMemo,
  })),
}))

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div>,
    h1: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <h1 {...rest}>{children}</h1>,
    p: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <p {...rest}>{children}</p>,
    section: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <section {...rest}>{children}</section>,
    form: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <form {...rest}>{children}</form>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
  useInView: () => true,
  useReducedMotion: () => false,
}))


const mockUseAuthSession = useAuthSession as jest.Mock
const mockUseMultiPeriod = useMultiPeriodComparison as jest.Mock

describe('MultiPeriodPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuthSession.mockReturnValue({ user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    mockUseMultiPeriod.mockReturnValue({
      comparison: null, isComparing: false, isExporting: false, error: null,
      compareResults: mockCompareResults, exportCsv: mockExportCsv, clear: mockClear,
    })
  })

  it('renders hero header', () => {
    render(<MultiPeriodPage />)
    expect(screen.getByText('Period-Over-Period Analysis')).toBeInTheDocument()
  })

  it('shows upload zone for authenticated verified user', () => {
    render(<MultiPeriodPage />)
    expect(screen.getByText('Prior Period')).toBeInTheDocument()
    expect(screen.getByText('Current Period')).toBeInTheDocument()
  })

  it('shows sign-in CTA for unauthenticated user', () => {
    mockUseAuthSession.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
    render(<MultiPeriodPage />)
    expect(screen.getByText('Sign In')).toBeInTheDocument()
  })

  it('shows compare button in disabled state when no files', () => {
    render(<MultiPeriodPage />)
    expect(screen.getByText('Compare Periods')).toBeInTheDocument()
    expect(screen.getByText('Compare Periods').closest('button')).toBeDisabled()
  })

  it('shows comparison error', () => {
    mockUseMultiPeriod.mockReturnValue({
      comparison: null, isComparing: false, isExporting: false, error: 'Period mismatch',
      compareResults: mockCompareResults, exportCsv: mockExportCsv, clear: mockClear,
    })
    render(<MultiPeriodPage />)
    expect(screen.getByText('Period mismatch')).toBeInTheDocument()
  })

  it('shows result section with export buttons on success', () => {
    mockUseMultiPeriod.mockReturnValue({
      comparison: {
        prior_label: 'FY2024', current_label: 'FY2025', budget_label: null,
        total_accounts: 100, movements_by_type: {}, movements_by_significance: { material: 5, significant: 10 },
        significant_movements: [], all_movements: [], lead_sheet_summaries: [], dormant_accounts: [],
      },
      isComparing: false, isExporting: false, error: null,
      compareResults: mockCompareResults, exportCsv: mockExportCsv, clear: mockClear,
    })
    render(<MultiPeriodPage />)
    expect(screen.getByText(/FY2024 vs FY2025/)).toBeInTheDocument()
    expect(screen.getByText('Download Memo')).toBeInTheDocument()
    expect(screen.getByText('Export CSV')).toBeInTheDocument()
  })

  it('shows budget toggle button', () => {
    render(<MultiPeriodPage />)
    expect(screen.getByText('+ Add Budget/Forecast')).toBeInTheDocument()
  })

  it('shows materiality threshold input', () => {
    render(<MultiPeriodPage />)
    expect(screen.getByText(/Materiality/)).toBeInTheDocument()
  })
})
