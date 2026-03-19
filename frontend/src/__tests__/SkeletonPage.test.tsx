/**
 * SkeletonPage component tests
 *
 * Tests: rendering main element, title/subtitle placeholders,
 * custom widths, children rendering.
 */
import { SkeletonPage } from '@/components/shared/skeletons/SkeletonPage'
import { render, screen } from '@/test-utils'

describe('SkeletonPage', () => {
  it('renders main element', () => {
    const { container } = render(<SkeletonPage><div>Content</div></SkeletonPage>)
    expect(container.querySelector('main')).toBeInTheDocument()
  })

  it('renders children', () => {
    render(<SkeletonPage><div>Child Content</div></SkeletonPage>)
    expect(screen.getByText('Child Content')).toBeInTheDocument()
  })

  it('renders title placeholder with default width', () => {
    const { container } = render(<SkeletonPage><div /></SkeletonPage>)
    const title = container.querySelector('.h-8')
    expect(title).toHaveClass('w-56')
  })

  it('renders subtitle placeholder with default width', () => {
    const { container } = render(<SkeletonPage><div /></SkeletonPage>)
    const subtitle = container.querySelector('.h-4')
    expect(subtitle).toHaveClass('w-80')
  })

  it('applies custom title width', () => {
    const { container } = render(<SkeletonPage titleWidth="w-96"><div /></SkeletonPage>)
    const title = container.querySelector('.h-8')
    expect(title).toHaveClass('w-96')
  })

  it('applies custom subtitle width', () => {
    const { container } = render(<SkeletonPage subtitleWidth="w-48"><div /></SkeletonPage>)
    const subtitle = container.querySelector('.h-4')
    expect(subtitle).toHaveClass('w-48')
  })

  it('has pulse animation on header', () => {
    const { container } = render(<SkeletonPage><div /></SkeletonPage>)
    const pulseEl = container.querySelector('.animate-pulse')
    expect(pulseEl).toBeInTheDocument()
  })
})
