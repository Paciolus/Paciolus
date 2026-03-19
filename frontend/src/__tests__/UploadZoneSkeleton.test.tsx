/**
 * UploadZoneSkeleton component tests
 *
 * Tests: rendering dashed border, icon placeholder,
 * text placeholders, pulse animation.
 */
import { UploadZoneSkeleton } from '@/components/shared/skeletons/UploadZoneSkeleton'
import { render } from '@/test-utils'

describe('UploadZoneSkeleton', () => {
  it('renders with animate-pulse', () => {
    const { container } = render(<UploadZoneSkeleton />)
    expect(container.firstChild).toHaveClass('animate-pulse')
  })

  it('renders dashed border', () => {
    const { container } = render(<UploadZoneSkeleton />)
    expect(container.firstChild).toHaveClass('border-dashed')
  })

  it('renders icon placeholder circle', () => {
    const { container } = render(<UploadZoneSkeleton />)
    const iconPlaceholder = container.querySelector('.w-12.h-12.rounded-full')
    expect(iconPlaceholder).toBeInTheDocument()
  })

  it('renders title placeholder', () => {
    const { container } = render(<UploadZoneSkeleton />)
    const titlePlaceholder = container.querySelector('.h-4.w-48')
    expect(titlePlaceholder).toBeInTheDocument()
  })

  it('renders subtitle placeholder', () => {
    const { container } = render(<UploadZoneSkeleton />)
    const subtitlePlaceholder = container.querySelector('.h-3.w-32')
    expect(subtitlePlaceholder).toBeInTheDocument()
  })
})
