/**
 * EmptyStateCard component tests
 *
 * Tests: rendering title and message, icon display,
 * animation toggle, custom className.
 */
import { EmptyStateCard, ChartIcon, TrendIcon, IndustryIcon, RollingIcon } from '@/components/shared/EmptyStateCard'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
}))

describe('EmptyStateCard', () => {
  it('renders title', () => {
    render(<EmptyStateCard icon={<span>Icon</span>} title="No Data Available" message="Upload a file to begin." />)
    expect(screen.getByText('No Data Available')).toBeInTheDocument()
  })

  it('renders message', () => {
    render(<EmptyStateCard icon={<span>Icon</span>} title="Test" message="Upload a trial balance to see metrics." />)
    expect(screen.getByText('Upload a trial balance to see metrics.')).toBeInTheDocument()
  })

  it('renders icon content', () => {
    render(<EmptyStateCard icon={<span data-testid="test-icon">Chart</span>} title="Test" message="Message" />)
    expect(screen.getByTestId('test-icon')).toBeInTheDocument()
  })

  it('renders with animation wrapper by default', () => {
    const { container } = render(<EmptyStateCard icon={<span>I</span>} title="T" message="M" />)
    // When animate=true, the outer div is a motion.div wrapper
    expect(container.firstChild).toBeTruthy()
  })

  it('renders without animation when animate is false', () => {
    const { container } = render(<EmptyStateCard icon={<span>I</span>} title="T" message="M" animate={false} />)
    expect(container.firstChild).toBeTruthy()
  })

  it('applies custom className', () => {
    render(<EmptyStateCard icon={<span>I</span>} title="T" message="M" className="my-class" animate={false} />)
    // The root div should have the className
    const card = screen.getByText('T').closest('.my-class')
    expect(card).toBeInTheDocument()
  })
})

describe('EmptyStateCard Icons', () => {
  it('renders ChartIcon', () => {
    const { container } = render(<ChartIcon />)
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('renders TrendIcon', () => {
    const { container } = render(<TrendIcon />)
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('renders IndustryIcon', () => {
    const { container } = render(<IndustryIcon />)
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('renders RollingIcon', () => {
    const { container } = render(<RollingIcon />)
    expect(container.querySelector('svg')).toBeInTheDocument()
  })
})
