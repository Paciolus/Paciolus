/**
 * Sprint 688: CompositeRiskPage happy-path render test.
 */
import CompositeRiskPage from '@/app/tools/composite-risk/page'
import { render, screen, fireEvent, waitFor } from '@/test-utils'

const mockApiPost = jest.fn()

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true, tier: 'professional' },
    isAuthenticated: true,
    isLoading: false,
    logout: jest.fn(),
    token: 'test-token',
  })),
}))

jest.mock('@/utils/apiClient', () => ({
  apiPost: (...args: unknown[]) => mockApiPost(...args),
}))

jest.mock('@/components/ui/Reveal', () => ({
  Reveal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

jest.mock('@/utils/telemetry', () => ({
  trackEvent: jest.fn(),
}))

const sampleResponse = {
  account_assessments: [
    {
      account_name: 'Revenue',
      assertion: 'existence',
      inherent_risk: 'high',
      control_risk: 'moderate',
      combined_risk: 'high',
      fraud_risk_factor: true,
      auditor_notes: '',
    },
  ],
  testing_scores: {},
  going_concern_indicators_triggered: 0,
  high_risk_accounts: 1,
  fraud_risk_accounts: 1,
  total_assessments: 1,
  risk_distribution: { low: 0, moderate: 0, elevated: 0, high: 1 },
  overall_risk_tier: 'high',
  disclaimer: 'Auditor judgment required.',
}

describe('CompositeRiskPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockApiPost.mockResolvedValue({ ok: true, status: 200, data: sampleResponse })
  })

  it('renders the title, ISA 315 banner, and default empty row', () => {
    render(<CompositeRiskPage />)
    expect(screen.getByText('Composite Risk Scoring')).toBeInTheDocument()
    expect(screen.getAllByText(/ISA 315/i).length).toBeGreaterThan(0)
    expect(screen.getByLabelText('Account name row 1')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Build Composite Profile/i })).toBeDisabled()
  })

  it('adds a row when + Add Row is clicked', () => {
    render(<CompositeRiskPage />)
    expect(screen.queryByLabelText('Account name row 2')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Add Row/i }))
    expect(screen.getByLabelText('Account name row 2')).toBeInTheDocument()
  })

  it('submits a well-formed payload and renders the results matrix', async () => {
    render(<CompositeRiskPage />)
    fireEvent.change(screen.getByLabelText('Account name row 1'), {
      target: { value: 'Revenue' },
    })

    const submitBtn = screen.getByRole('button', { name: /Build Composite Profile/i })
    await waitFor(() => expect(submitBtn).not.toBeDisabled())
    fireEvent.click(submitBtn)

    await waitFor(() => expect(mockApiPost).toHaveBeenCalled())
    const [endpoint, token, payload] = mockApiPost.mock.calls[0]
    expect(endpoint).toBe('/composite-risk/profile')
    expect(token).toBe('test-token')
    expect(payload).toMatchObject({
      account_assessments: [
        expect.objectContaining({ account_name: 'Revenue', assertion: 'existence' }),
      ],
      going_concern_indicators_triggered: 0,
    })

    await waitFor(() => expect(screen.getByText('Composite Risk Profile')).toBeInTheDocument())
    expect(screen.getByText('Account / Assertion Matrix')).toBeInTheDocument()
    expect(screen.getByText('Auditor judgment required.')).toBeInTheDocument()
  })

  it('surfaces errors returned from the API', async () => {
    mockApiPost.mockResolvedValueOnce({ ok: false, error: 'Invalid assertion' })
    render(<CompositeRiskPage />)

    fireEvent.change(screen.getByLabelText('Account name row 1'), {
      target: { value: 'Revenue' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Build Composite Profile/i }))

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent('Invalid assertion'),
    )
  })
})
