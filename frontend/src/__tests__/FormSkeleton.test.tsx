/**
 * FormSkeleton component tests
 *
 * Tests: rendering default sections, custom section count,
 * custom fields per section, pulse animation.
 */
import { FormSkeleton } from '@/components/shared/skeletons/FormSkeleton'
import { render } from '@/test-utils'

describe('FormSkeleton', () => {
  it('renders 3 sections by default', () => {
    const { container } = render(<FormSkeleton />)
    const sections = container.querySelectorAll('.animate-pulse')
    expect(sections.length).toBe(3)
  })

  it('renders custom number of sections', () => {
    const { container } = render(<FormSkeleton sections={5} />)
    const sections = container.querySelectorAll('.animate-pulse')
    expect(sections.length).toBe(5)
  })

  it('renders section title placeholder', () => {
    const { container } = render(<FormSkeleton sections={1} />)
    // Title placeholder: h-5 w-28
    const titlePlaceholder = container.querySelector('.h-5.w-28')
    expect(titlePlaceholder).toBeInTheDocument()
  })

  it('renders correct number of field placeholders per section', () => {
    const { container } = render(<FormSkeleton sections={1} fieldsPerSection={4} />)
    // Each field is h-10, title is h-5 w-28
    const fields = container.querySelectorAll('.h-10')
    expect(fields.length).toBe(4)
  })

  it('renders with default fieldsPerSection of 3', () => {
    const { container } = render(<FormSkeleton sections={1} />)
    const fields = container.querySelectorAll('.h-10')
    expect(fields.length).toBe(3)
  })
})
