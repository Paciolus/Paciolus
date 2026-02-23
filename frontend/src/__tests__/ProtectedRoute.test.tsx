/**
 * Sprint 277: ProtectedRoute component tests
 *
 * Tests the auth guard wrapper that redirects unauthenticated users to /login.
 * Covers: authenticated render, redirect, loading spinner, sessionStorage path save.
 */
import React from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { render, screen } from '@/test-utils'

const mockPush = jest.fn()
const mockUseAuth = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => '/tools/trial-balance',
}))


describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    sessionStorage.clear()
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
    })
  })

  it('renders children when authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
    })

    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Secret Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    expect(screen.getByText('Secret Content')).toBeInTheDocument()
  })

  it('redirects to /login when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
    })

    render(
      <ProtectedRoute>
        <div>Secret Content</div>
      </ProtectedRoute>
    )

    expect(mockPush).toHaveBeenCalledWith('/login')
  })

  it('shows loading spinner when auth is loading', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
    })

    render(
      <ProtectedRoute>
        <div>Secret Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByText('Loading your vault...')).toBeInTheDocument()
    expect(screen.queryByText('Secret Content')).not.toBeInTheDocument()
  })

  it('stores current path in sessionStorage before redirect', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
    })

    render(
      <ProtectedRoute>
        <div>Secret Content</div>
      </ProtectedRoute>
    )

    expect(sessionStorage.getItem('paciolus_redirect')).toBe('/tools/trial-balance')
  })

  it('does not render children when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
    })

    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Secret Content</div>
      </ProtectedRoute>
    )

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })
})
