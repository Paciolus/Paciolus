/**
 * Sprint 129 / Sprint 482: Trial Balance Diagnostics page tests
 *
 * Rewritten to match the current page implementation which uses
 * useTrialBalanceAudit hook, GuestCTA, MaterialityControl, and
 * a unified drop zone layout.
 */
import TrialBalancePage from '@/app/tools/trial-balance/page'
import { render, screen } from '@/test-utils'

const mockResetAudit = jest.fn()
const mockHandleFileSelect = jest.fn()

jest.mock('@/contexts/MappingContext', () => ({
  MappingProvider: ({ children }: any) => <>{children}</>,
  useMappings: jest.fn(() => ({
    mappings: new Map(), setAccountType: jest.fn(), resetMappings: jest.fn(),
    getColumnMapping: jest.fn(() => null), setColumnMapping: jest.fn(),
    hasMappingOverrides: false,
  })),
}))

jest.mock('@/hooks/useTrialBalanceAudit', () => ({
  useTrialBalanceAudit: jest.fn(() => ({
    user: { is_verified: true }, isAuthenticated: true, token: 'test-token', isVerified: true,
    preflightStatus: 'idle', preflightReport: null, preflightError: '',
    showPreflight: false,
    handlePreflightProceed: jest.fn(), handlePreflightExportPDF: jest.fn(), handlePreflightExportCSV: jest.fn(),
    handlePopulationProfileExportPDF: jest.fn(), handlePopulationProfileExportCSV: jest.fn(),
    handleExpenseCategoryExportPDF: jest.fn(), handleExpenseCategoryExportCSV: jest.fn(),
    handleAccrualCompletenessExportPDF: jest.fn(), handleAccrualCompletenessExportCSV: jest.fn(),
    auditStatus: 'idle', auditResult: null, auditError: '',
    selectedFile: null, isRecalculating: false, scanningRows: 0,
    materialityThreshold: 500, setMaterialityThreshold: jest.fn(),
    displayMode: 'strict', handleDisplayModeChange: jest.fn(),
    showColumnMappingModal: false, pendingColumnDetection: null,
    handleColumnMappingConfirm: jest.fn(), handleColumnMappingClose: jest.fn(),
    showWorkbookInspector: false, pendingWorkbookInfo: null,
    handleWorkbookInspectorConfirm: jest.fn(), handleWorkbookInspectorClose: jest.fn(),
    showPdfPreview: false, pendingPdfPreview: null,
    handlePdfPreviewConfirm: jest.fn(), handlePdfPreviewClose: jest.fn(),
    selectedIndustry: null, availableIndustries: [], comparisonResults: null, isLoadingComparison: false, handleIndustryChange: jest.fn(),
    isDragging: false, handleDrop: jest.fn(), handleDragOver: jest.fn(), handleDragLeave: jest.fn(), handleFileSelect: mockHandleFileSelect,
    resetAudit: mockResetAudit, handleRerunAudit: jest.fn(),
  })),
}))

jest.mock('@/hooks/useCanvasAccentSync', () => ({
  useCanvasAccentSync: jest.fn(),
}))

jest.mock('@/components/shared', () => ({
  GuestCTA: ({ description }: any) => <div data-testid="guest-cta">{description}</div>,
  DisclaimerBox: ({ children }: any) => <div data-testid="disclaimer-box">{children}</div>,
  Citation: ({ code }: any) => <span data-testid="citation">{code}</span>,
  CitationFooter: () => <div data-testid="citation-footer">Citations</div>,
}))
jest.mock('@/components/shared/PdfExtractionPreview', () => ({
  PdfExtractionPreview: () => null,
}))
jest.mock('@/components/diagnostic', () => ({
  MaterialityControl: () => <div data-testid="materiality-control">Materiality</div>,
  EngagementDetailsPanel: () => <div data-testid="engagement-details">Engagement</div>,
  DEFAULT_ENGAGEMENT_METADATA: {
    entityName: '', fiscalYearEnd: '', engagementPeriod: '',
    preparedBy: '', reviewedBy: '', reportStatus: 'Draft',
  },
}))
jest.mock('@/components/currencyRates/CurrencyRatePanel', () => ({
  CurrencyRatePanel: () => <div data-testid="currency-rate-panel">Rates</div>,
}))
jest.mock('@/components/preflight/PreFlightSummary', () => ({
  PreFlightSummary: () => <div data-testid="preflight-summary">Preflight</div>,
}))
jest.mock('@/components/mapping', () => ({
  ColumnMappingModal: () => null,
}))
jest.mock('@/components/workbook', () => ({
  WorkbookInspector: () => null,
}))
jest.mock('@/components/trialBalance/AuditResultsPanel', () => ({
  AuditResultsPanel: () => <div data-testid="audit-results">Results</div>,
}))
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))


