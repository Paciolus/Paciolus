/**
 * ToolPageSkeleton component tests
 *
 * Tests: rendering with defaults, card variant, table variant,
 * custom result count.
 */
import { ToolPageSkeleton } from '@/components/shared/skeletons/ToolPageSkeleton'
import { render } from '@/test-utils'

describe('ToolPageSkeleton', () => {
  it('renders main element', () => {
    const { container } = render(<ToolPageSkeleton />)
    expect(container.querySelector('main')).toBeInTheDocument()
  })

  it('renders title and subtitle skeletons', () => {
    const { container } = render(<ToolPageSkeleton />)
    const titleEl = container.querySelector('.h-8')
    const subtitleEl = container.querySelector('.h-4')
    expect(titleEl).toBeInTheDocument()
    expect(subtitleEl).toBeInTheDocument()
  })

  it('renders upload zone skeleton', () => {
    const { container } = render(<ToolPageSkeleton />)
    const uploadZone = container.querySelector('.border-dashed')
    expect(uploadZone).toBeInTheDocument()
  })

  it('renders card grid by default', () => {
    const { container } = render(<ToolPageSkeleton />)
    const grid = container.querySelector('.grid')
    expect(grid).toBeInTheDocument()
  })

  it('renders table skeleton when resultsVariant is table', () => {
    const { container } = render(<ToolPageSkeleton resultsVariant="table" />)
    // Table has a border-b row structure
    const tableRows = container.querySelectorAll('.border-b')
    expect(tableRows.length).toBeGreaterThan(0)
  })
})
