'use client'

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
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
import { apiPost, apiGet, apiPut, isAuthError } from '@/utils'

/**
 * AuthContext - Day 13: Secure Commercial Infrastructure
 *
 * Provides authentication state management for Paciolus.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - JWT tokens stored in sessionStorage (client-side only)
 * - User data stored in sessionStorage (client-side only)
 * - No financial/trial balance data ever touches storage
 * - Session ends when browser tab closes (true ephemeral)
 */

// Storage keys
const TOKEN_KEY = 'paciolus_token'
const USER_KEY = 'paciolus_user'

// Context
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter()

  // DEV MOCK: Simulated logged-in user for development testing
  const [state, setState] = useState<AuthState>({
    user: { id: 1, email: "test@paciolus.com", is_active: true, is_verified: true, created_at: "2026-02-03T00:00:00Z" },
    token: "mock-dev-token",
    isAuthenticated: true,
    isLoading: false, // Skip loading since we're using mock
  })

  // Initialize auth state from sessionStorage
  useEffect(() => {
    const initAuth = () => {
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
        } else {
          setState(prev => ({ ...prev, isLoading: false }))
        }
      } catch (error) {
        console.error('Error initializing auth:', error)
        // Clear potentially corrupted data
        sessionStorage.removeItem(TOKEN_KEY)
        sessionStorage.removeItem(USER_KEY)
        setState(prev => ({ ...prev, isLoading: false }))
      }
    }

    initAuth()
  }, [])

  // Login function
  const login = useCallback(async (credentials: LoginCredentials): Promise<AuthResult> => {
    const { data, error, ok } = await apiPost<AuthResponse>(
      '/auth/login',
      null, // No token for login
      { email: credentials.email, password: credentials.password }
    )

    if (ok && data?.access_token) {
      // Store in sessionStorage (Zero-Storage: client-side only)
      sessionStorage.setItem(TOKEN_KEY, data.access_token)
      sessionStorage.setItem(USER_KEY, JSON.stringify(data.user))

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

  // Logout function
  const logout = useCallback(() => {
    // Clear sessionStorage
    sessionStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(USER_KEY)

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
      // Token expired or invalid
      logout()
    }
  }, [state.token, logout])

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

  // Context value
  const contextValue: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
    updateProfile,
    changePassword,
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
