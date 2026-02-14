/**
 * Sprint 231: ToolsLayout tests — verifies layout-level concerns
 * (ToolNav, VerificationBanner, EngagementProvider) that were moved
 * from individual pages in Sprint 207.
 */
import { render, screen } from '@/test-utils'

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/contexts/EngagementContext', () => ({
  EngagementProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="engagement-provider">{children}</div>,
  useEngagementContext: jest.fn(() => ({
    activeEngagement: null, clearEngagement: jest.fn(), toastMessage: null, dismissToast: jest.fn(),
  })),
}))

jest.mock('next/navigation', () => ({
  usePathname: jest.fn(() => '/tools/trial-balance'),
  useSearchParams: jest.fn(() => new URLSearchParams()),
  useRouter: jest.fn(() => ({ push: jest.fn(), replace: jest.fn() })),
}))

jest.mock('@/components/shared', () => ({
  ToolNav: ({ currentTool }: { currentTool: string }) => <nav data-testid="tool-nav" data-tool={currentTool}>Nav</nav>,
}))
jest.mock('@/components/auth', () => ({
  VerificationBanner: () => <div data-testid="verification-banner">Verify</div>,
}))
jest.mock('@/components/engagement', () => ({
  EngagementBanner: () => <div data-testid="engagement-banner">Engagement</div>,
  ToolLinkToast: () => null,
}))

import ToolsLayout from '@/app/tools/layout'
import { usePathname } from 'next/navigation'

const mockUsePathname = usePathname as jest.Mock

describe('ToolsLayout', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUsePathname.mockReturnValue('/tools/trial-balance')
  })

  it('renders ToolNav', () => {
    render(<ToolsLayout><div>child</div></ToolsLayout>)
    expect(screen.getByTestId('tool-nav')).toBeInTheDocument()
  })

  it('renders VerificationBanner', () => {
    render(<ToolsLayout><div>child</div></ToolsLayout>)
    expect(screen.getByTestId('verification-banner')).toBeInTheDocument()
  })

  it('wraps children in EngagementProvider', () => {
    render(<ToolsLayout><div>child</div></ToolsLayout>)
    expect(screen.getByTestId('engagement-provider')).toBeInTheDocument()
    expect(screen.getByText('child')).toBeInTheDocument()
  })

  it('renders EngagementBanner', () => {
    render(<ToolsLayout><div>child</div></ToolsLayout>)
    expect(screen.getByTestId('engagement-banner')).toBeInTheDocument()
  })

  it('derives currentTool from pathname for trial-balance', () => {
    mockUsePathname.mockReturnValue('/tools/trial-balance')
    render(<ToolsLayout><div>child</div></ToolsLayout>)
    expect(screen.getByTestId('tool-nav')).toHaveAttribute('data-tool', 'tb-diagnostics')
  })

  it('derives currentTool from pathname for journal-entry-testing', () => {
    mockUsePathname.mockReturnValue('/tools/journal-entry-testing')
    render(<ToolsLayout><div>child</div></ToolsLayout>)
    expect(screen.getByTestId('tool-nav')).toHaveAttribute('data-tool', 'je-testing')
  })

  it('defaults to tb-diagnostics for unknown segments', () => {
    mockUsePathname.mockReturnValue('/tools/unknown-tool')
    render(<ToolsLayout><div>child</div></ToolsLayout>)
    expect(screen.getByTestId('tool-nav')).toHaveAttribute('data-tool', 'tb-diagnostics')
  })
})
