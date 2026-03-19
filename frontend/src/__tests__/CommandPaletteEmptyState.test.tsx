/**
 * CommandPalette EmptyState component tests
 *
 * Tests: rendering with/without query, context-aware suggestions.
 */
import { EmptyState } from '@/components/shared/CommandPalette/EmptyState'
import { render, screen } from '@/test-utils'

let mockPathname = '/'
jest.mock('next/navigation', () => ({
  usePathname: () => mockPathname,
}))

describe('CommandPalette EmptyState', () => {
  beforeEach(() => {
    mockPathname = '/'
  })

  it('shows "No commands available" when no query', () => {
    render(<EmptyState query="" />)
    expect(screen.getByText('No commands available')).toBeInTheDocument()
  })

  it('shows "No results found" when query is provided', () => {
    render(<EmptyState query="something" />)
    expect(screen.getByText('No results found')).toBeInTheDocument()
  })

  it('shows default suggestion on home page', () => {
    mockPathname = '/'
    render(<EmptyState query="" />)
    expect(screen.getByText(/Try "tools", "settings", or a client name/)).toBeInTheDocument()
  })

  it('shows tool-specific suggestion on tools page', () => {
    mockPathname = '/tools/trial-balance'
    render(<EmptyState query="" />)
    expect(screen.getByText(/Try searching for a tool name/)).toBeInTheDocument()
  })

  it('shows workspace-specific suggestion on engagements page', () => {
    mockPathname = '/engagements'
    render(<EmptyState query="" />)
    expect(screen.getByText(/Try a client name/)).toBeInTheDocument()
  })
})
