/**
 * Sprint 704: EngravedStat monument-style stat block.
 */
import { EngravedStat } from '@/components/marketing/EngravedStat'
import { render, screen } from '@/test-utils'

describe('EngravedStat', () => {
  it('renders value, label, and optional kicker + sub', () => {
    render(
      <EngravedStat
        kicker="I."
        value="1,452"
        label="Automated Tests"
        sub="Across all 18 diagnostic tools"
      />,
    )
    expect(screen.getByText('I.')).toBeInTheDocument()
    expect(screen.getByText('1,452')).toBeInTheDocument()
    expect(screen.getByText('Automated Tests')).toBeInTheDocument()
    expect(screen.getByText('Across all 18 diagnostic tools')).toBeInTheDocument()
  })

  it('omits the kicker when not provided', () => {
    const { container } = render(
      <EngravedStat value="7" label="Audit Frameworks" />,
    )
    // Find the figure's first child — in the no-kicker branch it should
    // be the value <span>, not a kicker <span>.
    const fig = container.querySelector('figure')
    expect(fig).not.toBeNull()
    const firstChild = fig!.firstElementChild
    expect(firstChild!.textContent).toBe('7')
  })

  it('applies oldstyle-nums inline style to the value', () => {
    render(<EngravedStat value="1,452" label="Tests" />)
    const valueEl = screen.getByText('1,452')
    expect(valueEl.getAttribute('style')).toContain('oldstyle-nums')
  })

  it('honours the accent prop on the kicker colour class', () => {
    const { rerender } = render(<EngravedStat kicker="I." value="1" label="x" accent="sage" />)
    expect(screen.getByText('I.').className).toMatch(/text-sage-400/)
    rerender(<EngravedStat kicker="I." value="1" label="x" accent="brass" />)
    expect(screen.getByText('I.').className).toMatch(/text-brass-400/)
  })

  it('renders as a <figure> with a <figcaption>', () => {
    const { container } = render(<EngravedStat value="12" label="Tools" />)
    expect(container.querySelector('figure')).not.toBeNull()
    expect(container.querySelector('figcaption')).not.toBeNull()
  })
})
