/**
 * Citation component tests
 *
 * Tests: known citation rendering, unknown code fallback,
 * tooltip display on hover, link rendering.
 */
import { Citation } from '@/components/shared/Citation'
import { render, screen, fireEvent } from '@/test-utils'

jest.mock('@/lib/citations', () => ({
  getCitation: (code: string) => {
    if (code === 'ISA 240') {
      return {
        code: 'ISA 240',
        fullName: 'The Auditor\'s Responsibilities Relating to Fraud',
        officialUrl: 'https://example.com/isa240',
        officialNote: 'IFAC eISA',
        freeUrl: 'https://example.com/isa240-free',
        freeNote: 'IAASB open',
      }
    }
    return null
  },
}))

describe('Citation', () => {
  it('renders code text for unknown citation', () => {
    render(<Citation code="UNKNOWN-999" />)
    expect(screen.getByText('UNKNOWN-999')).toBeInTheDocument()
  })

  it('renders known citation with dotted underline', () => {
    render(<Citation code="ISA 240" />)
    const codeEl = screen.getByText('ISA 240')
    expect(codeEl).toBeInTheDocument()
    expect(codeEl.className).toContain('border-dotted')
  })

  it('shows tooltip on hover', () => {
    render(<Citation code="ISA 240" />)
    const trigger = screen.getByRole('button')
    fireEvent.mouseEnter(trigger)
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    expect(screen.getByText(/Auditor's Responsibilities/)).toBeInTheDocument()
  })

  it('shows official link in tooltip', () => {
    render(<Citation code="ISA 240" />)
    fireEvent.mouseEnter(screen.getByRole('button'))
    expect(screen.getByText('Official: IFAC eISA')).toBeInTheDocument()
  })

  it('shows free link in tooltip when available', () => {
    render(<Citation code="ISA 240" />)
    fireEvent.mouseEnter(screen.getByRole('button'))
    expect(screen.getByText('Also: IAASB open')).toBeInTheDocument()
  })

  it('hides tooltip on mouse leave', () => {
    render(<Citation code="ISA 240" />)
    const trigger = screen.getByRole('button')
    fireEvent.mouseEnter(trigger)
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    fireEvent.mouseLeave(trigger)
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })
})
