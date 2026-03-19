/**
 * ToolNav component tests
 *
 * Tests: rendering tool links, current tool highlighting,
 * More dropdown, navigation structure.
 */
import { ToolNav } from '@/components/shared/ToolNav'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
}))

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, ...rest }: any) => <a href={href} {...rest}>{children}</a>,
}))

jest.mock('next/image', () => ({
  __esModule: true,
  default: ({ alt = '', ...props }: any) => <img alt={alt} {...props} />,
}))

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: () => ({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    logout: jest.fn(),
  }),
}))

jest.mock('@/components/auth', () => ({
  ProfileDropdown: () => <div data-testid="profile-dropdown" />,
}))

jest.mock('@/components/shared/BrandIcon', () => ({
  BrandIcon: ({ name, className }: any) => <span data-testid={`icon-${name}`} className={className} />,
}))

jest.mock('@/hooks/useCommandPalette', () => ({
  useCommandPalette: () => ({ openPalette: jest.fn() }),
}))

describe('ToolNav', () => {
  it('renders nav element', () => {
    render(<ToolNav currentTool="tb-diagnostics" />)
    expect(screen.getByRole('navigation', { name: 'Tool navigation' })).toBeInTheDocument()
  })

  it('renders first 6 inline tool labels', () => {
    render(<ToolNav currentTool="tb-diagnostics" />)
    expect(screen.getByText('TB Diagnostics')).toBeInTheDocument()
    expect(screen.getByText('Multi-Period')).toBeInTheDocument()
    expect(screen.getByText('JE Testing')).toBeInTheDocument()
  })

  it('highlights current tool (not a link)', () => {
    render(<ToolNav currentTool="tb-diagnostics" />)
    const tbEl = screen.getByText('TB Diagnostics')
    // Current tool is a span, not a link
    expect(tbEl.tagName).toBe('SPAN')
  })

  it('renders non-current tools as links', () => {
    render(<ToolNav currentTool="tb-diagnostics" />)
    const jeLink = screen.getByText('JE Testing')
    expect(jeLink.closest('a')).toHaveAttribute('href', '/tools/journal-entry-testing')
  })

  it('renders More button for overflow tools', () => {
    render(<ToolNav currentTool="tb-diagnostics" />)
    const moreBtn = screen.getByRole('button', { name: /More/ })
    expect(moreBtn).toBeInTheDocument()
  })

  it('renders Workspaces link', () => {
    render(<ToolNav currentTool="tb-diagnostics" />)
    const link = screen.getByText('Workspaces')
    expect(link.closest('a')).toHaveAttribute('href', '/engagements')
  })

  it('shows Sign In when not authenticated', () => {
    render(<ToolNav currentTool="tb-diagnostics" />)
    const signIn = screen.getByText('Sign In')
    expect(signIn.closest('a')).toHaveAttribute('href', '/login')
  })
})
