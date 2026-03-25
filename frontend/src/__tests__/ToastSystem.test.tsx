/**
 * Toast notification system tests — Sprint 582
 *
 * Tests: rendering, auto-dismiss, manual dismiss, toast types, aria attributes.
 */
import { act, fireEvent } from '@testing-library/react'
import { ToastProvider, useToast } from '@/contexts/ToastContext'
import { ToastContainer } from '@/components/shared/ToastContainer'
import { render, screen, waitFor } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileTap, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children, mode }: any) => <>{children}</>,
}))

function TestTrigger() {
  const { success, error, info } = useToast()
  return (
    <div>
      <button onClick={() => success('Upload complete', '1,250 rows analyzed')}>
        Success
      </button>
      <button onClick={() => error('Upload failed', 'Could not parse file')}>
        Error
      </button>
      <button onClick={() => info('Processing', 'Analysis in progress')}>
        Info
      </button>
    </div>
  )
}

function renderWithToast() {
  return render(
    <ToastProvider>
      <TestTrigger />
      <ToastContainer />
    </ToastProvider>
  )
}

describe('Toast Notification System', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('renders success toast with title and description', () => {
    renderWithToast()
    fireEvent.click(screen.getByText('Success'))
    expect(screen.getByText('Upload complete')).toBeInTheDocument()
    expect(screen.getByText('1,250 rows analyzed')).toBeInTheDocument()
  })

  it('renders error toast with title and description', () => {
    renderWithToast()
    fireEvent.click(screen.getByText('Error'))
    expect(screen.getByText('Upload failed')).toBeInTheDocument()
    expect(screen.getByText('Could not parse file')).toBeInTheDocument()
  })

  it('renders info toast with title and description', () => {
    renderWithToast()
    fireEvent.click(screen.getByText('Info'))
    expect(screen.getByText('Processing')).toBeInTheDocument()
    expect(screen.getByText('Analysis in progress')).toBeInTheDocument()
  })

  it('auto-dismisses success toast after 4 seconds', () => {
    renderWithToast()
    fireEvent.click(screen.getByText('Success'))
    expect(screen.getByText('Upload complete')).toBeInTheDocument()

    act(() => { jest.advanceTimersByTime(4100) })
    expect(screen.queryByText('Upload complete')).not.toBeInTheDocument()
  })

  it('auto-dismisses error toast after 6 seconds', () => {
    renderWithToast()
    fireEvent.click(screen.getByText('Error'))
    expect(screen.getByText('Upload failed')).toBeInTheDocument()

    act(() => { jest.advanceTimersByTime(4100) })
    expect(screen.getByText('Upload failed')).toBeInTheDocument()

    act(() => { jest.advanceTimersByTime(2100) })
    expect(screen.queryByText('Upload failed')).not.toBeInTheDocument()
  })

  it('can manually dismiss toast via close button', () => {
    renderWithToast()
    fireEvent.click(screen.getByText('Success'))
    expect(screen.getByText('Upload complete')).toBeInTheDocument()

    fireEvent.click(screen.getByLabelText('Dismiss notification'))
    expect(screen.queryByText('Upload complete')).not.toBeInTheDocument()
  })

  it('renders multiple toasts simultaneously', () => {
    renderWithToast()
    fireEvent.click(screen.getByText('Success'))
    fireEvent.click(screen.getByText('Error'))
    fireEvent.click(screen.getByText('Info'))

    expect(screen.getByText('Upload complete')).toBeInTheDocument()
    expect(screen.getByText('Upload failed')).toBeInTheDocument()
    expect(screen.getByText('Processing')).toBeInTheDocument()
  })

  it('has correct aria-live region for accessibility', () => {
    renderWithToast()
    const container = screen.getByLabelText('Notifications')
    expect(container).toHaveAttribute('aria-live', 'polite')
  })

  it('toast items have role="status"', () => {
    renderWithToast()
    fireEvent.click(screen.getByText('Success'))
    const toastEl = screen.getByText('Upload complete').closest('[role="status"]')
    expect(toastEl).toBeInTheDocument()
  })
})
