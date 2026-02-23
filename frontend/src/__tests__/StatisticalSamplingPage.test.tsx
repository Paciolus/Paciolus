/**
 * Sprint 271: Statistical Sampling page tests
 */
import { render, screen, fireEvent } from '@/test-utils'

const mockRunDesign = jest.fn()
const mockRunEvaluation = jest.fn()
const mockResetDesign = jest.fn()
const mockResetEvaluation = jest.fn()
const mockHandleExportMemo = jest.fn()
const mockHandleExportCSV = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/contexts/EngagementContext', () => ({
  useOptionalEngagementContext: jest.fn(() => null),
}))

jest.mock('@/hooks/useStatisticalSampling', () => ({
  useStatisticalSampling: jest.fn(() => ({
    designStatus: 'idle', designResult: null, designError: '',
    runDesign: mockRunDesign, resetDesign: mockResetDesign,
    evalStatus: 'idle', evalResult: null, evalError: '',
    runEvaluation: mockRunEvaluation, resetEvaluation: mockResetEvaluation,
  })),
}))

jest.mock('@/hooks/useTestingExport', () => ({
  useTestingExport: jest.fn(() => ({
    exporting: null, handleExportMemo: mockHandleExportMemo, handleExportCSV: mockHandleExportCSV,
  })),
}))

jest.mock('@/components/statisticalSampling', () => ({
  SamplingDesignPanel: ({ status }: { status: string }) => (
    <div data-testid="design-panel">DesignPanel-{status}</div>
  ),
  SampleSelectionTable: () => <div data-testid="selection-table">SelectionTable</div>,
  SamplingEvaluationPanel: () => <div data-testid="eval-panel">EvalPanel</div>,
  SamplingResultCard: () => <div data-testid="result-card">ResultCard</div>,
}))

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => (
      <div {...rest}>{children}</div>
    ),
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

import { useStatisticalSampling } from '@/hooks/useStatisticalSampling'
import StatisticalSamplingPage from '@/app/tools/statistical-sampling/page'
import { useAuth } from '@/contexts/AuthContext'

const mockUseAuth = useAuth as jest.Mock
const mockUseSampling = useStatisticalSampling as jest.Mock

