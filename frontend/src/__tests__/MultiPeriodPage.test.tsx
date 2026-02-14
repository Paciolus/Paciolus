/**
 * Sprint 129: Multi-Period Comparison page tests (10 tests)
 *
 * Special pattern: no domain hook for file uploads — uses custom fetch + inline state.
 * The useMultiPeriodComparison hook handles comparison/export only.
 */
import { render, screen } from '@/test-utils'

const mockCompareResults = jest.fn()
const mockExportCsv = jest.fn()
const mockClear = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
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
}))

jest.mock('@/utils', () => {
  const actual = jest.requireActual('@/utils')
  return { ...actual, apiDownload: jest.fn().mockResolvedValue({ ok: true, blob: new Blob(), filename: 'test.pdf' }), downloadBlob: jest.fn() }
})

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div>,
    h1: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <h1 {...rest}>{children}</h1>,
    p: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <p {...rest}>{children}</p>,
    section: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <section {...rest}>{children}</section>,
    form: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <form {...rest}>{children}</form>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

import { useAuth } from '@/contexts/AuthContext'
import { useMultiPeriodComparison } from '@/hooks'
import MultiPeriodPage from '@/app/tools/multi-period/page'

const mockUseAuth = useAuth as jest.Mock
const mockUseMultiPeriod = useMultiPeriodComparison as jest.Mock

describe('MultiPeriodPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
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
    mockUseAuth.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
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