// Access the mock to change return values per-test
const mockUseTrialBalanceAudit = jest.requireMock('@/hooks/useTrialBalanceAudit').useTrialBalanceAudit as jest.Mock

const defaultHookReturn = {
  user: { is_verified: true }, isAuthenticated: true, token: 'test-token', isVerified: true,
  preflightStatus: 'idle', preflightReport: null, preflightError: '',
  showPreflight: false,
  handlePreflightProceed: jest.fn(), handlePreflightExportPDF: jest.fn(), handlePreflightExportCSV: jest.fn(),
  handlePopulationProfileExportPDF: jest.fn(), handlePopulationProfileExportCSV: jest.fn(),
  handleExpenseCategoryExportPDF: jest.fn(), handleExpenseCategoryExportCSV: jest.fn(),
  handleAccrualCompletenessExportPDF: jest.fn(), handleAccrualCompletenessExportCSV: jest.fn(),
  auditStatus: 'idle', auditResult: null, auditError: '',
  selectedFile: null, isRecalculating: false, scanningRows: 0,
  materialityThreshold: 500, setMaterialityThreshold: jest.fn(),
  displayMode: 'strict', handleDisplayModeChange: jest.fn(),
  showColumnMappingModal: false, pendingColumnDetection: null,
  handleColumnMappingConfirm: jest.fn(), handleColumnMappingClose: jest.fn(),
  showWorkbookInspector: false, pendingWorkbookInfo: null,
  handleWorkbookInspectorConfirm: jest.fn(), handleWorkbookInspectorClose: jest.fn(),
  showPdfPreview: false, pendingPdfPreview: null,
  handlePdfPreviewConfirm: jest.fn(), handlePdfPreviewClose: jest.fn(),
  selectedIndustry: null, availableIndustries: [], comparisonResults: null, isLoadingComparison: false, handleIndustryChange: jest.fn(),
  isDragging: false, handleDrop: jest.fn(), handleDragOver: jest.fn(), handleDragLeave: jest.fn(), handleFileSelect: mockHandleFileSelect,
  resetAudit: mockResetAudit, handleRerunAudit: jest.fn(),
}

describe('TrialBalancePage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseTrialBalanceAudit.mockReturnValue({ ...defaultHookReturn })
  })

  it('renders hero title for authenticated user', () => {
    render(<TrialBalancePage />)
    expect(screen.getByText('Trial Balance Diagnostics')).toBeInTheDocument()
  })

  it('shows ISA 520 badge', () => {
    render(<TrialBalancePage />)
    expect(screen.getByText('ISA 520 Analytical Procedures')).toBeInTheDocument()
  })

  it('shows upload zone with drop target', () => {
    render(<TrialBalancePage />)
    expect(screen.getByText(/Drag and drop your trial balance/)).toBeInTheDocument()
  })

  it('shows guest CTA for unauthenticated user', () => {
    mockUseTrialBalanceAudit.mockReturnValue({ ...defaultHookReturn, isAuthenticated: false, user: null, isVerified: false })
    render(<TrialBalancePage />)
    expect(screen.getByTestId('guest-cta')).toBeInTheDocument()
  })

  it('shows materiality control', () => {
    render(<TrialBalancePage />)
    expect(screen.getByTestId('materiality-control')).toBeInTheDocument()
  })

  it('shows upload prompt text', () => {
    render(<TrialBalancePage />)
    expect(screen.getByText(/or click to browse/)).toBeInTheDocument()
  })

  it('shows zero-storage message', () => {
    render(<TrialBalancePage />)
    expect(screen.getByText(/never saved to any disk or server/)).toBeInTheDocument()
  })

  it('shows error state with try again', () => {
    mockUseTrialBalanceAudit.mockReturnValue({ ...defaultHookReturn, auditStatus: 'error', auditError: 'Invalid file format' })
    render(<TrialBalancePage />)
    expect(screen.getByText('Invalid file format')).toBeInTheDocument()
    expect(screen.getByText('Try again')).toBeInTheDocument()
  })

  it('shows loading state with progress', () => {
    mockUseTrialBalanceAudit.mockReturnValue({ ...defaultHookReturn, auditStatus: 'loading', scanningRows: 1500 })
    render(<TrialBalancePage />)
    expect(screen.getByText(/Streaming analysis in progress/)).toBeInTheDocument()
    expect(screen.getByText('1,500')).toBeInTheDocument()
  })
})
