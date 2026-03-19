/**
 * CardGridSkeleton component tests
 *
 * Tests: rendering default cards, custom count, variants,
 * custom column classes, pulse animation.
 */
import { CardGridSkeleton } from '@/components/shared/skeletons/CardGridSkeleton'
import { render } from '@/test-utils'

describe('CardGridSkeleton', () => {
  it('renders 3 cards by default', () => {
    const { container } = render(<CardGridSkeleton />)
    const cards = container.querySelectorAll('.animate-pulse')
    expect(cards.length).toBe(3)
  })

  it('renders custom number of cards', () => {
    const { container } = render(<CardGridSkeleton count={6} />)
    const cards = container.querySelectorAll('.animate-pulse')
    expect(cards.length).toBe(6)
  })

  it('applies default grid columns class', () => {
    const { container } = render(<CardGridSkeleton />)
    const grid = container.firstChild as HTMLElement
    expect(grid.className).toContain('grid-cols-1')
  })

  it('applies custom columns class', () => {
    const { container } = render(<CardGridSkeleton columns="grid-cols-2" />)
    const grid = container.firstChild as HTMLElement
    expect(grid.className).toContain('grid-cols-2')
  })

  it('renders default variant content', () => {
    const { container } = render(<CardGridSkeleton count={1} variant="default" />)
    const titleBar = container.querySelector('.h-5.w-24')
    expect(titleBar).toBeInTheDocument()
  })

  it('renders detailed variant with button placeholder', () => {
    const { container } = render(<CardGridSkeleton count={1} variant="detailed" />)
    const buttonBar = container.querySelector('.h-8.w-24')
    expect(buttonBar).toBeInTheDocument()
  })

  it('renders compact variant', () => {
    const { container } = render(<CardGridSkeleton count={1} variant="compact" />)
    const titleBar = container.querySelector('.h-5.w-36')
    expect(titleBar).toBeInTheDocument()
  })
})
