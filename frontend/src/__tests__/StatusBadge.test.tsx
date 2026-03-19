/**
 * StatusBadge component tests
 *
 * Tests: rendering label, applying color classes.
 */
import { StatusBadge } from '@/components/shared/StatusBadge'
import { render, screen } from '@/test-utils'

describe('StatusBadge', () => {
  it('renders the label text', () => {
    render(<StatusBadge label="Active" colors={{ bg: 'bg-sage-50', text: 'text-sage-700', border: 'border-sage-200' }} />)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('applies background color class', () => {
    render(<StatusBadge label="Error" colors={{ bg: 'bg-clay-50', text: 'text-clay-700', border: 'border-clay-200' }} />)
    const badge = screen.getByText('Error')
    expect(badge.className).toContain('bg-clay-50')
  })

  it('applies text color class', () => {
    render(<StatusBadge label="Warning" colors={{ bg: 'bg-oatmeal-50', text: 'text-oatmeal-700', border: 'border-oatmeal-200' }} />)
    const badge = screen.getByText('Warning')
    expect(badge.className).toContain('text-oatmeal-700')
  })

  it('applies border color class', () => {
    render(<StatusBadge label="Info" colors={{ bg: 'bg-sage-50', text: 'text-sage-600', border: 'border-sage-300' }} />)
    const badge = screen.getByText('Info')
    expect(badge.className).toContain('border-sage-300')
  })

  it('renders as an inline-flex span', () => {
    render(<StatusBadge label="Test" colors={{ bg: 'bg-sage-50', text: 'text-sage-700', border: 'border-sage-200' }} />)
    const badge = screen.getByText('Test')
    expect(badge.tagName).toBe('SPAN')
    expect(badge.className).toContain('inline-flex')
  })

  it('has rounded-full style', () => {
    render(<StatusBadge label="Badge" colors={{ bg: 'bg-sage-50', text: 'text-sage-700', border: 'border-sage-200' }} />)
    const badge = screen.getByText('Badge')
    expect(badge.className).toContain('rounded-full')
  })
})
