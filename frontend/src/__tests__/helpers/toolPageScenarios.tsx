/**
 * Sprint 548: Shared tool page test harness.
 *
 * Extracts the repeated auth/loading/error/success/export test pattern
 * from all testing tool pages into a reusable runner.
 */
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { render, screen } from '@/test-utils'

// Re-export for convenience
export { render, screen }

export interface ToolPageTestConfig {
  /** Display name for the describe block */
  name: string
  /** The page component to render */
  Component: React.ComponentType
  /** The mock for the tool's primary hook (e.g. useAPTesting) */
  getToolHookMock: () => jest.Mock
  /** Text expected in the hero header */
  heroText: string
  /** Regex matching the upload zone prompt */
  uploadPromptPattern: RegExp
  /** Regex matching the loading state text */
  loadingTextPattern: RegExp
  /** test-ids expected in success state (score card, test grid, flagged table) */
  successTestIds: string[]
  /** Labels shown in idle-state info cards */
  infoCardLabels: string[]
  /** Mock success result payload */
  mockSuccessResult: Record<string, unknown>
  /** Whether this tool has tier gating (free users see upgrade CTA) */
  hasTierGating?: boolean
}

/**
 * Run the standard 8+ test scenarios shared across all testing tool pages.
 *
 * Each test file should call this in a describe block, then add any
 * page-specific tests outside the harness.
 */
export function runStandardToolPageScenarios(config: ToolPageTestConfig) {
  const mockUseAuthSession = useAuthSession as jest.Mock

  describe(`${config.name} — standard scenarios`, () => {
    beforeEach(() => {
      jest.clearAllMocks()
      mockUseAuthSession.mockReturnValue({
        user: { is_verified: true, tier: 'enterprise' },
        isAuthenticated: true,
        isLoading: false,
        logout: jest.fn(),
        token: 'test-token',
      })
      config.getToolHookMock().mockReturnValue({
        status: 'idle',
        result: null,
        error: null,
        runTests: jest.fn(),
        reset: jest.fn(),
      })
    })

    it('renders hero header', () => {
      render(<config.Component />)
      expect(screen.getByText(config.heroText)).toBeInTheDocument()
    })

    it('shows upload zone for authenticated verified user', () => {
      render(<config.Component />)
      expect(screen.getByText(config.uploadPromptPattern)).toBeInTheDocument()
    })

    it('shows sign-in CTA for unauthenticated user', () => {
      mockUseAuthSession.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        logout: jest.fn(),
        token: null,
      })
      render(<config.Component />)
      expect(screen.getByText('Sign In')).toBeInTheDocument()
      expect(screen.getByText('Create Account')).toBeInTheDocument()
    })

    it('shows loading state', () => {
      config.getToolHookMock().mockReturnValue({
        status: 'loading',
        result: null,
        error: null,
        runTests: jest.fn(),
        reset: jest.fn(),
      })
      render(<config.Component />)
      expect(screen.getByText(config.loadingTextPattern)).toBeInTheDocument()
    })

    it('shows error state with retry button', () => {
      config.getToolHookMock().mockReturnValue({
        status: 'error',
        result: null,
        error: 'Column detection failed',
        runTests: jest.fn(),
        reset: jest.fn(),
      })
      render(<config.Component />)
      expect(screen.getByText('Analysis Failed')).toBeInTheDocument()
      expect(screen.getByText('Column detection failed')).toBeInTheDocument()
      expect(screen.getByText('Try Again')).toBeInTheDocument()
    })

    it('shows result components on success', () => {
      config.getToolHookMock().mockReturnValue({
        status: 'success',
        error: null,
        runTests: jest.fn(),
        reset: jest.fn(),
        result: config.mockSuccessResult,
      })
      render(<config.Component />)
      for (const testId of config.successTestIds) {
        expect(screen.getByTestId(testId)).toBeInTheDocument()
      }
    })

    it('shows export buttons on success', () => {
      config.getToolHookMock().mockReturnValue({
        status: 'success',
        error: null,
        runTests: jest.fn(),
        reset: jest.fn(),
        result: config.mockSuccessResult,
      })
      render(<config.Component />)
      expect(screen.getByText('Download Testing Memo')).toBeInTheDocument()
      expect(screen.getByText('Export Flagged CSV')).toBeInTheDocument()
      expect(screen.getByText('New Test')).toBeInTheDocument()
    })

    it('shows info cards in idle state', () => {
      render(<config.Component />)
      for (const label of config.infoCardLabels) {
        expect(screen.getByText(label)).toBeInTheDocument()
      }
    })

    if (config.hasTierGating) {
      it('shows upgrade gate for free tier user', () => {
        mockUseAuthSession.mockReturnValue({
          user: { is_verified: true, tier: 'free' },
          isAuthenticated: true,
          isLoading: false,
          logout: jest.fn(),
          token: 'test-token',
        })
        render(<config.Component />)
        expect(screen.getByText('Upgrade Required')).toBeInTheDocument()
        expect(screen.getByText('View Plans')).toBeInTheDocument()
        expect(screen.queryByText(config.uploadPromptPattern)).not.toBeInTheDocument()
      })

      it('shows tool content for paid tier user', () => {
        render(<config.Component />)
        expect(screen.queryByText('Upgrade Required')).not.toBeInTheDocument()
        expect(screen.getByText(config.uploadPromptPattern)).toBeInTheDocument()
      })
    }
  })
}
