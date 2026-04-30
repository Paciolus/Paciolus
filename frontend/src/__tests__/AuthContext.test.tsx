/**
 * Sprint 234: AuthContext tests — provider rendering, useAuth hook contract
 */
import { ReactNode } from 'react'
import { renderHook, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({ push: jest.fn(), replace: jest.fn() })),
}))

// Mock utils — apiPost/apiGet/apiPut used in auth operations
jest.mock('@/utils', () => ({
  apiPost: jest.fn().mockResolvedValue({ ok: false, error: 'Not mocked' }),
  apiGet: jest.fn().mockResolvedValue({ ok: false, error: 'Not mocked' }),
  apiPut: jest.fn().mockResolvedValue({ ok: false, error: 'Not mocked' }),
  isAuthError: jest.fn(() => false),
  setTokenRefreshCallback: jest.fn(),
  fetchCsrfToken: jest.fn().mockResolvedValue(null),
  setCsrfToken: jest.fn(),
  getCsrfToken: jest.fn(() => null),
}))

// Must import AFTER mocks

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>
}

describe('useAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    sessionStorage.clear()
    localStorage.clear()
  })

  it('throws when used outside AuthProvider', () => {
    // Suppress console.error for expected throw
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => {
      renderHook(() => useAuth())
    }).toThrow('useAuthSession must be used within an AuthSessionProvider')

    spy.mockRestore()
  })

  it('provides initial unauthenticated state', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    // Wait for initialization
    await new Promise(resolve => setTimeout(resolve, 50))

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBeNull()
    expect(result.current.token).toBeNull()
  })

  it('exposes auth methods', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(typeof result.current.login).toBe('function')
    expect(typeof result.current.register).toBe('function')
    expect(typeof result.current.logout).toBe('function')
    expect(typeof result.current.refreshUser).toBe('function')
    expect(typeof result.current.updateProfile).toBe('function')
    expect(typeof result.current.changePassword).toBe('function')
    expect(typeof result.current.verifyEmail).toBe('function')
    expect(typeof result.current.resendVerification).toBe('function')
    expect(typeof result.current.checkVerificationStatus).toBe('function')
  })

  it('restores auth via silent refresh on mount', async () => {
    // Phase LXIV: tokens are in-memory only (useRef) — no sessionStorage token key.
    // Auth is restored on mount by calling /auth/refresh; the HttpOnly cookie is
    // sent automatically by the browser (credentials: 'include').
    // Security Sprint: X-Requested-With header is required by the refresh endpoint.
    // Security remediation: browser refresh responses no longer include
    // access_token in the JSON body — the cookie alone is the carrier.
    const originalFetch = global.fetch
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        // access_token deliberately omitted — browser default contract.
        user: {
          id: 1, email: 'test@example.com', name: 'Test User',
          is_verified: true, is_active: true, created_at: '2024-01-01',
        },
      }),
    } as Response)

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true)
    })

    // Security remediation: browser cookie-auth uses a non-null sentinel
    // so 56 hooks gating on `!token` and the apiClient 401-retry path
    // (which checks truthy `newToken`) keep working unchanged. The actual
    // JWT travels via the HttpOnly cookie. Treat the sentinel as opaque.
    expect(result.current.token).toBeTruthy()
    expect(typeof result.current.token).toBe('string')
    expect(result.current.user?.email).toBe('test@example.com')

    // Verify X-Requested-With header was sent with refresh request
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/refresh'),
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-Requested-With': 'XMLHttpRequest',
        }),
      }),
    )

    global.fetch = originalFetch
  })

  it('remains unauthenticated when silent refresh fails', async () => {
    // Default fetch mock is not set — refreshAccessToken catches the error and
    // leaves auth state as unauthenticated.
    const { result } = renderHook(() => useAuth(), { wrapper })

    await new Promise(resolve => setTimeout(resolve, 50))

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBeNull()
  })

  it('updateProfile returns error when not authenticated', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    await new Promise(resolve => setTimeout(resolve, 50))

    const authResult = await result.current.updateProfile({ name: 'New Name' })
    expect(authResult.success).toBe(false)
    expect(authResult.error).toBe('Not authenticated')
  })

  it('changePassword returns error when not authenticated', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    await new Promise(resolve => setTimeout(resolve, 50))

    const authResult = await result.current.changePassword({
      current_password: 'old',
      new_password: 'new123',
    })
    expect(authResult.success).toBe(false)
    expect(authResult.error).toBe('Not authenticated')
  })

  it('resendVerification returns error when not authenticated', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    await new Promise(resolve => setTimeout(resolve, 50))

    const authResult = await result.current.resendVerification()
    expect(authResult.success).toBe(false)
    expect(authResult.error).toBe('Not authenticated')
  })

  it('checkVerificationStatus returns null when not authenticated', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    await new Promise(resolve => setTimeout(resolve, 50))

    const status = await result.current.checkVerificationStatus()
    expect(status).toBeNull()
  })
})
