/**
 * BottomProof component tests
 *
 * Tests: section heading, credential badges, closing metrics,
 * CTA links, auth-aware CTA.
 */
import { BottomProof } from '@/components/marketing/BottomProof'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
    span: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <span {...rest}>{children}</span>,
  },
}))

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, ...rest }: any) => <a href={href} {...rest}>{children}</a>,
}))

jest.mock('@/components/ui/Reveal', () => ({
  Reveal: ({ children, className }: any) => <div className={className}>{children}</div>,
}))

jest.mock('@/utils/marketingMotion', () => ({
  VIEWPORT: { eager: { once: true } },
  CountUp: ({ target, suffix }: any) => <span>{target}{suffix || ''}</span>,
}))

jest.mock('@/lib/motion', () => ({
  staggerContainerTight: { hidden: {}, visible: {} },
  fadeUp: { hidden: {}, visible: {} },
}))

let mockAuth = { isAuthenticated: false }
jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: () => mockAuth,
}))

describe('BottomProof', () => {
  beforeEach(() => {
    mockAuth = { isAuthenticated: false }
  })

  it('renders section heading', () => {
    render(<BottomProof />)
    expect(screen.getByText('Every Test Cites Its Standard')).toBeInTheDocument()
  })

  it('renders Professional Standards label', () => {
    render(<BottomProof />)
    expect(screen.getByText('Professional Standards')).toBeInTheDocument()
  })

  it('renders credential badges', () => {
    // Sprint 705: pill strip replaced with <StandardsSpecimen>, which
    // emits each code twice (desktop specimen row + mobile fallback
    // link). getByText would throw on the duplicate; getAllByText is
    // the correct assertion — the intent is "these standards appear
    // on the page," and they do.
    render(<BottomProof />)
    expect(screen.getAllByText(/ISA 240/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/PCAOB AS 2315/).length).toBeGreaterThan(0)
  })

  it('renders closing metrics', () => {
    render(<BottomProof />)
    expect(screen.getByText('Automated Tests')).toBeInTheDocument()
    expect(screen.getByText('Audit Tools')).toBeInTheDocument()
    expect(screen.getByText('Standards Referenced')).toBeInTheDocument()
  })

  it('renders Explore Demo link', () => {
    render(<BottomProof />)
    const link = screen.getByText('Explore Demo')
    expect(link.closest('a')).toHaveAttribute('href', '/demo')
  })

  it('renders description text', () => {
    render(<BottomProof />)
    expect(screen.getByText(/Twelve audit-focused tools/)).toBeInTheDocument()
  })
})
