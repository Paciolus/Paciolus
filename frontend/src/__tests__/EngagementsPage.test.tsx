/**
 * Engagements page tests — Sprint 580
 *
 * Engagements page now redirects to /portfolio (merged UX).
 * Tests verify the redirect behavior.
 */
import EngagementsPage from '@/app/(workspace)/engagements/page'
import { render, screen } from '@/test-utils'

const mockReplace = jest.fn()

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: mockReplace }),
}))

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...rest }: any) => <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

describe('EngagementsPage (redirect)', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('redirects to /portfolio', () => {
    render(<EngagementsPage />)
    expect(mockReplace).toHaveBeenCalledWith('/portfolio')
  })

  it('shows redirect loading state', () => {
    render(<EngagementsPage />)
    expect(screen.getByText('Redirecting to Portfolio...')).toBeInTheDocument()
  })
})
