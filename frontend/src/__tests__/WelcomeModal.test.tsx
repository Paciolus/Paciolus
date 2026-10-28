/**
 * WelcomeModal tests — Sprint 583
 *
 * Tests: first-run display, step navigation, skip, completion persistence,
 * and (Sprint 856) Escape-to-close, initial focus, Tab focus trap.
 */
import { act, fireEvent } from '@testing-library/react'
import { WelcomeModal } from '@/components/shared/WelcomeModal'
import { render, screen, waitFor } from '@/test-utils'

const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => '/dashboard',
}))

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileTap, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

describe('WelcomeModal', () => {
  beforeEach(() => {
    localStorage.clear()
    mockPush.mockClear()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('renders when forceShow is true', () => {
    render(<WelcomeModal forceShow />)
    expect(screen.getByText('Choose a Tool')).toBeInTheDocument()
    expect(screen.getByText('Welcome to Paciolus')).toBeInTheDocument()
  })

  it('shows step 1 of 3', () => {
    render(<WelcomeModal forceShow />)
    expect(screen.getByText('Step 1 of 3')).toBeInTheDocument()
  })

  it('navigates through all 3 steps', () => {
    render(<WelcomeModal forceShow />)

    // Step 1
    expect(screen.getByText('Choose a Tool')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Next'))

    // Step 2
    expect(screen.getByText('Run Diagnostic Tools')).toBeInTheDocument()
    expect(screen.getByText('Step 2 of 3')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Next'))

    // Step 3 — final step shows CTA instead of Next
    expect(screen.getByText('Export Audit-Ready Memos')).toBeInTheDocument()
    expect(screen.getByText('Step 3 of 3')).toBeInTheDocument()
    expect(screen.getByText('Get Started')).toBeInTheDocument()
  })

  it('clicking final CTA navigates to trial balance and sets localStorage', () => {
    render(<WelcomeModal forceShow />)
    fireEvent.click(screen.getByText('Next'))
    fireEvent.click(screen.getByText('Next'))
    fireEvent.click(screen.getByText('Get Started'))

    expect(mockPush).toHaveBeenCalledWith('/tools/trial-balance')
    expect(localStorage.getItem('paciolus_onboarding_complete')).toBe('true')
  })

  it('skip button closes modal and sets localStorage', () => {
    render(<WelcomeModal forceShow />)
    fireEvent.click(screen.getByText('Skip'))

    expect(screen.queryByText('Choose a Tool')).not.toBeInTheDocument()
    expect(localStorage.getItem('paciolus_onboarding_complete')).toBe('true')
  })

  it('does not show when onboarding is already complete', () => {
    localStorage.setItem('paciolus_onboarding_complete', 'true')
    render(<WelcomeModal />)

    jest.advanceTimersByTime(1000)
    expect(screen.queryByText('Choose a Tool')).not.toBeInTheDocument()
  })

  it('has accessible dialog attributes', () => {
    render(<WelcomeModal forceShow />)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(dialog).toHaveAttribute('aria-labelledby', 'welcome-title')
  })

  it('step 1 points at the tool picker, not the trial balance upload', () => {
    render(<WelcomeModal forceShow />)
    expect(screen.queryByText(/upload a trial balance/i)).not.toBeInTheDocument()
    expect(screen.getByText(/pick the tool that matches the file you have/i)).toBeInTheDocument()
  })

  it('Escape closes the modal and records completion', () => {
    render(<WelcomeModal forceShow />)
    act(() => { jest.advanceTimersByTime(100) })
    fireEvent.keyDown(document, { key: 'Escape' })

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(localStorage.getItem('paciolus_onboarding_complete')).toBe('true')
  })

  it('moves focus into the dialog on open', () => {
    render(<WelcomeModal forceShow />)
    act(() => { jest.advanceTimersByTime(100) })

    expect(screen.getByRole('dialog')).toContainElement(document.activeElement as HTMLElement)
    expect(screen.getByText('Skip')).toHaveFocus()
  })

  it('traps Tab and Shift+Tab inside the dialog', () => {
    render(<WelcomeModal forceShow />)
    act(() => { jest.advanceTimersByTime(100) })
    const skip = screen.getByText('Skip')
    const next = screen.getByText('Next')

    // Shift+Tab from the first control wraps to the last
    skip.focus()
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true })
    expect(next).toHaveFocus()

    // Tab from the last control wraps to the first
    fireEvent.keyDown(document, { key: 'Tab' })
    expect(skip).toHaveFocus()
  })
})
