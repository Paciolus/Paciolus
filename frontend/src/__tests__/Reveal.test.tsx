/**
 * Reveal component tests
 *
 * Tests: rendering children, className prop, delay prop.
 */
import { Reveal } from '@/components/ui/Reveal'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ ref, initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  useInView: () => true,
}))

jest.mock('@/lib/motion', () => ({
  fadeUp: { hidden: {}, visible: {} },
  duration: { base: 0.5 },
  ease: { out: [0, 0, 0.2, 1] },
  lift: {},
  useMotionPreference: () => ({ prefersReducedMotion: false }),
}))

describe('Reveal', () => {
  it('renders children', () => {
    render(<Reveal>Test Content</Reveal>)
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('applies className', () => {
    const { container } = render(<Reveal className="my-class">Content</Reveal>)
    expect(container.firstChild).toHaveClass('my-class')
  })

  it('renders nested elements', () => {
    render(
      <Reveal>
        <h1>Title</h1>
        <p>Paragraph</p>
      </Reveal>
    )
    expect(screen.getByText('Title')).toBeInTheDocument()
    expect(screen.getByText('Paragraph')).toBeInTheDocument()
  })

  it('renders with delay prop without error', () => {
    render(<Reveal delay={0.1}>Content</Reveal>)
    expect(screen.getByText('Content')).toBeInTheDocument()
  })
})
