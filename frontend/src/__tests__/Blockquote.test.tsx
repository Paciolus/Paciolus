/**
 * Sprint 703: Blockquote editorial pull-quote component.
 */
import { Blockquote } from '@/components/marketing/Blockquote'
import { render, screen } from '@/test-utils'

describe('Blockquote', () => {
  it('renders children inside a <blockquote>', () => {
    render(<Blockquote>The moment when you need a defensible answer.</Blockquote>)
    const bq = screen.getByText(/defensible answer/)
    expect(bq).toBeInTheDocument()
    expect(bq.closest('blockquote')).not.toBeNull()
  })

  it('wraps the quote in a <figure> for semantic pairing with the figcaption', () => {
    render(
      <Blockquote attribution="Paciolus — About page">
        Test quote.
      </Blockquote>,
    )
    const fig = screen.getByText('Test quote.').closest('figure')
    expect(fig).not.toBeNull()
  })

  it('renders the attribution in a <figcaption> when provided', () => {
    render(
      <Blockquote attribution="Paciolus — About page">
        Test quote.
      </Blockquote>,
    )
    const cap = screen.getByText('Paciolus — About page')
    expect(cap.tagName.toLowerCase()).toBe('figcaption')
  })

  it('omits the <figcaption> when no attribution is provided', () => {
    const { container } = render(<Blockquote>Test quote.</Blockquote>)
    expect(container.querySelector('figcaption')).toBeNull()
  })

  it('respects the size override', () => {
    const { rerender } = render(<Blockquote>quote</Blockquote>)
    const pXl = screen.getByText('quote')
    expect(pXl.className).toMatch(/text-2xl/)

    rerender(<Blockquote size="lg">quote</Blockquote>)
    const pLg = screen.getByText('quote')
    expect(pLg.className).toMatch(/text-xl/)
  })

  it('sets oldstyle-nums on the quote paragraph', () => {
    render(<Blockquote>140 tests since 1992.</Blockquote>)
    const p = screen.getByText('140 tests since 1992.')
    // font-variant-numeric is set inline — jsdom normalises it, so we
    // check the inline style rather than the computed style to be robust.
    expect(p.getAttribute('style')).toContain('oldstyle-nums')
  })
})
