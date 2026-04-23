/**
 * Sprint 689e: Form1099Page gating + happy-path render tests.
 */
import Form1099Page from '@/app/tools/form-1099/page'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useForm1099 } from '@/hooks/useForm1099'
import { render, screen } from '@/test-utils'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(),
}))

jest.mock('@/hooks/useForm1099', () => ({
  useForm1099: jest.fn(),
}))

jest.mock('@/utils/telemetry', () => ({
  trackEvent: jest.fn(),
}))

const mockUseAuthSession = useAuthSession as jest.Mock
const mockUseHook = useForm1099 as jest.Mock

const defaultHookReturn = {
  status: 'idle' as const,
  result: null,
  error: '',
  analyze: jest.fn(),
  exportCsv: jest.fn(),
  reset: jest.fn(),
}

describe('Form1099Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseHook.mockReturnValue(defaultHookReturn)
  })

  it('renders GuestCTA for unauthenticated visitors', () => {
    mockUseAuthSession.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, token: null })
    render(<Form1099Page />)
    expect(screen.getByText('Form 1099 Preparation')).toBeInTheDocument()
    expect(screen.getByText(/requires a verified account/i)).toBeInTheDocument()
  })

  it('renders UnverifiedCTA for authenticated but unverified users', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: false, tier: 'solo' }, isAuthenticated: true, isLoading: false, token: 't',
    })
    render(<Form1099Page />)
    expect(screen.getByText(/verify your email/i)).toBeInTheDocument()
  })

  it('renders upgrade gate for FREE tier', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'free' }, isAuthenticated: true, isLoading: false, token: 't',
    })
    render(<Form1099Page />)
    expect(screen.getByText('Upgrade Required')).toBeInTheDocument()
    expect(screen.queryByText(/Upload Vendors and Payments/i)).not.toBeInTheDocument()
  })

  it('renders upload surface + info cards + disclaimer for paid tiers', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'professional' }, isAuthenticated: true, isLoading: false, token: 't',
    })
    render(<Form1099Page />)
    expect(screen.getAllByText('Form 1099 Preparation').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Upload Vendors and Payments')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Prepare 1099 Candidates/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download CSV/i })).toBeInTheDocument()
    expect(screen.getByText('IRS Thresholds Built-In')).toBeInTheDocument()
    expect(screen.getByText('Processor Safe-Harbor')).toBeInTheDocument()
    expect(screen.getByText('Zero-Storage')).toBeInTheDocument()
    expect(screen.getByText(/corporate \/ processor safe-harbors/i)).toBeInTheDocument()
  })
})
