/**
 * ProcessTimeline component tests
 *
 * Tests: rendering section header, three steps,
 * step titles, descriptions, details, CTA hint.
 */
import { ProcessTimeline } from '@/components/marketing/ProcessTimeline'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  useInView: () => true,
}))

jest.mock('@/components/shared', () => ({
  BrandIcon: ({ name, className }: any) => <span data-testid={`icon-${name}`} className={className} />,
}))

jest.mock('@/components/ui/Reveal', () => ({
  Reveal: ({ children, className }: any) => <div className={className}>{children}</div>,
}))

jest.mock('@/utils/constants', () => ({
  ANALYSIS_LABEL_STANDARD: 'under 3 seconds',
}))

jest.mock('@/utils/marketingMotion', () => ({
  DRAW: {
    lineHorizontal: () => ({ hidden: {}, visible: {} }),
    lineVertical: () => ({ hidden: {}, visible: {} }),
  },
  VIEWPORT: { eager: { once: true }, default: { once: true } },
  CountUp: ({ target, pad }: any) => <span>{pad ? String(target).padStart(pad, '0') : target}</span>,
}))

jest.mock('@/utils/themeUtils', () => ({
  SPRING: { bouncy: {}, snappy: {} },
}))

jest.mock('@/utils/motionTokens', () => ({
  TIMING: {},
  EASE: {},
}))

jest.mock('@/lib/motion', () => ({
  staggerContainerTight: { hidden: {}, visible: {} },
  fadeUp: { hidden: {}, visible: {} },
}))

describe('ProcessTimeline', () => {
  it('renders section heading', () => {
    render(<ProcessTimeline />)
    expect(screen.getByText('From Raw Data to Diagnostic Intelligence')).toBeInTheDocument()
  })

  it('renders How It Works label', () => {
    render(<ProcessTimeline />)
    expect(screen.getByText('How It Works')).toBeInTheDocument()
  })

  it('renders Upload step', () => {
    render(<ProcessTimeline />)
    // Multiple "Upload" headings for desktop + mobile
    const uploadElements = screen.getAllByText('Upload')
    expect(uploadElements.length).toBeGreaterThanOrEqual(1)
  })

  it('renders Analyze step', () => {
    render(<ProcessTimeline />)
    const analyzeElements = screen.getAllByText('Analyze')
    expect(analyzeElements.length).toBeGreaterThanOrEqual(1)
  })

  it('renders Export step', () => {
    render(<ProcessTimeline />)
    const exportElements = screen.getAllByText('Export')
    expect(exportElements.length).toBeGreaterThanOrEqual(1)
  })

  it('renders step descriptions', () => {
    render(<ProcessTimeline />)
    expect(screen.getAllByText('Raw trial balance data').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Intelligent classification').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Reclassified intelligence').length).toBeGreaterThanOrEqual(1)
  })

  it('renders analysis time hint', () => {
    render(<ProcessTimeline />)
    expect(screen.getByText('under 3 seconds')).toBeInTheDocument()
  })

  it('renders description text', () => {
    render(<ProcessTimeline />)
    expect(screen.getByText(/Upload your source document/)).toBeInTheDocument()
  })
})
