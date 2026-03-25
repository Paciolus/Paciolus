/**
 * WelcomeModal tests — Sprint 583
 *
 * Tests: first-run display, step navigation, skip, completion persistence.
 */
import { fireEvent } from '@testing-library/react'
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
    expect(screen.getByText('Upload a Trial Balance')).toBeInTheDocument()
    expect(screen.getByText('Welcome to Paciolus')).toBeInTheDocument()
  })

  it('shows step 1 of 3', () => {
    render(<WelcomeModal forceShow />)
    expect(screen.getByText('Step 1 of 3')).toBeInTheDocument()
  })

  it('navigates through all 3 steps', () => {
    render(<WelcomeModal forceShow />)

    // Step 1
    expect(screen.getByText('Upload a Trial Balance')).toBeInTheDocument()
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

    expect(screen.queryByText('Upload a Trial Balance')).not.toBeInTheDocument()
    expect(localStorage.getItem('paciolus_onboarding_complete')).toBe('true')
  })

  it('does not show when onboarding is already complete', () => {
    localStorage.setItem('paciolus_onboarding_complete', 'true')
    render(<WelcomeModal />)

    jest.advanceTimersByTime(1000)
    expect(screen.queryByText('Upload a Trial Balance')).not.toBeInTheDocument()
  })

  it('has accessible dialog attributes', () => {
    render(<WelcomeModal forceShow />)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(dialog).toHaveAttribute('aria-labelledby', 'welcome-title')
  })
})
