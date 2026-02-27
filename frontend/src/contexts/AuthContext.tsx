'use client'

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  ReactNode,
  ReactElement
} from 'react'
import { useRouter } from 'next/navigation'
import type {
  User,
  AuthState,
  LoginCredentials,
  RegisterCredentials,
  ProfileUpdate,
  PasswordChange,
  AuthResponse,
  AuthResult,
  AuthContextType,
} from '@/types/auth'
import { API_URL } from '@/utils/constants'
import { apiPost, apiGet, apiPut, isAuthError, setTokenRefreshCallback, setCsrfToken, getCsrfToken } from '@/utils'

/**
 * AuthContext - Day 13: Secure Commercial Infrastructure
 * Sprint 198: Refresh Token Integration
 * HttpOnly Cookie Hardening: Refresh tokens moved to HttpOnly server-set cookies;
 * access tokens stored in-memory only (React ref, not storage).
 *
 * ZERO-STORAGE COMPLIANCE:
 * - JWT access tokens stored in-memory only (React ref — not storage)
 * - Refresh tokens stored as HttpOnly Secure SameSite=Lax server-set cookies
 * - User metadata cached in sessionStorage for fast UI hydration (non-sensitive)
 * - No financial/trial balance data ever touches storage
 */

// Non-sensitive user metadata cache key (for fast UI hydration on reload)
const USER_KEY = 'paciolus_user'

/**
 * Clear non-sensitive session data on logout/auth failure.
 */
function clearAuthSessionData(): void {
  if (typeof window !== 'undefined') {
    sessionStorage.removeItem(USER_KEY)
  }
}

