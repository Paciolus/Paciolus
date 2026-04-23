/**
 * Sprint 689f: BookToTaxPage gating + happy-path render tests.
 */
import BookToTaxPage from '@/app/tools/book-to-tax/page'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useBookToTax } from '@/hooks/useBookToTax'
import { render, screen } from '@/test-utils'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(),
}))

jest.mock('@/hooks/useBookToTax', () => ({
  useBookToTax: jest.fn(),
}))

jest.mock('@/utils/telemetry', () => ({
  trackEvent: jest.fn(),
}))

const mockUseAuthSession = useAuthSession as jest.Mock
const mockUseHook = useBookToTax as jest.Mock

const defaultHookReturn = {
  status: 'idle' as const,
  result: null,
  standardAdjustments: [],
  error: '',
  analyze: jest.fn(),
  exportCsv: jest.fn(),
  loadStandardAdjustments: jest.fn(),
  reset: jest.fn(),
}

describe('BookToTaxPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseHook.mockReturnValue(defaultHookReturn)
  })

  it('renders GuestCTA for unauthenticated visitors', () => {
    mockUseAuthSession.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, token: null })
    render(<BookToTaxPage />)
    expect(screen.getByText('Book-to-Tax Reconciliation')).toBeInTheDocument()
    expect(screen.getByText(/requires a verified account/i)).toBeInTheDocument()
  })

  it('renders UnverifiedCTA for authenticated but unverified users', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: false, tier: 'solo' }, isAuthenticated: true, isLoading: false, token: 't',
    })
    render(<BookToTaxPage />)
    expect(screen.getByText(/verify your email/i)).toBeInTheDocument()
  })

  it('renders upgrade gate for FREE tier', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'free' }, isAuthenticated: true, isLoading: false, token: 't',
    })
    render(<BookToTaxPage />)
    expect(screen.getByText('Upgrade Required')).toBeInTheDocument()
    expect(screen.queryByText(/Reconciliation Inputs/i)).not.toBeInTheDocument()
    // loadStandardAdjustments NOT called for free tier
    expect(defaultHookReturn.loadStandardAdjustments).not.toHaveBeenCalled()
  })

  it('renders form + info cards + loads catalog for paid tiers', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'professional' }, isAuthenticated: true, isLoading: false, token: 't',
    })
    render(<BookToTaxPage />)
    expect(screen.getAllByText('Book-to-Tax Reconciliation').length).toBeGreaterThanOrEqual(1)
    // Catalog preload fired for paid tiers
    expect(defaultHookReturn.loadStandardAdjustments).toHaveBeenCalled()
    expect(screen.getByText('Reconciliation Inputs')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Compute M-1 \/ M-3/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download CSV/i })).toBeInTheDocument()
    expect(screen.getByText('M-1 / M-3 Auto-Select')).toBeInTheDocument()
    expect(screen.getByText('ASC 740 Rollforward')).toBeInTheDocument()
    expect(screen.getByText('Standard Adjustments Catalog')).toBeInTheDocument()
    expect(screen.getByText(/working-paper draft, not a filed return/i)).toBeInTheDocument()
  })
})
