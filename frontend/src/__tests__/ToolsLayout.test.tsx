/**
 * Sprint 231 / Sprint 482: ToolsLayout tests
 *
 * Rewritten for Sprint 475 layout refactor: ToolsLayout now renders
 * AuthenticatedShell (UnifiedToolbar + VerificationBanner) + EngagementProvider.
 */
import React from 'react'
import ToolsLayout from '@/app/tools/layout'
import { render, screen } from '@/test-utils'

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

jest.mock('@/components/shell', () => ({
  AuthenticatedShell: ({ children }: { children: React.ReactNode }) => <div data-testid="authenticated-shell">{children}</div>,
}))
jest.mock('@/components/shared/SonificationToggle', () => ({
  SonificationToggle: () => <div data-testid="sonification-toggle" />,
}))
jest.mock('@/components/engagement', () => ({
  EngagementBanner: () => <div data-testid="engagement-banner">Engagement</div>,
  ToolLinkToast: () => null,
}))


describe('ToolsLayout', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders AuthenticatedShell', () => {
    render(<ToolsLayout><div>child</div></ToolsLayout>)
    expect(screen.getByTestId('authenticated-shell')).toBeInTheDocument()
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

  it('renders SonificationToggle', () => {
    render(<ToolsLayout><div>child</div></ToolsLayout>)
    expect(screen.getByTestId('sonification-toggle')).toBeInTheDocument()
  })

  it('renders children inside the shell', () => {
    render(<ToolsLayout><div data-testid="page-content">Page</div></ToolsLayout>)
    expect(screen.getByTestId('page-content')).toBeInTheDocument()
  })
})
