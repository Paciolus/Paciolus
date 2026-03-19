/**
 * UsageMeter component tests
 *
 * Tests: rendering label, usage count, unlimited state,
 * near-limit state, at-limit state, progress bar.
 */
import { UsageMeter } from '@/components/shared/UsageMeter'
import { render, screen } from '@/test-utils'

describe('UsageMeter', () => {
  it('renders label', () => {
    render(<UsageMeter used={5} limit={10} label="Diagnostics" />)
    expect(screen.getByText('Diagnostics')).toBeInTheDocument()
  })

  it('shows used / limit count', () => {
    render(<UsageMeter used={3} limit={10} label="Clients" />)
    expect(screen.getByText('3 / 10')).toBeInTheDocument()
  })

  it('shows Unlimited when limit is 0', () => {
    render(<UsageMeter used={15} limit={0} label="Diagnostics" />)
    expect(screen.getByText('Unlimited')).toBeInTheDocument()
  })

  it('does not render progress bar when unlimited', () => {
    const { container } = render(<UsageMeter used={5} limit={0} label="Test" />)
    expect(container.querySelector('.bg-sage-500')).toBeNull()
    expect(container.querySelector('.bg-clay-500')).toBeNull()
  })

  it('renders progress bar when not unlimited', () => {
    const { container } = render(<UsageMeter used={5} limit={10} label="Test" />)
    const progressBar = container.querySelector('.h-2')
    expect(progressBar).toBeInTheDocument()
  })

  it('shows warning color near limit (80%+)', () => {
    const { container } = render(<UsageMeter used={8} limit={10} label="Test" />)
    const counter = screen.getByText('8 / 10')
    // Near limit should have clay-400 color
    expect(counter.className).toContain('text-clay-400')
  })

  it('shows error color at limit', () => {
    const { container } = render(<UsageMeter used={10} limit={10} label="Test" />)
    const counter = screen.getByText('10 / 10')
    expect(counter.className).toContain('text-clay-600')
  })
})
