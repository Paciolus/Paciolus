'use client'

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  ReactNode
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
import { apiPost, apiGet, apiPut, isAuthError, setTokenRefreshCallback, fetchCsrfToken, setCsrfToken, getCsrfToken } from '@/utils'
import { API_URL } from '@/utils/constants'

/**
 * AuthContext - Day 13: Secure Commercial Infrastructure
 * Sprint 198: Refresh Token Integration
 *
 * Provides authentication state management for Paciolus.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - JWT access tokens stored in sessionStorage (client-side only)
 * - Refresh tokens stored in sessionStorage (default) or localStorage ("Remember Me")
 * - User data stored in sessionStorage (client-side only)
 * - No financial/trial balance data ever touches storage
 */

// Storage keys
const TOKEN_KEY = 'paciolus_token'
const USER_KEY = 'paciolus_user'
const REFRESH_TOKEN_KEY = 'paciolus_refresh_token'
const REMEMBER_ME_KEY = 'paciolus_remember_me'

/**
 * Get the stored refresh token from either localStorage or sessionStorage.
 * localStorage is used when "Remember Me" was checked at login.
 */
function getStoredRefreshToken(): string | null {
  if (typeof window === 'undefined') return null
  // Check localStorage first (Remember Me), then sessionStorage
  return localStorage.getItem(REFRESH_TOKEN_KEY) || sessionStorage.getItem(REFRESH_TOKEN_KEY)
}

/**
 * Store the refresh token in the appropriate storage.
 */
function storeRefreshToken(token: string, rememberMe: boolean): void {
  if (rememberMe) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
    localStorage.setItem(REMEMBER_ME_KEY, 'true')
    // Also keep in sessionStorage for current session
    sessionStorage.setItem(REFRESH_TOKEN_KEY, token)
  } else {
    sessionStorage.setItem(REFRESH_TOKEN_KEY, token)
  }
}

/**
 * Clear all auth tokens from both storage locations.
 */
function clearAllAuthStorage(): void {
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(USER_KEY)
  sessionStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(REMEMBER_ME_KEY)
}

/**
 * Check if "Remember Me" was previously set.
 */
function isRememberMeActive(): boolean {
  if (typeof window === 'undefined') return false
  return localStorage.getItem(REMEMBER_ME_KEY) === 'true'
}

// Context
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter()

  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  })

  // Ref to prevent concurrent refresh attempts
  const refreshPromiseRef = useRef<Promise<boolean> | null>(null)

  /**
   * Attempt to refresh the access token using the stored refresh token.
   * Returns true if successful, false if refresh failed (user should re-login).
   * Deduplicates concurrent calls — only one refresh request in-flight at a time.
   */
  const refreshAccessToken = useCallback(async (): Promise<boolean> => {
    // If a refresh is already in progress, wait for it
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current
    }

    const refreshToken = getStoredRefreshToken()
    if (!refreshToken) return false

    const promise = (async () => {
      try {
        const response = await fetch(`${API_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        })

        if (!response.ok) {
          // Refresh failed — token expired or revoked
          clearAllAuthStorage()
          setState({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          })
          return false
        }

        const data: AuthResponse = await response.json()
        const rememberMe = isRememberMeActive()

        // Store new tokens
        sessionStorage.setItem(TOKEN_KEY, data.access_token)
        sessionStorage.setItem(USER_KEY, JSON.stringify(data.user))
        storeRefreshToken(data.refresh_token, rememberMe)

        // Sprint 200: Refresh CSRF token alongside auth token
        await fetchCsrfToken()

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
        // Return the new token from sessionStorage
        return sessionStorage.getItem(TOKEN_KEY)
      }
      return null
    })

    return () => {
      setTokenRefreshCallback(null)
    }
  }, [refreshAccessToken])

  // Initialize auth state from storage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedToken = sessionStorage.getItem(TOKEN_KEY)
        const storedUser = sessionStorage.getItem(USER_KEY)

        if (storedToken && storedUser) {
          const user = JSON.parse(storedUser) as User
          setState({
            user,
            token: storedToken,
            isAuthenticated: true,
            isLoading: false,
          })
          return
        }

        // No session token — check if we have a refresh token (Remember Me)
        const refreshToken = getStoredRefreshToken()
        if (refreshToken) {
          const success = await refreshAccessToken()
          if (success) return
        }

        setState(prev => ({ ...prev, isLoading: false }))
      } catch (error) {
        console.error('Error initializing auth:', error)
        clearAllAuthStorage()
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
      { email: credentials.email, password: credentials.password }
    )

    if (ok && data?.access_token) {
      const rememberMe = credentials.rememberMe ?? false

      // Store in sessionStorage (Zero-Storage: client-side only)
      sessionStorage.setItem(TOKEN_KEY, data.access_token)
      sessionStorage.setItem(USER_KEY, JSON.stringify(data.user))
      storeRefreshToken(data.refresh_token, rememberMe)

      // Sprint 200: Fetch CSRF token for mutation request protection
      await fetchCsrfToken()

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
      // Store in sessionStorage (Zero-Storage: client-side only)
      sessionStorage.setItem(TOKEN_KEY, data.access_token)
      sessionStorage.setItem(USER_KEY, JSON.stringify(data.user))
      // Registration doesn't have "Remember Me" — store in sessionStorage
      storeRefreshToken(data.refresh_token, false)

      // Sprint 200: Fetch CSRF token for mutation request protection
      await fetchCsrfToken()

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

  // Logout function — revokes refresh token server-side
  const logout = useCallback(async () => {
    const refreshToken = getStoredRefreshToken()

    // Best-effort server-side revocation (don't block on failure)
    if (refreshToken) {
      try {
        const csrfToken = getCsrfToken()
        await fetch(`${API_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        })
      } catch {
        // Ignore — we're logging out regardless
      }
    }

    // Clear all storage + CSRF token (Sprint 200)
    clearAllAuthStorage()
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
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Re-export types for convenience (backwards compatibility)
export type { User, AuthContextType, LoginCredentials, RegisterCredentials }
