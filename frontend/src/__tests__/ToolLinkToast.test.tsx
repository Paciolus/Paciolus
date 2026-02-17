/**
 * ToolLinkToast component tests — Sprint 277
 *
 * Tests: message rendering, null message, dismiss button,
 * auto-dismiss after 4000ms, dismiss callback.
 */
import { render, screen, fireEvent, act } from '@/test-utils'

jest.mock('framer-motion', () => {
  const R = require('react')
  return {
    motion: new Proxy(
      {},
      {
        get: (_: unknown, tag: string) =>
          R.forwardRef(
            (
              {
                initial,
                animate,
                exit,
                transition,
                variants,
                whileHover,
                whileInView,
                whileTap,
                viewport,
                layout,
                layoutId,
                ...rest
              }: any,
              ref: any,
            ) => R.createElement(tag, { ...rest, ref }),
          ),
      },
    ),
    AnimatePresence: ({ children }: any) => children,
  }
})

import { ToolLinkToast } from '@/components/engagement/ToolLinkToast'

describe('ToolLinkToast', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('renders message when provided', () => {
    render(
      <ToolLinkToast message="Results linked to Workspace" onDismiss={jest.fn()} />,
    )
    expect(screen.getByText('Results linked to Workspace')).toBeInTheDocument()
  })

  it('does not render when message is null', () => {
    const { container } = render(
      <ToolLinkToast message={null} onDismiss={jest.fn()} />,
    )
    expect(container.querySelector('[data-theme="dark"]')).not.toBeInTheDocument()
  })

  it('calls onDismiss when dismiss button is clicked', () => {
    const onDismiss = jest.fn()
    render(
      <ToolLinkToast message="Results linked" onDismiss={onDismiss} />,
    )
    const dismissButton = screen.getByRole('button')
    fireEvent.click(dismissButton)
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('auto-dismisses after 4000ms', () => {
    const onDismiss = jest.fn()
    render(
      <ToolLinkToast message="Results linked" onDismiss={onDismiss} />,
    )
    expect(onDismiss).not.toHaveBeenCalled()

    act(() => {
      jest.advanceTimersByTime(4000)
    })

    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('renders dismiss (X) button', () => {
    render(
      <ToolLinkToast message="Test message" onDismiss={jest.fn()} />,
    )
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
    // The button contains an SVG with an X path
    const svg = button.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })
})
