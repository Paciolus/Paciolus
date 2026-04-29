/**
 * Sprint 688: AccountRiskHeatmapPage happy-path render test.
 */
import AccountRiskHeatmapPage from '@/app/tools/account-risk-heatmap/page'
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

jest.mock('@/utils/apiClient', () => {
  const actual = jest.requireActual('@/utils/apiClient')
  return {
    ...actual,
    apiPost: (...args: unknown[]) => mockApiPost(...args),
  }
})

jest.mock('@/components/ui/Reveal', () => ({
  Reveal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

jest.mock('@/utils/telemetry', () => ({
  trackEvent: jest.fn(),
}))

const sampleResponse = {
  rows: [
    {
      account_number: '4000',
      account_name: 'Revenue',
      signal_count: 1,
      weighted_score: 5.321,
      sources: ['audit_engine'],
      severities: { high: 1 },
      issues: ['Rounding anomaly'],
      total_materiality: '10000',
      priority_tier: 'high',
      rank: 1,
    },
  ],
  total_accounts_with_signals: 1,
  high_priority_count: 1,
  moderate_priority_count: 0,
  low_priority_count: 0,
  total_signals: 1,
  sources_active: ['audit_engine'],
}

describe('AccountRiskHeatmapPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockApiPost.mockResolvedValue({ ok: true, status: 200, data: sampleResponse })
  })

  it('renders title, upstream JSON textarea, and default signal row', () => {
    render(<AccountRiskHeatmapPage />)
    expect(screen.getByText('Account Risk Heatmap')).toBeInTheDocument()
    expect(screen.getByText('Upstream Engine JSON (optional)')).toBeInTheDocument()
    expect(screen.getByLabelText('Account name signal 1')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Generate Heatmap/i })).toBeDisabled()
  })

  it('enables submit once a signal is filled in, posts the payload, and renders results', async () => {
    render(<AccountRiskHeatmapPage />)

    fireEvent.change(screen.getByLabelText('Account name signal 1'), {
      target: { value: 'Revenue' },
    })
    fireEvent.change(screen.getByLabelText('Source signal 1'), {
      target: { value: 'audit_engine' },
    })
    fireEvent.change(screen.getByLabelText('Issue signal 1'), {
      target: { value: 'Rounding anomaly' },
    })

    const submit = screen.getByRole('button', { name: /Generate Heatmap/i })
    await waitFor(() => expect(submit).not.toBeDisabled())
    fireEvent.click(submit)

    await waitFor(() => expect(mockApiPost).toHaveBeenCalled())
    const [endpoint, token, payload] = mockApiPost.mock.calls[0]
    expect(endpoint).toBe('/audit/account-risk-heatmap')
    expect(token).toBe('test-token')
    expect(payload).toMatchObject({
      signals: [
        expect.objectContaining({
          account_name: 'Revenue',
          source: 'audit_engine',
          issue: 'Rounding anomaly',
        }),
      ],
    })

    await waitFor(() => expect(screen.getByText('Heatmap Summary')).toBeInTheDocument())
    expect(screen.getByText('Ranked Accounts')).toBeInTheDocument()
    expect(screen.getByText('Revenue')).toBeInTheDocument()
  })

  it('rejects invalid upstream JSON and does not call apiPost', async () => {
    render(<AccountRiskHeatmapPage />)

    fireEvent.change(screen.getByLabelText('Account name signal 1'), {
      target: { value: 'Revenue' },
    })
    fireEvent.change(screen.getByLabelText('Source signal 1'), {
      target: { value: 'audit_engine' },
    })
    fireEvent.change(screen.getByLabelText('Issue signal 1'), {
      target: { value: 'Rounding anomaly' },
    })

    const textarea = screen.getByPlaceholderText(/audit_anomalies/i)
    fireEvent.change(textarea, { target: { value: '{not valid json' } })

    fireEvent.click(screen.getByRole('button', { name: /Generate Heatmap/i }))

    await waitFor(() => expect(screen.getAllByRole('alert').length).toBeGreaterThan(0))
    expect(mockApiPost).not.toHaveBeenCalled()
  })
})
