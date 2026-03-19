/**
 * MegaDropdown component tests
 *
 * Tests: rendering when open/closed, tool columns,
 * account section, menu role.
 */
import { MegaDropdown } from '@/components/shared/UnifiedToolbar/MegaDropdown'
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

  it('renders with aria-label for accessibility', () => {
    render(<MegaDropdown isOpen={true} onClose={jest.fn()} />)
    expect(screen.getByRole('menu')).toHaveAttribute('aria-label', 'Tools and navigation')
  })
})
