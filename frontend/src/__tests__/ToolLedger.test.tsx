/**
 * Sprint 706: ToolLedger — 12-row bound-ledger grid replacing the
 * one-card slideshow on the homepage.
 */
import { ToolLedger } from '@/components/marketing/ToolLedger'
import { CANONICAL_TOOL_COUNT, TOOL_LEDGER } from '@/content/tool-ledger'
import { render, screen, fireEvent } from '@/test-utils'

describe('ToolLedger', () => {
  it('renders exactly CANONICAL_TOOL_COUNT rows', () => {
    render(<ToolLedger />)
    const rows = screen.getAllByRole('listitem')
    expect(rows).toHaveLength(CANONICAL_TOOL_COUNT)
  })

  it('shows every tool name', () => {
    render(<ToolLedger />)
    for (const entry of TOOL_LEDGER) {
      expect(screen.getByText(entry.name)).toBeInTheDocument()
    }
  })

  it('collapses all panels by default (aria-expanded=false)', () => {
    render(<ToolLedger />)
    const buttons = screen.getAllByRole('button', { expanded: false })
    // Every ledger row button + any non-ledger buttons; at minimum we
    // should have the 12 row buttons collapsed.
    expect(buttons.length).toBeGreaterThanOrEqual(CANONICAL_TOOL_COUNT)
  })

  it('expands a row on click and shows its summary', () => {
    render(<ToolLedger />)
    const firstEntry = TOOL_LEDGER[0]!
    const button = screen.getByRole('button', { name: new RegExp(firstEntry.name) })
    fireEvent.click(button)
    expect(button).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText(firstEntry.summary)).toBeInTheDocument()
  })

  it('only one panel expanded at a time', () => {
    render(<ToolLedger />)
    const first = screen.getByRole('button', { name: new RegExp(TOOL_LEDGER[0]!.name) })
    const second = screen.getByRole('button', { name: new RegExp(TOOL_LEDGER[1]!.name) })
    fireEvent.click(first)
    expect(first).toHaveAttribute('aria-expanded', 'true')
    fireEvent.click(second)
    expect(second).toHaveAttribute('aria-expanded', 'true')
    expect(first).toHaveAttribute('aria-expanded', 'false')
  })

  it('renders roman numerals for the desktop row label', () => {
    render(<ToolLedger />)
    // The first tool renders both "1." (mobile) and "I." (desktop).
    // We can find the "I." span specifically.
    const romanFirst = screen.getAllByText((_content, element) => {
      return element?.tagName === 'SPAN' && element.textContent === 'I.'
    })
    expect(romanFirst.length).toBeGreaterThan(0)
  })

  it('keyboard activation via Enter expands the panel', () => {
    render(<ToolLedger />)
    const button = screen.getByRole('button', { name: new RegExp(TOOL_LEDGER[2]!.name) })
    fireEvent.keyDown(button, { key: 'Enter' })
    expect(button).toHaveAttribute('aria-expanded', 'true')
  })

  it('links to the tool catalog page from the expanded panel', () => {
    render(<ToolLedger />)
    const entry = TOOL_LEDGER[2]!  // JE Testing
    const button = screen.getByRole('button', { name: new RegExp(entry.name) })
    fireEvent.click(button)
    const link = screen.getByRole('link', { name: /Open tool/i })
    expect(link).toHaveAttribute('href', entry.href)
  })

  it('tests badge shows the test count when present, em-dash otherwise', () => {
    render(<ToolLedger />)
    // JE Testing is number 3 and has testCount=19.
    expect(screen.getByText('19')).toBeInTheDocument()
    // TB Diagnostics is number 1 and has testCount=null. The em-dash
    // appears once per tool without a test count; there are 5 such tools
    // in the current data, so we just assert 'at least one exists.'
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })

  it('summary footer shows the canonical count', () => {
    render(<ToolLedger />)
    expect(
      screen.getByText(new RegExp(`${CANONICAL_TOOL_COUNT} tools.*every paid plan`, 'i')),
    ).toBeInTheDocument()
  })
})
