/**
 * Sprint 705: StandardsSpecimen — replaces the pill strip on the homepage.
 *
 * Pins:
 *   - Every standard from the data source renders.
 *   - Governing-body headings group the list (IAASB / PCAOB / FASB / IASB).
 *   - Each row is a link that routes to the first-cited tool's catalog page.
 *   - Oldstyle-figures inline style on the standard code.
 *   - Mobile-fallback pill strip renders when the specimen layout is hidden.
 */
import { StandardsSpecimen } from '@/components/marketing/StandardsSpecimen'
import { STANDARDS_SPECIMEN, BODY_ORDER, BODY_LABELS } from '@/content/standards-specimen'
import { render, screen } from '@/test-utils'

describe('StandardsSpecimen', () => {
  it('renders every standard from the data source', () => {
    render(<StandardsSpecimen />)
    for (const entry of STANDARDS_SPECIMEN) {
      // Use getAllByText because the mobile fallback renders the same codes.
      expect(screen.getAllByText(entry.code).length).toBeGreaterThan(0)
    }
  })

  it('renders a heading per governing body present in the data', () => {
    render(<StandardsSpecimen />)
    const bodiesPresent = new Set(STANDARDS_SPECIMEN.map(e => e.body))
    for (const body of BODY_ORDER) {
      if (!bodiesPresent.has(body)) continue
      expect(screen.getByText(BODY_LABELS[body])).toBeInTheDocument()
    }
  })

  it('each standard row is a link to its first-cited tool', () => {
    render(<StandardsSpecimen />)
    const revenue = STANDARDS_SPECIMEN.find(e => e.code === 'ISA 240')!
    // ISA 240 lists journal_entry_testing first → /tools/journal-entry-testing
    const codeEl = screen.getAllByText('ISA 240')[0]
    const link = codeEl?.closest('a')
    expect(link).not.toBeNull()
    expect(link!.getAttribute('href')).toBe('/tools/journal-entry-testing')
    expect(revenue.tools[0]).toBe('journal_entry_testing')
  })

  it('applies oldstyle-nums inline style to standard codes', () => {
    render(<StandardsSpecimen />)
    const codeEl = screen.getAllByText('ISA 530')[0]
    expect(codeEl!.getAttribute('style')).toContain('oldstyle-nums')
  })

  it('renders the mobile fallback pill strip', () => {
    const { container } = render(<StandardsSpecimen />)
    // The mobile fallback is the <div className="md:hidden mt-10">.
    const fallback = container.querySelector('.md\\:hidden')
    expect(fallback).not.toBeNull()
    // The fallback renders every code as a link.
    const fallbackLinks = fallback!.querySelectorAll('a')
    expect(fallbackLinks.length).toBe(STANDARDS_SPECIMEN.length)
  })

  it('shows the "n standards · m tools cite them" summary', () => {
    render(<StandardsSpecimen />)
    const totalTools = new Set(STANDARDS_SPECIMEN.flatMap(e => e.tools)).size
    expect(
      screen.getByText(new RegExp(`${STANDARDS_SPECIMEN.length} standards.*${totalTools} tools`)),
    ).toBeInTheDocument()
  })
})