describe('StatisticalSamplingPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({
      user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
    })
    mockUseSampling.mockReturnValue({
      designStatus: 'idle', designResult: null, designError: '',
      runDesign: mockRunDesign, resetDesign: mockResetDesign,
      evalStatus: 'idle', evalResult: null, evalError: '',
      runEvaluation: mockRunEvaluation, resetEvaluation: mockResetEvaluation,
    })
  })

  it('renders hero header with ISA 530 reference', () => {
    render(<StatisticalSamplingPage />)
    expect(screen.getByText('Statistical Sampling')).toBeInTheDocument()
    expect(screen.getByText('ISA 530 / PCAOB AS 2315')).toBeInTheDocument()
  })

  it('renders two tabs: Design Sample and Evaluate Results', () => {
    render(<StatisticalSamplingPage />)
    expect(screen.getByText('1. Design Sample')).toBeInTheDocument()
    expect(screen.getByText('2. Evaluate Results')).toBeInTheDocument()
  })

  it('shows design panel in idle state', () => {
    render(<StatisticalSamplingPage />)
    expect(screen.getByTestId('design-panel')).toBeInTheDocument()
    expect(screen.getByText('DesignPanel-idle')).toBeInTheDocument()
  })

  it('shows guest CTA for unauthenticated user', () => {
    mockUseAuth.mockReturnValue({
      user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null,
    })
    render(<StatisticalSamplingPage />)
    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByText('Create Account')).toBeInTheDocument()
    // Should NOT show tabs when unauthenticated
    expect(screen.queryByText('1. Design Sample')).not.toBeInTheDocument()
  })

  it('shows info cards in idle design state', () => {
    render(<StatisticalSamplingPage />)
    expect(screen.getByText('Monetary Unit Sampling')).toBeInTheDocument()
    expect(screen.getByText('Simple Random Sampling')).toBeInTheDocument()
    expect(screen.getByText('Stringer Bound Evaluation')).toBeInTheDocument()
  })

  it('shows design results with action buttons on success', () => {
    mockUseSampling.mockReturnValue({
      designStatus: 'success',
      designResult: {
        method: 'mus',
        actual_sample_size: 50,
        population_size: 1000,
        selected_items: [],
        strata_summary: [],
      },
      designError: '',
      runDesign: mockRunDesign,
      resetDesign: mockResetDesign,
      evalStatus: 'idle', evalResult: null, evalError: '',
      runEvaluation: mockRunEvaluation, resetEvaluation: mockResetEvaluation,
    })
    render(<StatisticalSamplingPage />)
    expect(screen.getByTestId('selection-table')).toBeInTheDocument()
    expect(screen.getByText('Proceed to Evaluation')).toBeInTheDocument()
    expect(screen.getByText('New Design')).toBeInTheDocument()
  })

  it('switches to evaluate tab when clicking tab button', () => {
    render(<StatisticalSamplingPage />)
    fireEvent.click(screen.getByText('2. Evaluate Results'))
    expect(screen.getByTestId('eval-panel')).toBeInTheDocument()
    expect(screen.queryByTestId('design-panel')).not.toBeInTheDocument()
  })

  it('shows evaluation results on eval success', () => {
    mockUseSampling.mockReturnValue({
      designStatus: 'idle', designResult: null, designError: '',
      runDesign: mockRunDesign, resetDesign: mockResetDesign,
      evalStatus: 'success',
      evalResult: {
        method: 'mus',
        conclusion: 'pass',
        conclusion_detail: 'UEL within tolerance',
        errors_found: 0,
        errors: [],
      },
      evalError: '',
      runEvaluation: mockRunEvaluation, resetEvaluation: mockResetEvaluation,
    })
    render(<StatisticalSamplingPage />)
    fireEvent.click(screen.getByText('2. Evaluate Results'))
    expect(screen.getByTestId('result-card')).toBeInTheDocument()
    expect(screen.getByText('New Evaluation')).toBeInTheDocument()
  })

  it('shows disclaimer for authenticated users', () => {
    render(<StatisticalSamplingPage />)
    expect(screen.getByText(/ISA 530 \(Audit Sampling\)/)).toBeInTheDocument()
  })

  it('shows success dot on design tab when design completes', () => {
    mockUseSampling.mockReturnValue({
      designStatus: 'success',
      designResult: {
        method: 'mus',
        actual_sample_size: 10,
        population_size: 100,
        selected_items: [],
        strata_summary: [],
      },
      designError: '',
      runDesign: mockRunDesign, resetDesign: mockResetDesign,
      evalStatus: 'idle', evalResult: null, evalError: '',
      runEvaluation: mockRunEvaluation, resetEvaluation: mockResetEvaluation,
    })
    render(<StatisticalSamplingPage />)
    // The design tab button should have the green dot indicator
    const designTab = screen.getByText('1. Design Sample')
    const dot = designTab.parentElement?.querySelector('.bg-sage-500')
    expect(dot).toBeInTheDocument()
  })

  it('calls resetDesign when New Design is clicked', () => {
    mockUseSampling.mockReturnValue({
      designStatus: 'success',
      designResult: {
        method: 'mus',
        actual_sample_size: 10,
        population_size: 100,
        selected_items: [],
        strata_summary: [],
      },
      designError: '',
      runDesign: mockRunDesign, resetDesign: mockResetDesign,
      evalStatus: 'idle', evalResult: null, evalError: '',
      runEvaluation: mockRunEvaluation, resetEvaluation: mockResetEvaluation,
    })
    render(<StatisticalSamplingPage />)
    fireEvent.click(screen.getByText('New Design'))
    expect(mockResetDesign).toHaveBeenCalled()
  })
})
