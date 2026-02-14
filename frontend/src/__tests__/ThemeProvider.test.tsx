/**
 * Sprint 232: ThemeProvider tests — DARK_ROUTES logic
 */
import { render } from '@/test-utils'

jest.mock('next/navigation', () => ({
  usePathname: jest.fn(() => '/'),
}))

import { ThemeProvider } from '@/components/ThemeProvider'
import { usePathname } from 'next/navigation'

const mockUsePathname = usePathname as jest.Mock

describe('ThemeProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    document.documentElement.removeAttribute('data-theme')
  })

  it('sets dark theme for homepage', () => {
    mockUsePathname.mockReturnValue('/')
    render(<ThemeProvider><div>child</div></ThemeProvider>)
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('sets dark theme for /login', () => {
    mockUsePathname.mockReturnValue('/login')
    render(<ThemeProvider><div>child</div></ThemeProvider>)
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('sets dark theme for /register', () => {
    mockUsePathname.mockReturnValue('/register')
    render(<ThemeProvider><div>child</div></ThemeProvider>)
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('sets dark theme for /privacy', () => {
    mockUsePathname.mockReturnValue('/privacy')
    render(<ThemeProvider><div>child</div></ThemeProvider>)
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('sets light theme for /tools/trial-balance', () => {
    mockUsePathname.mockReturnValue('/tools/trial-balance')
    render(<ThemeProvider><div>child</div></ThemeProvider>)
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('sets light theme for /engagements', () => {
    mockUsePathname.mockReturnValue('/engagements')
    render(<ThemeProvider><div>child</div></ThemeProvider>)
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('sets light theme for /settings', () => {
    mockUsePathname.mockReturnValue('/settings')
    render(<ThemeProvider><div>child</div></ThemeProvider>)
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('renders children', () => {
    mockUsePathname.mockReturnValue('/')
    const { getByText } = render(<ThemeProvider><div>test child</div></ThemeProvider>)
    expect(getByText('test child')).toBeInTheDocument()
  })
})
