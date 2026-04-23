/**
 * Sprint 689a: MultiCurrencyPage gating + happy-path render test.
 */
import MultiCurrencyPage from '@/app/tools/multi-currency/page'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useCurrencyRates } from '@/hooks/useCurrencyRates'
import { render, screen } from '@/test-utils'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(),
}))

jest.mock('@/hooks/useCurrencyRates', () => ({
  useCurrencyRates: jest.fn(),
}))

jest.mock('@/utils/telemetry', () => ({
  trackEvent: jest.fn(),
}))

const mockUseAuthSession = useAuthSession as jest.Mock
const mockUseCurrencyRates = useCurrencyRates as jest.Mock

const defaultHookReturn = {
  rateStatus: null,
  uploadStatus: 'idle' as const,
  error: '',
  uploadRateTable: jest.fn(),
  addSingleRate: jest.fn(),
  clearRates: jest.fn(),
  refreshStatus: jest.fn(),
}

describe('MultiCurrencyPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseCurrencyRates.mockReturnValue(defaultHookReturn)
  })

  it('renders GuestCTA for unauthenticated visitors', () => {
    mockUseAuthSession.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      token: null,
    })

    render(<MultiCurrencyPage />)

    expect(screen.getByText('Multi-Currency Conversion')).toBeInTheDocument()
    expect(screen.getByText(/requires a verified account/i)).toBeInTheDocument()
  })

  it('renders UnverifiedCTA for authenticated but unverified users', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: false, tier: 'solo' },
      isAuthenticated: true,
      isLoading: false,
      token: 'test-token',
    })

    render(<MultiCurrencyPage />)

    expect(screen.getByText(/verify your email/i)).toBeInTheDocument()
  })

  it('renders upgrade gate for FREE tier', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'free' },
      isAuthenticated: true,
      isLoading: false,
      token: 'test-token',
    })

    render(<MultiCurrencyPage />)

    expect(screen.getByText('Upgrade Required')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /view plans/i })).toHaveAttribute('href', '/pricing')
  })

  it('renders the currency rate panel and info cards for paid tiers', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'professional' },
      isAuthenticated: true,
      isLoading: false,
      token: 'test-token',
    })

    render(<MultiCurrencyPage />)

    // Hero + the panel header (both render "Multi-Currency Conversion")
    expect(screen.getAllByText('Multi-Currency Conversion').length).toBeGreaterThanOrEqual(1)

    // defaultOpen → refreshStatus fires on mount
    expect(defaultHookReturn.refreshStatus).toHaveBeenCalled()

    // defaultOpen → panel body visible: drop zone + tab controls
    expect(screen.getByText(/Drop a CSV, TSV, TXT, or Excel file/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Upload CSV/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Manual Entry/i })).toBeInTheDocument()

    // Info cards
    expect(screen.getByText('ISO 4217 Validation')).toBeInTheDocument()
    expect(screen.getByText('Staleness Detection')).toBeInTheDocument()
    expect(screen.getByText('Session-Scoped Rates')).toBeInTheDocument()

    // Disclaimer + citation footer
    expect(screen.getByText(/closing-rate translation/i)).toBeInTheDocument()
  })
})
