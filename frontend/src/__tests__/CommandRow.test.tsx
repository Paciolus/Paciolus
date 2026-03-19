/**
 * CommandRow component tests
 *
 * Tests: rendering label, detail, guard badges, selection state,
 * shortcut hints, interaction callbacks.
 */
import { CommandRow } from '@/components/shared/CommandPalette/CommandRow'
import { render, screen, fireEvent } from '@/test-utils'

const makeCommand = (overrides: Record<string, unknown> = {}) => ({
  id: 'cmd-1',
  label: 'Trial Balance',
  detail: 'Run TB diagnostics',
  category: 'tool' as const,
  action: jest.fn(),
  shortcutHint: undefined as string | undefined,
  ...overrides,
})

describe('CommandRow', () => {
  const onSelect = jest.fn()
  const onHover = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders command label', () => {
    render(
      <CommandRow command={makeCommand()} guardStatus="allowed" isSelected={false} onSelect={onSelect} onHover={onHover} />
    )
    expect(screen.getByText('Trial Balance')).toBeInTheDocument()
  })

  it('renders detail text', () => {
    render(
      <CommandRow command={makeCommand()} guardStatus="allowed" isSelected={false} onSelect={onSelect} onHover={onHover} />
    )
    expect(screen.getByText('Run TB diagnostics')).toBeInTheDocument()
  })

  it('shows Upgrade badge when tier_blocked', () => {
    render(
      <CommandRow command={makeCommand()} guardStatus="tier_blocked" isSelected={false} onSelect={onSelect} onHover={onHover} />
    )
    expect(screen.getByText('Upgrade')).toBeInTheDocument()
  })

  it('shows Verify badge when unverified', () => {
    render(
      <CommandRow command={makeCommand()} guardStatus="unverified" isSelected={false} onSelect={onSelect} onHover={onHover} />
    )
    expect(screen.getByText('Verify')).toBeInTheDocument()
  })

  it('shows Enter hint when selected', () => {
    render(
      <CommandRow command={makeCommand()} guardStatus="allowed" isSelected={true} onSelect={onSelect} onHover={onHover} />
    )
    expect(screen.getByText('Enter')).toBeInTheDocument()
  })

  it('shows shortcut hint when allowed and not selected', () => {
    render(
      <CommandRow command={makeCommand({ shortcutHint: 'Ctrl+T' })} guardStatus="allowed" isSelected={false} onSelect={onSelect} onHover={onHover} />
    )
    expect(screen.getByText('Ctrl+T')).toBeInTheDocument()
  })

  it('calls onSelect when clicked', () => {
    render(
      <CommandRow command={makeCommand()} guardStatus="allowed" isSelected={false} onSelect={onSelect} onHover={onHover} />
    )
    fireEvent.click(screen.getByRole('option'))
    expect(onSelect).toHaveBeenCalled()
  })

  it('calls onHover on mouse enter', () => {
    render(
      <CommandRow command={makeCommand()} guardStatus="allowed" isSelected={false} onSelect={onSelect} onHover={onHover} />
    )
    fireEvent.mouseEnter(screen.getByRole('option'))
    expect(onHover).toHaveBeenCalled()
  })
})
