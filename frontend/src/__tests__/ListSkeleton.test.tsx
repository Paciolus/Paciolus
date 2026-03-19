/**
 * ListSkeleton component tests
 *
 * Tests: rendering default rows, custom row count,
 * avatar visibility, pulse animation.
 */
import { ListSkeleton } from '@/components/shared/skeletons/ListSkeleton'
import { render } from '@/test-utils'

describe('ListSkeleton', () => {
  it('renders 5 rows by default', () => {
    const { container } = render(<ListSkeleton />)
    const rows = container.querySelectorAll('.animate-pulse')
    expect(rows.length).toBe(5)
  })

  it('renders custom number of rows', () => {
    const { container } = render(<ListSkeleton rows={3} />)
    const rows = container.querySelectorAll('.animate-pulse')
    expect(rows.length).toBe(3)
  })

  it('shows avatar circles by default', () => {
    const { container } = render(<ListSkeleton rows={1} />)
    const avatars = container.querySelectorAll('.rounded-full.w-10')
    expect(avatars.length).toBe(1)
  })

  it('hides avatar circles when showAvatar is false', () => {
    const { container } = render(<ListSkeleton rows={1} showAvatar={false} />)
    const avatars = container.querySelectorAll('.rounded-full.w-10')
    expect(avatars.length).toBe(0)
  })

  it('renders title and subtitle placeholders per row', () => {
    const { container } = render(<ListSkeleton rows={1} />)
    // title: h-4 w-48, subtitle: h-3 w-32
    const title = container.querySelector('.h-4.w-48')
    const subtitle = container.querySelector('.h-3.w-32')
    expect(title).toBeInTheDocument()
    expect(subtitle).toBeInTheDocument()
  })

  it('applies custom gap class', () => {
    const { container } = render(<ListSkeleton gap="gap-2" />)
    expect(container.firstChild).toHaveClass('gap-2')
  })
})
