/**
 * FeaturePillars component tests
 *
 * Tests: rendering section header, three pillars,
 * pillar titles, taglines, descriptions.
 */
import { FeaturePillars } from '@/components/marketing/FeaturePillars'
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
  Reveal: ({ children, className }: any) => <div className={className}>{children}</div>,
}))

jest.mock('@/utils/chartTheme', () => ({
  CHART_SHADOWS: { darkShadow: (o: number) => `rgba(0,0,0,${o})` },
}))

jest.mock('@/utils/marketingMotion', () => ({
  HOVER: { iconPulse: { rest: {}, hover: {} } },
  VIEWPORT: { eager: { once: true }, default: { once: true } },
}))

jest.mock('@/lib/motion', () => ({
  staggerContainerTight: { hidden: {}, visible: {} },
  fadeUp: { hidden: {}, visible: {} },
}))

describe('FeaturePillars', () => {
  it('renders section heading', () => {
    render(<FeaturePillars />)
    expect(screen.getByText('Built for Financial Professionals')).toBeInTheDocument()
  })

  it('renders Why Paciolus label', () => {
    render(<FeaturePillars />)
    expect(screen.getByText('Why Paciolus')).toBeInTheDocument()
  })

  it('renders Zero-Storage Security pillar', () => {
    render(<FeaturePillars />)
    expect(screen.getByText('Zero-Storage Security')).toBeInTheDocument()
    expect(screen.getByText('Never written to disk. Never retained.')).toBeInTheDocument()
  })

  it('renders Precision pillar', () => {
    render(<FeaturePillars />)
    expect(screen.getByText('Precision at Every Threshold')).toBeInTheDocument()
    expect(screen.getByText('Set once. Applied everywhere.')).toBeInTheDocument()
  })

  it('renders Professional-Grade Exports pillar', () => {
    render(<FeaturePillars />)
    expect(screen.getByText('Professional-Grade Exports')).toBeInTheDocument()
    expect(screen.getByText('Done before you close the tab.')).toBeInTheDocument()
  })

  it('renders pillar descriptions', () => {
    render(<FeaturePillars />)
    expect(screen.getByText(/processed in-memory/)).toBeInTheDocument()
    expect(screen.getByText(/Configure materiality/)).toBeInTheDocument()
    expect(screen.getByText(/PDF memos with ISA and PCAOB citations/)).toBeInTheDocument()
  })

  it('renders brand icons for each pillar', () => {
    render(<FeaturePillars />)
    expect(screen.getByTestId('icon-padlock')).toBeInTheDocument()
    expect(screen.getByTestId('icon-sliders')).toBeInTheDocument()
    expect(screen.getByTestId('icon-document')).toBeInTheDocument()
  })
})
