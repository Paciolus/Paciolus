/**
 * DisclaimerBox component tests
 *
 * Tests: rendering with children, Disclaimer prefix,
 * custom className, default className.
 */
import { DisclaimerBox } from '@/components/shared/DisclaimerBox'
import { render, screen } from '@/test-utils'

describe('DisclaimerBox', () => {
  it('renders children content', () => {
    render(<DisclaimerBox>This is test disclaimer content.</DisclaimerBox>)
    expect(screen.getByText(/This is test disclaimer content/)).toBeInTheDocument()
  })

  it('renders Disclaimer prefix', () => {
    render(<DisclaimerBox>Some content</DisclaimerBox>)
    expect(screen.getByText('Disclaimer:')).toBeInTheDocument()
  })

  it('applies default className mt-8', () => {
    const { container } = render(<DisclaimerBox>Content</DisclaimerBox>)
    expect(container.firstChild).toHaveClass('mt-8')
  })

  it('applies custom className', () => {
    const { container } = render(<DisclaimerBox className="mt-4">Content</DisclaimerBox>)
    expect(container.firstChild).toHaveClass('mt-4')
  })

  it('renders as a paragraph with correct styling', () => {
    render(<DisclaimerBox>Content</DisclaimerBox>)
    const prefix = screen.getByText('Disclaimer:')
    expect(prefix.className).toContain('font-medium')
  })

  it('renders complex children content', () => {
    render(
      <DisclaimerBox>
        <span>Complex</span> disclaimer with <strong>formatting</strong>
      </DisclaimerBox>
    )
    expect(screen.getByText('Complex')).toBeInTheDocument()
    expect(screen.getByText('formatting')).toBeInTheDocument()
  })
})
