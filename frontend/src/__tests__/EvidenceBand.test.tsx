/**
 * EvidenceBand component tests
 *
 * Tests: rendering section header, credential cells,
 * CTA link, stat values.
 */
import { EvidenceBand } from '@/components/marketing/EvidenceBand'
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

jest.mock('@/components/shared', () => ({
  BrandIcon: ({ name, className }: any) => <span data-testid={`icon-${name}`} className={className} />,
}))

jest.mock('@/components/ui/Reveal', () => ({
  Reveal: ({ children, className }: any) => <div className={className}>{children}</div>,
}))

jest.mock('@/utils/marketingMotion', () => ({
  VIEWPORT: { eager: { once: true }, default: { once: true } },
}))

jest.mock('@/lib/motion', () => ({
  staggerContainerTight: { hidden: {}, visible: {} },
  fadeUp: { hidden: {}, visible: {} },
}))

jest.mock('@/utils/constants', () => ({
  ANALYSIS_LABEL_SHORT: 'Under 3s',
}))

describe('EvidenceBand', () => {
  it('renders section heading', () => {
    render(<EvidenceBand />)
    expect(screen.getByText('Standards-Driven by Design')).toBeInTheDocument()
  })

  it('renders Platform Credentials label', () => {
    render(<EvidenceBand />)
    expect(screen.getByText('Platform Credentials')).toBeInTheDocument()
  })

  it('renders stat values', () => {
    render(<EvidenceBand />)
    expect(screen.getByText('140+')).toBeInTheDocument()
    expect(screen.getByText('Zero')).toBeInTheDocument()
  })

  it('renders cell labels', () => {
    render(<EvidenceBand />)
    expect(screen.getByText('Automated Tests')).toBeInTheDocument()
    expect(screen.getByText('Per-Memo Citations')).toBeInTheDocument()
    expect(screen.getByText('Lines Stored')).toBeInTheDocument()
    expect(screen.getByText('Diagnostic Runtime')).toBeInTheDocument()
  })

  it('renders demo CTA link', () => {
    render(<EvidenceBand />)
    const link = screen.getByText(/Explore all 18 tools/)
    expect(link.closest('a')).toHaveAttribute('href', '/demo')
  })

  it('renders description text', () => {
    render(<EvidenceBand />)
    expect(screen.getByText(/Every test cites its standard/)).toBeInTheDocument()
  })
})
