/**
 * MegaDropdown component tests
 *
 * Tests: rendering when open/closed, tool columns,
 * account section, menu role.
 */
import { MegaDropdown } from '@/components/shared/UnifiedToolbar/MegaDropdown'
import { TOOL_COLUMNS } from '@/components/shared/UnifiedToolbar/toolbarConfig'
import { TOOL_LEDGER } from '@/content/tool-ledger'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ ref, initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, style, children, ...rest }: any) =>
      <div {...rest} style={style} ref={ref}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, ...rest }: any) => <a href={href} {...rest}>{children}</a>,
}))

jest.mock('next/navigation', () => ({
  usePathname: () => '/',
}))

jest.mock('@/lib/motion', () => ({
  fadeScale: { hidden: {}, visible: {}, exit: {} },
}))

describe('MegaDropdown', () => {
  it('renders nothing when closed', () => {
    const { container } = render(<MegaDropdown isOpen={false} onClose={jest.fn()} />)
    expect(container.textContent).toBe('')
  })

  it('renders menu when open', () => {
    render(<MegaDropdown isOpen={true} onClose={jest.fn()} />)
    expect(screen.getByRole('menu')).toBeInTheDocument()
  })

  it('renders Account column heading', () => {
    render(<MegaDropdown isOpen={true} onClose={jest.fn()} />)
    expect(screen.getByText('Account')).toBeInTheDocument()
  })

  it('renders tool links as menuitems', () => {
    render(<MegaDropdown isOpen={true} onClose={jest.fn()} />)
    const menuItems = screen.getAllByRole('menuitem')
    expect(menuItems.length).toBeGreaterThan(0)
  })

  it('offers every tool in the ledger', () => {
    // The ledger is tied to backend/tools_registry.py by
    // backend/tests/test_catalog_consistency.py, so this closes the chain
    // registry -> ledger -> navigation. Six tools (Sprint 689b-g) were missing
    // from the toolbar for six months while every count check passed.
    const navHrefs = new Set(TOOL_COLUMNS.flatMap(col => col.items.map(i => i.href)))
    const missing = TOOL_LEDGER.filter(entry => !navHrefs.has(entry.href)).map(e => e.name)
    expect(missing).toEqual([])
  })

  it('does not offer a tool that is not in the ledger', () => {
    // Non-ledger destinations are allowed but must be named, so a typo in an href
    // cannot masquerade as an intentional extra.
    const ledgerHrefs = new Set(TOOL_LEDGER.map(e => e.href))
    const allowedExtras = new Set(['/flux', '/recon'])
    const unexpected = TOOL_COLUMNS.flatMap(col => col.items.map(i => i.href)).filter(
      href => !ledgerHrefs.has(href) && !allowedExtras.has(href)
    )
    expect(unexpected).toEqual([])
  })

  it('lists each tool exactly once across all columns', () => {
    const hrefs = TOOL_COLUMNS.flatMap(col => col.items.map(i => i.href))
    expect(hrefs.length).toBe(new Set(hrefs).size)
  })

  it('uses registry slugs as tool keys', () => {
    // The toolKey comment promises these match backend entitlement names. Two did
    // not ('journal_entry', 'fixed_assets') until Sprint 788.
    const ledgerIds = new Set(TOOL_LEDGER.map(e => e.id))
    const ledgerHrefs = new Map(TOOL_LEDGER.map(e => [e.href, e.id]))
    const mismatched = TOOL_COLUMNS.flatMap(col => col.items)
      .filter(item => ledgerHrefs.has(item.href))
      .filter(item => item.toolKey !== ledgerHrefs.get(item.href))
      .map(item => `${item.label}: ${item.toolKey} != ${ledgerHrefs.get(item.href)}`)
    expect(ledgerIds.size).toBeGreaterThan(0)
    expect(mismatched).toEqual([])
  })

  it('renders with aria-label for accessibility', () => {
    render(<MegaDropdown isOpen={true} onClose={jest.fn()} />)
    expect(screen.getByRole('menu')).toHaveAttribute('aria-label', 'Tools and navigation')
  })
})
