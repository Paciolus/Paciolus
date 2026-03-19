/**
 * MarketingFooter component tests
 *
 * Tests: rendering footer links, brand section, disclaimer,
 * copyright, legal links, auth shortcuts.
 */
import { MarketingFooter } from '@/components/marketing/MarketingFooter'
import { render, screen } from '@/test-utils'

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, ...rest }: any) => <a href={href} {...rest}>{children}</a>,
}))

jest.mock('next/image', () => ({
  __esModule: true,
  default: ({ alt = '', ...props }: any) => <img alt={alt} {...props} />,
}))

jest.mock('@/components/shared', () => ({
  BrandIcon: ({ name, className }: any) => <span data-testid={`icon-${name}`} className={className} />,
}))

describe('MarketingFooter', () => {
  it('renders footer element', () => {
    render(<MarketingFooter />)
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
  })

  it('renders Solutions section', () => {
    render(<MarketingFooter />)
    expect(screen.getByText('Solutions')).toBeInTheDocument()
  })

  it('renders Company section', () => {
    render(<MarketingFooter />)
    expect(screen.getByText('Company')).toBeInTheDocument()
  })

  it('renders Legal section', () => {
    render(<MarketingFooter />)
    expect(screen.getByText('Legal')).toBeInTheDocument()
  })

  it('renders Privacy Policy link', () => {
    render(<MarketingFooter />)
    const link = screen.getByText('Privacy Policy')
    expect(link.closest('a')).toHaveAttribute('href', '/privacy')
  })

  it('renders Terms of Service link', () => {
    render(<MarketingFooter />)
    const link = screen.getByText('Terms of Service')
    expect(link.closest('a')).toHaveAttribute('href', '/terms')
  })

  it('renders Start Free Trial link', () => {
    render(<MarketingFooter />)
    const link = screen.getByText('Start Free Trial')
    expect(link.closest('a')).toHaveAttribute('href', '/register')
  })

  it('renders Sign In link', () => {
    render(<MarketingFooter />)
    const link = screen.getByText('Sign In')
    expect(link.closest('a')).toHaveAttribute('href', '/login')
  })

  it('renders Zero-Storage Architecture badge', () => {
    render(<MarketingFooter />)
    expect(screen.getByText('Zero-Storage Architecture')).toBeInTheDocument()
  })

  it('renders Pacioli motto', () => {
    render(<MarketingFooter />)
    expect(screen.getByText(/Particularis de Computis/)).toBeInTheDocument()
  })

  it('renders disclaimer text', () => {
    render(<MarketingFooter />)
    expect(screen.getByText(/data analytics tool for financial professionals/)).toBeInTheDocument()
  })

  it('renders copyright', () => {
    render(<MarketingFooter />)
    expect(screen.getByText(/Paciolus, Inc/)).toBeInTheDocument()
  })
})
