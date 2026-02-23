/**
 * AuditResultsPanel component tests
 *
 * Tests: recalculating skeleton, balanced/unbalanced states,
 * financial summary display, conditional child component rendering,
 * industry benchmark selector, disclaimer, and reset button.
 */
import userEvent from '@testing-library/user-event'
import { AuditResultsPanel } from '@/components/trialBalance/AuditResultsPanel'
import type { AuditResult } from '@/types/diagnostic'
import { render, screen } from '@/test-utils'

// Mock MappingContext
jest.mock('@/contexts/MappingContext', () => ({
  useMappings: jest.fn(() => ({
    mappings: new Map(),
    setAccountType: jest.fn(),
    clearMapping: jest.fn(),
    clearAllMappings: jest.fn(),
    manualMappingCount: 0,
    initializeFromAudit: jest.fn(),
    exportConfig: jest.fn(),
    importConfig: jest.fn(),
    downloadConfig: jest.fn(),
    getOverridesForApi: jest.fn(() => ({})),
  })),
}))

// Mock all child components as stubs
jest.mock('@/components/risk', () => ({
  RiskDashboard: (props: any) => (
    <div data-testid="risk-dashboard">
      RiskDashboard: {props.anomalies?.length ?? 0} anomalies
    </div>
  ),
}))

jest.mock('@/components/export', () => ({
  DownloadReportButton: (props: any) => (
    <button data-testid="download-report" disabled={props.disabled}>
      Download Report
    </button>
  ),
}))

jest.mock('@/components/analytics', () => ({
  KeyMetricsSection: () => <div data-testid="key-metrics">KeyMetricsSection</div>,
}))

jest.mock('@/components/diagnostics/ClassificationQualitySection', () => ({
  ClassificationQualitySection: () => <div data-testid="classification-quality">ClassificationQuality</div>,
}))

jest.mock('@/components/sensitivity', () => ({
  SensitivityToolbar: (props: any) => (
    <div data-testid="sensitivity-toolbar">
      SensitivityToolbar threshold={props.threshold}
    </div>
  ),
}))

jest.mock('@/components/mapping', () => ({
  MappingToolbar: (props: any) => (
    <div data-testid="mapping-toolbar">MappingToolbar</div>
  ),
}))

jest.mock('@/components/benchmark', () => ({
  BenchmarkSection: (props: any) => (
    <div data-testid="benchmark-section">
      BenchmarkSection industry={props.industryDisplay}
    </div>
  ),
}))

jest.mock('@/components/leadSheet', () => ({
  LeadSheetSection: () => <div data-testid="lead-sheet">LeadSheetSection</div>,
}))

jest.mock('@/components/financialStatements', () => ({
  FinancialStatementsPreview: () => <div data-testid="financial-statements">FinancialStatementsPreview</div>,
}))


// ─── Fixtures ──────────────────────────────────────────────────────────────────

const baseResult: AuditResult = {
  status: 'completed',
  balanced: true,
  total_debits: 1500000,
  total_credits: 1500000,
  difference: 0,
  row_count: 150,
  message: 'Trial balance is balanced',
  abnormal_balances: [],
  has_risk_alerts: false,
  materiality_threshold: 10000,
  material_count: 0,
  immaterial_count: 0,
}

const resultWithAnomalies: AuditResult = {
  ...baseResult,
  abnormal_balances: [
    {
      account: 'Suspense',
      type: 'Liability',
      issue: 'Suspense account',
      amount: 5000,
      materiality: 'material',
      confidence: 0.85,
      anomaly_type: 'suspense_account',
      severity: 'medium',
    },
  ],
  material_count: 1,
  immaterial_count: 0,
  has_risk_alerts: true,
  risk_summary: {
    high_severity: 0,
    medium_severity: 1,
    low_severity: 0,
    suspense_account: 1,
    abnormal_balance: 0,
  },
}

const resultWithAnalytics: AuditResult = {
  ...resultWithAnomalies,
  analytics: {
    ratios: {},
    variances: {},
    has_previous_data: false,
    category_totals: { total_assets: 1000000, current_assets: 500000, total_liabilities: 400000, total_equity: 600000, total_revenue: 2000000 },
  } as any,
}

const resultWithLeadSheet: AuditResult = {
  ...baseResult,
  lead_sheet_grouping: { A: [], B: [], C: [] } as any,
}

