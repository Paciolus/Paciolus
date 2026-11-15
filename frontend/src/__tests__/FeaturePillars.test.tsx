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
    expect(screen.getByText('What You Get')).toBeInTheDocument()
  })

  it('renders Why Paciolus label', () => {
    render(<FeaturePillars />)
    expect(screen.getByText('Why Paciolus')).toBeInTheDocument()
  })

  it('renders the uploads-not-kept pillar', () => {
    render(<FeaturePillars />)
    expect(screen.getByText('Uploads Not Kept')).toBeInTheDocument()
    expect(screen.getByText('Processed in memory.')).toBeInTheDocument()
  })

  it('renders Precision pillar', () => {
    render(<FeaturePillars />)
    expect(screen.getByText('Your Materiality, Your Thresholds')).toBeInTheDocument()
    expect(screen.getByText('Set per engagement.')).toBeInTheDocument()
  })

  it('renders Professional-Grade Exports pillar', () => {
    render(<FeaturePillars />)
    expect(screen.getByText('PDF Memos and Excel Workpapers')).toBeInTheDocument()
    expect(screen.getByText('For your review.')).toBeInTheDocument()
  })

  it('renders pillar descriptions', () => {
    render(<FeaturePillars />)
    expect(screen.getByText(/We save your account, client list, analysis summaries/)).toBeInTheDocument()
    expect(screen.getByText(/You set materiality for each engagement/)).toBeInTheDocument()
    expect(screen.getByText(/Paciolus is not a workpaper archive/)).toBeInTheDocument()
  })

  it('renders brand icons for each pillar', () => {
    render(<FeaturePillars />)
    expect(screen.getByTestId('icon-padlock')).toBeInTheDocument()
    expect(screen.getByTestId('icon-sliders')).toBeInTheDocument()
    expect(screen.getByTestId('icon-document')).toBeInTheDocument()
  })
})
