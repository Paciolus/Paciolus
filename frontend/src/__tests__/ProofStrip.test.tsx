/**
 * ProofStrip component tests
 *
 * Tests: rendering industry badges, outcome metrics,
 * section label.
 */
import { ProofStrip } from '@/components/marketing/ProofStrip'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
}))

jest.mock('@/components/shared', () => ({
  BrandIcon: ({ name, className }: any) => <span data-testid={`icon-${name}`} className={className} />,
}))

jest.mock('@/components/ui/Reveal', () => ({
  Reveal: ({ children }: any) => <div>{children}</div>,
}))

jest.mock('@/utils/marketingMotion', () => ({
  VIEWPORT: { eager: { once: true }, default: { once: true } },
}))

jest.mock('@/lib/motion', () => ({
  staggerContainerTight: { hidden: {}, visible: {} },
  fadeUp: { hidden: {}, visible: {} },
}))

describe('ProofStrip', () => {
  it('renders section label', () => {
    render(<ProofStrip />)
    expect(screen.getByText('Used across the profession')).toBeInTheDocument()
  })

  it('renders industry badges', () => {
    render(<ProofStrip />)
    expect(screen.getByText('CPA Firms')).toBeInTheDocument()
    expect(screen.getByText('Internal Audit')).toBeInTheDocument()
    expect(screen.getByText('Corporate Finance')).toBeInTheDocument()
    expect(screen.getByText('Consulting')).toBeInTheDocument()
    expect(screen.getByText('Government')).toBeInTheDocument()
    expect(screen.getByText('Non-Profit')).toBeInTheDocument()
  })

  it('renders outcome metrics', () => {
    render(<ProofStrip />)
    expect(screen.getByText('Typically under three seconds')).toBeInTheDocument()
    expect(screen.getByText('Zero file storage')).toBeInTheDocument()
    expect(screen.getByText('ISA & PCAOB')).toBeInTheDocument()
    expect(screen.getByText('140+ automated tests')).toBeInTheDocument()
  })

  it('renders metric labels', () => {
    render(<ProofStrip />)
    expect(screen.getByText('For standard file sizes')).toBeInTheDocument()
    expect(screen.getByText('Raw files destroyed on completion')).toBeInTheDocument()
    expect(screen.getByText('Standards-aligned output')).toBeInTheDocument()
    expect(screen.getByText('Across all 18 tools')).toBeInTheDocument()
  })
})