const resultWithClassification: AuditResult = {
  ...baseResult,
  classification_quality: {
    issues: [],
    quality_score: 0.95,
    issue_counts: {},
    total_issues: 0,
  },
}

const unbalancedResult: AuditResult = {
  ...baseResult,
  balanced: false,
  total_debits: 1500000,
  total_credits: 1400000,
  difference: 100000,
}

const defaultProps = {
  result: baseResult,
  isRecalculating: false,
  filename: 'test-tb.csv',
  token: 'test-token',
  materialityThreshold: 10000,
  setMaterialityThreshold: jest.fn(),
  displayMode: 'all' as const,
  onDisplayModeChange: jest.fn(),
  selectedIndustry: '',
  availableIndustries: [] as string[],
  comparisonResults: null,
  isLoadingComparison: false,
  onIndustryChange: jest.fn(),
  onRerunAudit: jest.fn(),
  onReset: jest.fn(),
}

describe('AuditResultsPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    defaultProps.onRerunAudit.mockReturnValue(undefined)
    defaultProps.onReset.mockReturnValue(undefined)
    defaultProps.onIndustryChange.mockResolvedValue(undefined)
  })

  // ─── Recalculating State ────────────────────────────────────────────

  it('shows recalculating skeleton when isRecalculating is true', () => {
    render(<AuditResultsPanel {...defaultProps} isRecalculating={true} />)
    expect(screen.getByText('Recalculating with new threshold...')).toBeInTheDocument()
  })

  it('hides main content when recalculating', () => {
    render(<AuditResultsPanel {...defaultProps} isRecalculating={true} />)
    // The content div uses 'hidden' class to hide via CSS
    const balancedText = screen.getByText('Balanced')
    expect(balancedText.closest('div.hidden')).toBeTruthy()
  })

  // ─── Balanced / Unbalanced States ───────────────────────────────────

  it('shows "Balanced" with check icon when result is balanced', () => {
    render(<AuditResultsPanel {...defaultProps} />)
    expect(screen.getByText('Balanced')).toBeInTheDocument()
    expect(screen.queryByText('Out of Balance')).not.toBeInTheDocument()
  })

  it('shows "Out of Balance" with warning when result is unbalanced', () => {
    render(<AuditResultsPanel {...defaultProps} result={unbalancedResult} />)
    expect(screen.getByText('Out of Balance')).toBeInTheDocument()
    expect(screen.queryByText('Balanced')).not.toBeInTheDocument()
  })

  // ─── Financial Summary ──────────────────────────────────────────────

  it('displays total debits, credits, difference, and row count', () => {
    render(<AuditResultsPanel {...defaultProps} />)
    expect(screen.getByText('Total Debits:')).toBeInTheDocument()
    expect(screen.getByText('Total Credits:')).toBeInTheDocument()
    // Both debits and credits are $1,500,000 so there are 2 matches
    expect(screen.getAllByText('$1,500,000')).toHaveLength(2)
    expect(screen.getByText('Difference:')).toBeInTheDocument()
    expect(screen.getByText('Rows Analyzed:')).toBeInTheDocument()
    expect(screen.getByText('150')).toBeInTheDocument()
  })

  it('shows difference in sage color when zero', () => {
    render(<AuditResultsPanel {...defaultProps} />)
    const differenceValue = screen.getByText('$0')
    expect(differenceValue.className).toContain('text-sage')
  })

  it('shows difference in clay color when non-zero', () => {
    render(<AuditResultsPanel {...defaultProps} result={unbalancedResult} />)
    const differenceValue = screen.getByText('$100,000')
    expect(differenceValue.className).toContain('text-clay')
  })

  // ─── Conditional Child Components ───────────────────────────────────

  it('shows SensitivityToolbar always', () => {
    render(<AuditResultsPanel {...defaultProps} />)
    expect(screen.getByTestId('sensitivity-toolbar')).toBeInTheDocument()
  })

  it('shows RiskDashboard when anomalies exist', () => {
    render(<AuditResultsPanel {...defaultProps} result={resultWithAnomalies} />)
    expect(screen.getByTestId('risk-dashboard')).toBeInTheDocument()
    expect(screen.getByText(/1 anomalies/)).toBeInTheDocument()
  })

  it('does not show RiskDashboard when no anomalies', () => {
    render(<AuditResultsPanel {...defaultProps} />)
    expect(screen.queryByTestId('risk-dashboard')).not.toBeInTheDocument()
  })

  it('shows MappingToolbar when anomalies exist', () => {
    render(<AuditResultsPanel {...defaultProps} result={resultWithAnomalies} />)
    expect(screen.getByTestId('mapping-toolbar')).toBeInTheDocument()
  })

  it('does not show MappingToolbar when no anomalies', () => {
    render(<AuditResultsPanel {...defaultProps} />)
    expect(screen.queryByTestId('mapping-toolbar')).not.toBeInTheDocument()
  })

  it('shows ClassificationQualitySection when data present', () => {
    render(<AuditResultsPanel {...defaultProps} result={resultWithClassification} />)
    expect(screen.getByTestId('classification-quality')).toBeInTheDocument()
  })

  it('does not show ClassificationQualitySection when no data', () => {
    render(<AuditResultsPanel {...defaultProps} />)
    expect(screen.queryByTestId('classification-quality')).not.toBeInTheDocument()
  })

  it('shows KeyMetricsSection when analytics present', () => {
    render(<AuditResultsPanel {...defaultProps} result={resultWithAnalytics} />)
    expect(screen.getByTestId('key-metrics')).toBeInTheDocument()
  })

  it('does not show KeyMetricsSection when no analytics', () => {
    render(<AuditResultsPanel {...defaultProps} />)
    expect(screen.queryByTestId('key-metrics')).not.toBeInTheDocument()
  })

  it('shows LeadSheetSection when lead_sheet_grouping present', () => {
    render(<AuditResultsPanel {...defaultProps} result={resultWithLeadSheet} />)
    expect(screen.getByTestId('lead-sheet')).toBeInTheDocument()
  })

  it('shows FinancialStatementsPreview when lead_sheet_grouping present', () => {
    render(<AuditResultsPanel {...defaultProps} result={resultWithLeadSheet} />)
    expect(screen.getByTestId('financial-statements')).toBeInTheDocument()
  })

  // ─── Industry Benchmark ─────────────────────────────────────────────

  it('shows industry selector when industries are available and analytics present', () => {
    render(
      <AuditResultsPanel
        {...defaultProps}
        result={resultWithAnalytics}
        availableIndustries={['technology', 'manufacturing']}
      />
    )
    expect(screen.getByText('Industry Benchmark Comparison')).toBeInTheDocument()
    expect(screen.getByText('Technology')).toBeInTheDocument()
    expect(screen.getByText('Manufacturing')).toBeInTheDocument()
  })

  it('does not show industry selector when no industries available', () => {
    render(<AuditResultsPanel {...defaultProps} result={resultWithAnalytics} />)
    expect(screen.queryByText('Industry Benchmark Comparison')).not.toBeInTheDocument()
  })

  it('calls onIndustryChange when industry is selected', async () => {
    const user = userEvent.setup()
    render(
      <AuditResultsPanel
        {...defaultProps}
        result={resultWithAnalytics}
        availableIndustries={['technology', 'manufacturing']}
      />
    )

    const select = screen.getByRole('combobox')
    await user.selectOptions(select, 'technology')

    expect(defaultProps.onIndustryChange).toHaveBeenCalledWith('technology')
  })

  it('shows BenchmarkSection when industry is selected', () => {
    render(
      <AuditResultsPanel
        {...defaultProps}
        result={resultWithAnalytics}
        availableIndustries={['technology']}
        selectedIndustry="technology"
      />
    )
    expect(screen.getByTestId('benchmark-section')).toBeInTheDocument()
  })

  // ─── Disclaimer & Actions ──────────────────────────────────────────

  it('shows disclaimer text', () => {
    render(<AuditResultsPanel {...defaultProps} />)
    expect(screen.getByText(/This automated trial balance diagnostic tool/)).toBeInTheDocument()
  })

  it('shows download report button', () => {
    render(<AuditResultsPanel {...defaultProps} />)
    expect(screen.getByTestId('download-report')).toBeInTheDocument()
  })

  it('calls onReset when "Upload another file" is clicked', async () => {
    const user = userEvent.setup()
    render(<AuditResultsPanel {...defaultProps} />)

    await user.click(screen.getByText('Upload another file'))
    expect(defaultProps.onReset).toHaveBeenCalledTimes(1)
  })

  it('disables actions when recalculating', () => {
    render(<AuditResultsPanel {...defaultProps} isRecalculating={true} />)
    expect(screen.getByText('Upload another file').closest('button')).toBeDisabled()
    expect(screen.getByTestId('download-report')).toBeDisabled()
  })
})
