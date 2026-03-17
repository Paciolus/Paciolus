'use client'

/**
 * AuthSessionContext — Core authentication session provider.
 *
 * Owns the foundational auth lifecycle: in-memory access token storage,
 * HttpOnly refresh-cookie deduplication, login, register, logout, and
 * user-data refresh.  Every other auth-related context depends on this
 * one for the current token and user object.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - JWT access tokens stored in-memory only (React ref — not storage)
 * - Refresh tokens stored as HttpOnly Secure SameSite=Lax server-set cookies
 * - User metadata cached in sessionStorage for fast UI hydration (non-sensitive)
 * - No financial/trial balance data ever touches storage
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  ReactNode,
  ReactElement,
} from 'react'
import { useRouter } from 'next/navigation'
import type {
  User,
  AuthState,
  LoginCredentials,
  RegisterCredentials,
  AuthResponse,
  AuthResult,
} from '@/types/auth'
import { API_URL } from '@/utils/constants'
import { apiPost, apiGet, isAuthError, setTokenRefreshCallback, setCsrfToken, getCsrfToken } from '@/utils'

// Non-sensitive user metadata cache key (for fast UI hydration on reload)
const USER_KEY = 'paciolus_user'

/**
 * Clear non-sensitive session data on logout/auth failure.
 * SECURITY: Also wipes financial mapping data to prevent cross-session leakage.
 */
function clearAuthSessionData(): void {
  if (typeof window !== 'undefined') {
    sessionStorage.removeItem(USER_KEY)
    sessionStorage.removeItem('paciolus_account_mappings')
    sessionStorage.removeItem('paciolus_last_threshold')
  }
}

/**
 * Shape of the AuthSession context value — session state + core auth methods.
 */
export interface AuthSessionContextType extends AuthState {
  login: (credentials: LoginCredentials & { rememberMe?: boolean }) => Promise<AuthResult>
  register: (credentials: RegisterCredentials) => Promise<AuthResult>
  logout: () => void | Promise<void>
  refreshUser: () => Promise<void>
}

const AuthSessionContext = createContext<AuthSessionContextType | undefined>(undefined)

export function AuthSessionProvider({ children }: { children: ReactNode }): ReactElement {
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
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
          },
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

  const contextValue: AuthSessionContextType = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
  }

  return (
    <AuthSessionContext.Provider value={contextValue}>
      {children}
    </AuthSessionContext.Provider>
  )
}

/**
 * Hook to consume the core auth session context.
 * Provides: user, token, isAuthenticated, isLoading, login, register, logout, refreshUser.
 */
export function useAuthSession(): AuthSessionContextType {
  const context = useContext(AuthSessionContext)
  if (context === undefined) {
    throw new Error('useAuthSession must be used within an AuthSessionProvider')
  }
  return context
}
