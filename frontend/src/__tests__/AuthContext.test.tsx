/**
 * Sprint 234: AuthContext tests — provider rendering, useAuth hook contract
 */
import { ReactNode } from 'react'
import { renderHook } from '@testing-library/react'

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
import { AuthProvider, useAuth } from '@/contexts/AuthContext'

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
    }).toThrow('useAuth must be used within an AuthProvider')

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

  it('restores auth from sessionStorage', async () => {
    // Seed sessionStorage before rendering
    sessionStorage.setItem('paciolus_token', 'stored-token')
    sessionStorage.setItem('paciolus_user', JSON.stringify({
      id: 1, email: 'test@example.com', name: 'Test User', is_verified: true,
    }))

    const { result } = renderHook(() => useAuth(), { wrapper })

    // Wait for async initialization
    await new Promise(resolve => setTimeout(resolve, 50))

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.token).toBe('stored-token')
    expect(result.current.user?.email).toBe('test@example.com')
  })

  it('clears auth on invalid stored user data', async () => {
    sessionStorage.setItem('paciolus_token', 'bad-token')
    sessionStorage.setItem('paciolus_user', '"not-an-object"')

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
