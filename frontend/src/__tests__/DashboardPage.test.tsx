/**
 * DashboardPage smoke test (Sprint 743 — Phase 0.2 gap-fill).
 *
 * Pins the basic render contract before Sprint 751's structural decomposition.
 * Sprint 751 plans to extract: tool catalog registry, useDashboardStats /
 * useActivityFeed / usePreferences hooks. Without this test the refactor
 * could ship regressions silently.
 *
 * Scope: smoke-level only. Detailed interaction tests (favorite toggle,
 * activity-item navigation, etc.) are deferred to Sprint 751 once the
 * decomposed surfaces have stable hook boundaries to test against.
 */
import DashboardPage from '@/app/dashboard/page'
import { render, screen, waitFor } from '@/test-utils'

const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { id: 1, email: 'test@example.com', name: 'Test User', is_verified: true, tier: 'professional' },
    token: 'test-token',
    isAuthenticated: true,
    isLoading: false,
  })),
}))

const mockToastError = jest.fn()
jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({ error: mockToastError, success: jest.fn(), info: jest.fn() }),
}))

const mockApiGet = jest.fn()
const mockApiPut = jest.fn()
jest.mock('@/utils/apiClient', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPut: (...args: unknown[]) => mockApiPut(...args),
}))

jest.mock('@/components/shared/WelcomeModal', () => ({
  WelcomeModal: () => null,
}))

jest.mock('@/components/ui/Reveal', () => ({
  Reveal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const sampleStats = {
  total_clients: 5,
  assessments_today: 2,
  last_assessment_date: '2026-04-29T12:00:00Z',
  total_assessments: 17,
  tool_runs_today: 3,
  total_tool_runs: 42,
  active_workspaces: 1,
  tools_used: 6,
}

const sampleActivity = [
  {
    id: 101,
    tool_name: 'journal_entry_testing',
    tool_label: 'JE Testing',
    filename: 'JE-Q1-2026.xlsx',
    record_count: 4500,
    summary: { flagged_count: 12 },
    created_at: '2026-04-29T11:30:00Z',
  },
]

describe('DashboardPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Default: all three GETs succeed.
    mockApiGet.mockImplementation((endpoint: string) => {
      if (endpoint === '/dashboard/stats') {
        return Promise.resolve({ ok: true, status: 200, data: sampleStats })
      }
      if (endpoint.startsWith('/activity/tool-feed')) {
        return Promise.resolve({ ok: true, status: 200, data: sampleActivity })
      }
      if (endpoint === '/settings/preferences') {
        return Promise.resolve({ ok: true, status: 200, data: { favorite_tools: ['trial_balance', 'journal_entry_testing'] } })
      }
      return Promise.resolve({ ok: false, status: 404 })
    })
    mockApiPut.mockResolvedValue({ ok: true, status: 200, data: { favorite_tools: [] } })
  })

  it('issues the three dashboard data requests on mount', async () => {
    render(<DashboardPage />)

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith('/dashboard/stats', 'test-token')
    })
    expect(mockApiGet).toHaveBeenCalledWith(
      expect.stringMatching(/^\/activity\/tool-feed/),
      'test-token',
    )
    expect(mockApiGet).toHaveBeenCalledWith('/settings/preferences', 'test-token')
  })

  it('renders the welcome header and Quick Launch surface', async () => {
    render(<DashboardPage />)

    // Tool labels from the inline TOOLS catalog should appear
    await waitFor(() => {
      expect(screen.getAllByText(/JE Testing/i).length).toBeGreaterThan(0)
    })
    // Welcome header references the user's name
    expect(screen.getByText(/Test User/i)).toBeInTheDocument()
  })

  it('redirects unauthenticated users to /login', async () => {
    const { useAuthSession } = jest.requireMock('@/contexts/AuthSessionContext')
    ;(useAuthSession as jest.Mock).mockReturnValueOnce({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    })

    render(<DashboardPage />)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  it('surfaces a toast and stays on page when stats endpoint fails', async () => {
    mockApiGet.mockImplementation((endpoint: string) => {
      if (endpoint === '/dashboard/stats') {
        return Promise.reject(new Error('500'))
      }
      if (endpoint.startsWith('/activity/tool-feed')) {
        return Promise.resolve({ ok: true, status: 200, data: [] })
      }
      if (endpoint === '/settings/preferences') {
        return Promise.resolve({ ok: true, status: 200, data: { favorite_tools: [] } })
      }
      return Promise.resolve({ ok: false, status: 404 })
    })

    render(<DashboardPage />)

    await waitFor(() => {
      expect(mockToastError).toHaveBeenCalledWith('Failed to load dashboard stats')
    })
    expect(mockPush).not.toHaveBeenCalled()
  })
})
