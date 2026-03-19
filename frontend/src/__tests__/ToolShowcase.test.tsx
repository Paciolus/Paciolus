/**
 * ToolShowcase component tests
 *
 * Tests: rendering section heading, tool cards.
 */
import { ToolShowcase } from '@/components/marketing/ToolShowcase'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
    span: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <span {...rest}>{children}</span>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
  useInView: () => true,
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
  HOVER: { iconPulse: { rest: {}, hover: {} } },
  VIEWPORT: { eager: { once: true }, default: { once: true } },
}))

jest.mock('@/lib/motion', () => ({
  staggerContainerTight: { hidden: {}, visible: {} },
  fadeUp: { hidden: {}, visible: {} },
}))

jest.mock('@/utils/chartTheme', () => ({
  CHART_SHADOWS: { darkShadow: (o: number) => `rgba(0,0,0,${o})` },
}))

describe('ToolShowcase', () => {
  it('renders without crashing', () => {
    render(<ToolShowcase />)
    const section = document.querySelector('section')
    expect(section).toBeInTheDocument()
  })

  it('renders heading text', () => {
    render(<ToolShowcase />)
    const headings = screen.getAllByRole('heading')
    expect(headings.length).toBeGreaterThan(0)
  })

  it('renders tool category labels', () => {
    render(<ToolShowcase />)
    // ToolShowcase renders categories of tools
    const section = document.querySelector('section')
    expect(section?.textContent?.length).toBeGreaterThan(0)
  })

  it('renders demo CTA link', () => {
    render(<ToolShowcase />)
    const links = screen.getAllByRole('link')
    expect(links.length).toBeGreaterThan(0)
  })
})
