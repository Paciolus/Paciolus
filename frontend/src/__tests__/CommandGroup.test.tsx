/**
 * CommandGroup component tests
 *
 * Tests: rendering group label, items, empty state.
 */
import { CommandGroup } from '@/components/shared/CommandPalette/CommandGroup'
import { render, screen } from '@/test-utils'

jest.mock('@/components/shared/CommandPalette/CommandRow', () => ({
  CommandRow: ({ command }: any) => <div data-testid={`row-${command.id}`}>{command.label}</div>,
}))

const makeItem = (id: string, label: string) => ({
  command: {
    id,
    label,
    category: 'tool' as const,
    action: jest.fn(),
  },
  score: 100,
  guardStatus: 'allowed' as const,
})

describe('CommandGroup', () => {
  it('renders group label', () => {
    render(
      <CommandGroup
        category="tool"
        label="Tools"
        items={[makeItem('1', 'Trial Balance')]}
        selectedIndex={-1}
        flatOffset={0}
        onSelect={jest.fn()}
        onHover={jest.fn()}
      />
    )
    expect(screen.getByText('Tools')).toBeInTheDocument()
  })

  it('renders items', () => {
    render(
      <CommandGroup
        category="tool"
        label="Tools"
        items={[makeItem('1', 'Trial Balance'), makeItem('2', 'JE Testing')]}
        selectedIndex={-1}
        flatOffset={0}
        onSelect={jest.fn()}
        onHover={jest.fn()}
      />
    )
    expect(screen.getByText('Trial Balance')).toBeInTheDocument()
    expect(screen.getByText('JE Testing')).toBeInTheDocument()
  })

  it('renders nothing when items array is empty', () => {
    const { container } = render(
      <CommandGroup
        category="tool"
        label="Tools"
        items={[]}
        selectedIndex={-1}
        flatOffset={0}
        onSelect={jest.fn()}
        onHover={jest.fn()}
      />
    )
    expect(container.firstChild).toBeNull()
  })
})
