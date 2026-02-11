/**
 * Sprint 129: Trial Balance Diagnostics page tests (10 tests)
 *
 * Special pattern: no domain hook — uses custom fetch + inline state management.
 * Most complex page in the platform — ~18 sub-components mocked as stubs.
 */
import { render, screen } from '@/test-utils'

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/contexts/EngagementContext', () => ({
  useOptionalEngagementContext: jest.fn(() => null),
}))

jest.mock('@/hooks/useFileUpload', () => ({
  useFileUpload: jest.fn(() => ({
    isDragging: false, fileInputRef: { current: null },
    handleDrop: jest.fn(), handleDragOver: jest.fn(), handleDragLeave: jest.fn(), handleFileSelect: jest.fn(),
  })),
}))

jest.mock('@/hooks/useSettings', () => ({
  useSettings: jest.fn(() => ({ settings: null, isLoading: false })),
}))

jest.mock('@/hooks', () => ({
  useBenchmarks: jest.fn(() => ({
    availableIndustries: [], isLoadingComparison: false, comparisonResults: null,
    fetchComparison: jest.fn(), industriesFetchedRef: { current: false },
    fetchIndustries: jest.fn(), compareToBenchmarks: jest.fn(), clear: jest.fn(),
  })),
}))

jest.mock('@/contexts/MappingContext', () => ({
  MappingProvider: ({ children }: any) => <>{children}</>,
  useMappings: jest.fn(() => ({
    mappings: new Map(), setAccountType: jest.fn(), resetMappings: jest.fn(),
    getColumnMapping: jest.fn(() => null), setColumnMapping: jest.fn(),
    hasMappingOverrides: false,
  })),
}))

// Mock all sub-components
jest.mock('@/components/mapping', () => ({
  AccountTypeDropdown: () => <div data-testid="account-type-dropdown">Dropdown</div>,
  MappingIndicator: () => <div data-testid="mapping-indicator">Indicator</div>,
  MappingToolbar: () => <div data-testid="mapping-toolbar">MappingToolbar</div>,
  ColumnMappingModal: () => null,
}))
jest.mock('@/components/risk', () => ({ RiskDashboard: () => <div data-testid="risk-dashboard">RiskDashboard</div> }))
jest.mock('@/components/workbook', () => ({ WorkbookInspector: () => <div data-testid="workbook-inspector">Inspector</div> }))
jest.mock('@/components/export', () => ({ DownloadReportButton: () => <div data-testid="download-report">Download</div> }))
jest.mock('@/components/auth', () => ({ VerificationBanner: () => <div data-testid="verification-banner">Verify</div> }))
jest.mock('@/components/shared', () => ({ ToolNav: () => <nav data-testid="tool-nav">Nav</nav> }))
jest.mock('@/components/analytics', () => ({ KeyMetricsSection: () => <div data-testid="key-metrics">Metrics</div> }))
jest.mock('@/components/diagnostics/ClassificationQualitySection', () => ({
  ClassificationQualitySection: () => <div data-testid="classification-quality">Quality</div>,
}))
jest.mock('@/components/sensitivity', () => ({
  SensitivityToolbar: () => <div data-testid="sensitivity-toolbar">Sensitivity</div>,
}))
jest.mock('@/components/marketing', () => ({
  FeaturePillars: () => <div data-testid="feature-pillars">Pillars</div>,
  ProcessTimeline: () => <div data-testid="process-timeline">Timeline</div>,
  DemoZone: () => <div data-testid="demo-zone">Demo</div>,
}))
jest.mock('@/components/workspace', () => ({
  WorkspaceHeader: () => <div data-testid="workspace-header">Header</div>,
  QuickActionsBar: () => <div data-testid="quick-actions">Actions</div>,
  RecentHistoryMini: () => <div data-testid="recent-history">History</div>,
}))
jest.mock('@/components/diagnostic', () => ({
  MaterialityControl: () => <div data-testid="materiality-control">Materiality</div>,
}))
jest.mock('@/components/benchmark', () => ({
  BenchmarkSection: () => <div data-testid="benchmark-section">Benchmarks</div>,
}))
jest.mock('@/components/leadSheet', () => ({
  LeadSheetSection: () => <div data-testid="lead-sheet-section">LeadSheets</div>,
}))
jest.mock('@/components/financialStatements', () => ({
  FinancialStatementsPreview: () => <div data-testid="financial-statements">FS</div>,
}))

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div>,
    h1: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <h1 {...rest}>{children}</h1>,
    p: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <p {...rest}>{children}</p>,
    form: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <form {...rest}>{children}</form>,
    span: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <span {...rest}>{children}</span>,
    section: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <section {...rest}>{children}</section>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

import { useAuth } from '@/contexts/AuthContext'
import TrialBalancePage from '@/app/tools/trial-balance/page'

const mockUseAuth = useAuth as jest.Mock

describe('TrialBalancePage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
  })

  it('renders tool navigation', () => {
    render(<TrialBalancePage />)
    expect(screen.getByTestId('tool-nav')).toBeInTheDocument()
  })

  it('shows workspace header for authenticated user', () => {
    render(<TrialBalancePage />)
    expect(screen.getByTestId('workspace-header')).toBeInTheDocument()
  })

  it('shows diagnostic zone for authenticated verified user', () => {
    render(<TrialBalancePage />)
    expect(screen.getByText('Diagnostic Intelligence Zone')).toBeInTheDocument()
  })

  it('shows upload zone with drop target', () => {
    render(<TrialBalancePage />)
    expect(screen.getByText(/Drag and drop your trial balance/)).toBeInTheDocument()
  })

  it('shows marketing page for unauthenticated user', () => {
    mockUseAuth.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
    render(<TrialBalancePage />)
    expect(screen.getByText(/Surgical Precision/)).toBeInTheDocument()
    expect(screen.getByTestId('feature-pillars')).toBeInTheDocument()
    expect(screen.getByTestId('process-timeline')).toBeInTheDocument()
    expect(screen.getByTestId('demo-zone')).toBeInTheDocument()
  })

  it('shows verification gate for unverified user', () => {
    mockUseAuth.mockReturnValue({ user: { is_verified: false }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'tk' })
    render(<TrialBalancePage />)
    expect(screen.getByTestId('verification-banner')).toBeInTheDocument()
    expect(screen.getByText(/Verify Your Email/)).toBeInTheDocument()
  })

  it('shows quick actions bar', () => {
    render(<TrialBalancePage />)
    expect(screen.getByTestId('quick-actions')).toBeInTheDocument()
  })

  it('shows materiality control', () => {
    render(<TrialBalancePage />)
    expect(screen.getByTestId('materiality-control')).toBeInTheDocument()
  })

  it('renders zero-storage badge', () => {
    render(<TrialBalancePage />)
    expect(screen.getByText('Zero-Storage Processing')).toBeInTheDocument()
  })

  it('shows upload prompt text', () => {
    render(<TrialBalancePage />)
    expect(screen.getByText(/or click to browse/)).toBeInTheDocument()
  })
})