// Context
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Provider component
export function AuthProvider({ children }: { children: ReactNode }): ReactElement {
  const router = useRouter()

  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  })

  // In-memory access token store (survives re-renders, not page reloads)
  const tokenRef = useRef<string | null>(null)

  // Ref to prevent concurrent refresh attempts
  const refreshPromiseRef = useRef<Promise<boolean> | null>(null)

  /**
   * Attempt to refresh the access token using the HttpOnly refresh cookie.
   * Returns true if successful, false if refresh failed (user should re-login).
   * Deduplicates concurrent calls — only one refresh request in-flight at a time.
   */
  const refreshAccessToken = useCallback(async (): Promise<boolean> => {
    // If a refresh is already in progress, wait for it
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current
    }

    const promise = (async () => {
      try {
        const response = await fetch(`${API_URL}/auth/refresh`, {
          method: 'POST',
          credentials: 'include',  // Sends HttpOnly refresh cookie automatically
          headers: { 'Content-Type': 'application/json' },
          // No body — cookie is sent automatically by the browser
        })

        if (!response.ok) {
          // Refresh failed — cookie expired or revoked
          clearAuthSessionData()
          tokenRef.current = null
          setState({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          })
          return false
        }

        const data: AuthResponse = await response.json()

        // Store access token in-memory only
        tokenRef.current = data.access_token
        sessionStorage.setItem(USER_KEY, JSON.stringify(data.user))

        // Security Sprint: Read user-bound CSRF token from auth response
        if (data.csrf_token) setCsrfToken(data.csrf_token)

        setState({
          user: data.user,
          token: data.access_token,
          isAuthenticated: true,
          isLoading: false,
        })

        return true
      } catch {
        // Network error during refresh
        return false
      } finally {
        refreshPromiseRef.current = null
      }
    })()

    refreshPromiseRef.current = promise
    return promise
  }, [])

  // Register the token refresh callback for apiClient 401 interception
  useEffect(() => {
    setTokenRefreshCallback(async () => {
      const success = await refreshAccessToken()
      if (success) {
        return tokenRef.current
      }
      return null
    })

    return () => {
      setTokenRefreshCallback(null)
    }
  }, [refreshAccessToken])

  // Initialize auth state — attempt silent refresh via HttpOnly cookie
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Attempt silent refresh — HttpOnly cookie sent automatically by browser.
        // refreshAccessToken sets isLoading: false on both success and failure paths.
        await refreshAccessToken()
      } catch (error) {
        console.error('Error initializing auth:', error)
        clearAuthSessionData()
        setState(prev => ({ ...prev, isLoading: false }))
      }
    }

    initAuth()
  }, [refreshAccessToken])

  // Login function
  const login = useCallback(async (credentials: LoginCredentials & { rememberMe?: boolean }): Promise<AuthResult> => {
    const { data, error, ok } = await apiPost<AuthResponse>(
      '/auth/login',
      null, // No token for login
      { email: credentials.email, password: credentials.password, remember_me: credentials.rememberMe ?? false }
    )

    if (ok && data?.access_token) {
      // Store access token in-memory only; refresh token is set as HttpOnly cookie by server
      tokenRef.current = data.access_token
      sessionStorage.setItem(USER_KEY, JSON.stringify(data.user))

      // Security Sprint: Read user-bound CSRF token from login response
      if (data.csrf_token) setCsrfToken(data.csrf_token)

      setState({
        user: data.user,
        token: data.access_token,
        isAuthenticated: true,
        isLoading: false,
      })

      return { success: true }
    }

    return { success: false, error: error || 'Login failed' }
  }, [])

  // Register function
  const register = useCallback(async (credentials: RegisterCredentials): Promise<AuthResult> => {
    const { data, error, ok } = await apiPost<AuthResponse>(
      '/auth/register',
      null, // No token for registration
      { email: credentials.email, password: credentials.password }
    )

    if (ok && data?.access_token) {
      // Store access token in-memory only; refresh token is set as HttpOnly cookie by server
      tokenRef.current = data.access_token
      sessionStorage.setItem(USER_KEY, JSON.stringify(data.user))

      // Security Sprint: Read user-bound CSRF token from register response
      if (data.csrf_token) setCsrfToken(data.csrf_token)

      setState({
        user: data.user,
        token: data.access_token,
        isAuthenticated: true,
        isLoading: false,
      })

      return { success: true }
    }

    return { success: false, error: error || 'Registration failed' }
  }, [])

  // Logout function — revokes HttpOnly refresh cookie server-side
  const logout = useCallback(async () => {
    // Best-effort server-side revocation (don't block on failure)
    try {
      const csrfToken = getCsrfToken()
      await fetch(`${API_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include',  // Sends HttpOnly cookie for server-side revocation
        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
        },
        // No body — cookie is sent automatically
      })
    } catch {
      // Ignore — we're logging out regardless
    }

    // Clear in-memory token + cached user + CSRF token
    tokenRef.current = null
    clearAuthSessionData()
    setCsrfToken(null)

    // Reset state
    setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    })

    // Redirect to login
    router.push('/login')
  }, [router])

  // Refresh user data from API
  const refreshUser = useCallback(async () => {
    if (!state.token) return

    const { data, status, ok } = await apiGet<User>('/auth/me', state.token)

    if (ok && data) {
      sessionStorage.setItem(USER_KEY, JSON.stringify(data))
      setState(prev => ({ ...prev, user: data }))
    } else if (isAuthError(status)) {
      // Try silent refresh before logging out
      const refreshed = await refreshAccessToken()
      if (!refreshed) {
        logout()
      }
    }
  }, [state.token, logout, refreshAccessToken])

  // Update user profile (Sprint 48)
  const updateProfile = useCallback(async (profileData: ProfileUpdate): Promise<AuthResult> => {
    if (!state.token) {
      return { success: false, error: 'Not authenticated' }
    }

    const { data, error, ok } = await apiPut<User>(
      '/users/me',
      state.token,
      { ...profileData } as Record<string, unknown>
    )

    if (ok && data) {
      // Update stored user data
      sessionStorage.setItem(USER_KEY, JSON.stringify(data))
      setState(prev => ({ ...prev, user: data }))
      return { success: true }
    }

    return { success: false, error: error || 'Failed to update profile' }
  }, [state.token])

  // Change password (Sprint 48)
  const changePassword = useCallback(async (passwordData: PasswordChange): Promise<AuthResult> => {
    if (!state.token) {
      return { success: false, error: 'Not authenticated' }
    }

    const { error, ok } = await apiPut<{ message: string }>(
      '/users/me/password',
      state.token,
      { ...passwordData } as Record<string, unknown>
    )

    if (ok) {
      return { success: true }
    }

    return { success: false, error: error || 'Failed to change password' }
  }, [state.token])

  // Verify email with token (Sprint 58) — no auth required
  const verifyEmail = useCallback(async (token: string): Promise<AuthResult> => {
    const { error, ok } = await apiPost<{ message: string; user: { id: number; email: string; is_verified: boolean } }>(
      `/auth/verify-email?token=${encodeURIComponent(token)}`,
      null,
      {}
    )

    if (ok) {
      // If user is logged in, refresh their data to update is_verified
      if (state.token) {
        const { data: userData } = await apiGet<User>('/auth/me', state.token)
        if (userData) {
          sessionStorage.setItem(USER_KEY, JSON.stringify(userData))
          setState(prev => ({ ...prev, user: userData }))
        }
      }
      return { success: true }
    }

    return { success: false, error: error || 'Email verification failed' }
  }, [state.token])

  // Resend verification email (Sprint 58) — requires auth
  const resendVerification = useCallback(async (): Promise<AuthResult> => {
    if (!state.token) {
      return { success: false, error: 'Not authenticated' }
    }

    const { error, ok } = await apiPost<{ message: string; cooldown_minutes: number }>(
      '/auth/resend-verification',
      state.token,
      {}
    )

    if (ok) {
      return { success: true }
    }

    return { success: false, error: error || 'Failed to resend verification email' }
  }, [state.token])

  // Check verification status (Sprint 58) — requires auth
  const checkVerificationStatus = useCallback(async () => {
    if (!state.token) return null

    const { data, ok } = await apiGet<{
      is_verified: boolean
      email: string
      verified_at: string | null
      can_resend: boolean
      resend_cooldown_seconds: number
      email_service_configured: boolean
    }>('/auth/verification-status', state.token)

    if (ok && data) return data
    return null
  }, [state.token])

  // Context value
  const contextValue: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
    updateProfile,
    changePassword,
    verifyEmail,
    resendVerification,
    checkVerificationStatus,
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}

// Hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Re-export types for convenience (backwards compatibility)
export type { User, AuthContextType, LoginCredentials, RegisterCredentials }
