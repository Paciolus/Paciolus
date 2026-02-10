/**
 * Sprint 129: Inventory Testing page tests (10 tests)
 */
import { render, screen } from '@/test-utils'

const mockRunTests = jest.fn()
const mockReset = jest.fn()
const mockHandleExportMemo = jest.fn()
const mockHandleExportCSV = jest.fn()
const mockFileInputRef = { current: null }

jest.mock('@/context/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/hooks/useInventoryTesting', () => ({
  useInventoryTesting: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })),
}))

jest.mock('@/hooks/useFileUpload', () => ({
  useFileUpload: jest.fn(() => ({
    isDragging: false, fileInputRef: mockFileInputRef,
    handleDrop: jest.fn(), handleDragOver: jest.fn(), handleDragLeave: jest.fn(), handleFileSelect: jest.fn(),
  })),
}))

jest.mock('@/hooks/useTestingExport', () => ({
  useTestingExport: jest.fn(() => ({ exporting: null, handleExportMemo: mockHandleExportMemo, handleExportCSV: mockHandleExportCSV })),
}))

jest.mock('@/components/inventoryTesting', () => ({
  InventoryScoreCard: () => <div data-testid="inv-score-card">ScoreCard</div>,
  InventoryTestResultGrid: () => <div data-testid="inv-test-grid">Grid</div>,
  InventoryDataQualityBadge: () => <div data-testid="inv-quality-badge">Quality</div>,
  FlaggedInventoryTable: () => <div data-testid="inv-flagged-table">Flagged</div>,
}))

jest.mock('@/components/auth', () => ({ VerificationBanner: () => <div data-testid="verification-banner">Verify</div> }))
jest.mock('@/components/shared', () => ({ ToolNav: () => <nav data-testid="tool-nav">Nav</nav> }))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

import { useAuth } from '@/context/AuthContext'
import { useInventoryTesting } from '@/hooks/useInventoryTesting'
import InventoryTestingPage from '@/app/tools/inventory-testing/page'

const mockUseAuth = useAuth as jest.Mock
const mockUseInv = useInventoryTesting as jest.Mock

describe('InventoryTestingPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    mockUseInv.mockReturnValue({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })
  })

  it('renders hero header', () => {
    render(<InventoryTestingPage />)
    expect(screen.getByText('Inventory Testing')).toBeInTheDocument()
  })

  it('renders tool navigation', () => {
    render(<InventoryTestingPage />)
    expect(screen.getByTestId('tool-nav')).toBeInTheDocument()
  })

  it('shows upload zone for authenticated verified user', () => {
    render(<InventoryTestingPage />)
    expect(screen.getByText(/Upload Inventory Register/)).toBeInTheDocument()
  })

  it('shows sign-in CTA for unauthenticated user', () => {
    mockUseAuth.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
    render(<InventoryTestingPage />)
    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByText('Create Account')).toBeInTheDocument()
  })

  it('shows verification banner for unverified user', () => {
    mockUseAuth.mockReturnValue({ user: { is_verified: false }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'tk' })
    render(<InventoryTestingPage />)
    expect(screen.getByTestId('verification-banner')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockUseInv.mockReturnValue({ status: 'loading', result: null, error: null, runTests: mockRunTests, reset: mockReset })
    render(<InventoryTestingPage />)
    expect(screen.getByText(/Running 9-test inventory battery/)).toBeInTheDocument()
  })

  it('shows error state with retry button', () => {
    mockUseInv.mockReturnValue({ status: 'error', result: null, error: 'Column detection failed', runTests: mockRunTests, reset: mockReset })
    render(<InventoryTestingPage />)
    expect(screen.getByText('Analysis Failed')).toBeInTheDocument()
    expect(screen.getByText('Column detection failed')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('shows result components on success', () => {
    mockUseInv.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
    })
    render(<InventoryTestingPage />)
    expect(screen.getByTestId('inv-score-card')).toBeInTheDocument()
    expect(screen.getByTestId('inv-test-grid')).toBeInTheDocument()
    expect(screen.getByTestId('inv-flagged-table')).toBeInTheDocument()
  })

  it('shows export buttons on success', () => {
    mockUseInv.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
    })
    render(<InventoryTestingPage />)
    expect(screen.getByText('Download Testing Memo')).toBeInTheDocument()
    expect(screen.getByText('Export Flagged CSV')).toBeInTheDocument()
    expect(screen.getByText('New Test')).toBeInTheDocument()
  })

  it('shows info cards in idle state', () => {
    render(<InventoryTestingPage />)
    expect(screen.getByText('Structural Tests')).toBeInTheDocument()
    expect(screen.getByText('Statistical Tests')).toBeInTheDocument()
    expect(screen.getByText('Advanced Tests')).toBeInTheDocument()
  })
})
