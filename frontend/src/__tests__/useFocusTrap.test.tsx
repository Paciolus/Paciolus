/**
 * useFocusTrap hook tests
 *
 * Sprint 415: Keyboard accessibility regression tests.
 * Covers: Tab trapping, Shift+Tab wrapping, Escape close, focus restore, auto-focus.
 */
import { renderHook, act } from '@testing-library/react'
import { useFocusTrap } from '@/hooks/useFocusTrap'

function createModalContainer() {
  const container = document.createElement('div')
  const btn1 = document.createElement('button')
  btn1.textContent = 'First'
  const input = document.createElement('input')
  const btn2 = document.createElement('button')
  btn2.textContent = 'Last'
  container.appendChild(btn1)
  container.appendChild(input)
  container.appendChild(btn2)
  document.body.appendChild(container)
  return { container, btn1, input, btn2 }
}

describe('useFocusTrap', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
    document.body.innerHTML = ''
  })

  it('returns a ref to attach to the container', () => {
    const { result } = renderHook(() => useFocusTrap(false))
    expect(result.current).toHaveProperty('current')
  })

  it('auto-focuses first focusable element when opened', () => {
    const { container, btn1 } = createModalContainer()
    const { result } = renderHook(() => useFocusTrap(true))

    // Attach the ref to our container
    Object.defineProperty(result.current, 'current', {
      value: container,
      writable: true,
    })

    // Re-render to trigger the effect with the ref attached
    const { rerender } = renderHook(
      ({ isOpen }) => {
        const ref = useFocusTrap(isOpen)
        Object.defineProperty(ref, 'current', {
          value: container,
          writable: true,
        })
        return ref
      },
      { initialProps: { isOpen: false } }
    )

    rerender({ isOpen: true })

    act(() => {
      jest.advanceTimersByTime(100)
    })

    expect(document.activeElement).toBe(btn1)
  })

  it('calls onClose when Escape is pressed', () => {
    const onClose = jest.fn()
    const { container } = createModalContainer()

    renderHook(
      ({ isOpen }) => {
        const ref = useFocusTrap(isOpen, onClose)
        Object.defineProperty(ref, 'current', {
          value: container,
          writable: true,
        })
        return ref
      },
      { initialProps: { isOpen: true } }
    )

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    })

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('does not call onClose for non-Escape keys', () => {
    const onClose = jest.fn()
    const { container } = createModalContainer()

    renderHook(
      ({ isOpen }) => {
        const ref = useFocusTrap(isOpen, onClose)
        Object.defineProperty(ref, 'current', {
          value: container,
          writable: true,
        })
        return ref
      },
      { initialProps: { isOpen: true } }
    )

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }))
    })

    expect(onClose).not.toHaveBeenCalled()
  })

  it('wraps Tab from last element to first', () => {
    const { container, btn1, btn2 } = createModalContainer()

    renderHook(
      ({ isOpen }) => {
        const ref = useFocusTrap(isOpen)
        Object.defineProperty(ref, 'current', {
          value: container,
          writable: true,
        })
        return ref
      },
      { initialProps: { isOpen: true } }
    )

    // Focus the last button
    act(() => {
      btn2.focus()
    })
    expect(document.activeElement).toBe(btn2)

    // Tab forward from last → should wrap to first
    const event = new KeyboardEvent('keydown', {
      key: 'Tab',
      bubbles: true,
      cancelable: true,
    })
    act(() => {
      document.dispatchEvent(event)
    })

    expect(document.activeElement).toBe(btn1)
  })

  it('wraps Shift+Tab from first element to last', () => {
    const { container, btn1, btn2 } = createModalContainer()

    renderHook(
      ({ isOpen }) => {
        const ref = useFocusTrap(isOpen)
        Object.defineProperty(ref, 'current', {
          value: container,
          writable: true,
        })
        return ref
      },
      { initialProps: { isOpen: true } }
    )

    // Focus the first button
    act(() => {
      btn1.focus()
    })
    expect(document.activeElement).toBe(btn1)

    // Shift+Tab from first → should wrap to last
    const event = new KeyboardEvent('keydown', {
      key: 'Tab',
      shiftKey: true,
      bubbles: true,
      cancelable: true,
    })
    act(() => {
      document.dispatchEvent(event)
    })

    expect(document.activeElement).toBe(btn2)
  })

  it('restores focus to previously focused element on close', () => {
    const { container } = createModalContainer()

    // Create and focus a trigger button outside the modal
    const trigger = document.createElement('button')
    trigger.textContent = 'Open Modal'
    document.body.appendChild(trigger)
    trigger.focus()
    expect(document.activeElement).toBe(trigger)

    const { rerender } = renderHook(
      ({ isOpen }) => {
        const ref = useFocusTrap(isOpen)
        Object.defineProperty(ref, 'current', {
          value: container,
          writable: true,
        })
        return ref
      },
      { initialProps: { isOpen: true } }
    )

    act(() => {
      jest.advanceTimersByTime(100)
    })

    // Close the modal
    rerender({ isOpen: false })

    // Focus should be restored to the trigger
    expect(document.activeElement).toBe(trigger)
  })

  it('does not add keydown listener when closed', () => {
    const onClose = jest.fn()
    const { container } = createModalContainer()

    renderHook(
      ({ isOpen }) => {
        const ref = useFocusTrap(isOpen, onClose)
        Object.defineProperty(ref, 'current', {
          value: container,
          writable: true,
        })
        return ref
      },
      { initialProps: { isOpen: false } }
    )

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    })

    expect(onClose).not.toHaveBeenCalled()
  })
})
