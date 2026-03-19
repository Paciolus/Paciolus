/**
 * MarketingNav component tests
 *
 * Tests: rendering nav, logo, links, CTA button.
 */
import { MarketingNav } from '@/components/marketing/MarketingNav'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
    nav: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <nav {...rest}>{children}</nav>,
    span: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <span {...rest}>{children}</span>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
  useScroll: () => ({ scrollY: { get: () => 0 } }),
  useMotionValueEvent: jest.fn(),
  useTransform: () => 0,
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
  }),
}))

jest.mock('@/components/auth', () => ({
  ProfileDropdown: () => <div data-testid="profile-dropdown" />,
}))

describe('MarketingNav', () => {
  it('renders navigation element', () => {
    render(<MarketingNav />)
    const navs = screen.getAllByRole('navigation')
    expect(navs.length).toBeGreaterThan(0)
  })

  it('renders Paciolus logo', () => {
    render(<MarketingNav />)
    const logo = screen.getByAltText('Paciolus')
    expect(logo).toBeInTheDocument()
  })

  it('renders link to pricing', () => {
    render(<MarketingNav />)
    const links = screen.getAllByRole('link')
    const hrefs = links.map(l => l.getAttribute('href'))
    expect(hrefs).toContain('/pricing')
  })

  it('renders Sign In link when not authenticated', () => {
    render(<MarketingNav />)
    const signInLinks = screen.getAllByText(/Sign In/)
    expect(signInLinks.length).toBeGreaterThan(0)
  })
})
