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
  AuthResponse,
  AuthResult,
  AuthContextType,
} from '@/types/auth'

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

// API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL

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
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      })

      const data = await response.json()

      if (response.ok && data.access_token) {
        const authResponse = data as AuthResponse

        // Store in sessionStorage (Zero-Storage: client-side only)
        sessionStorage.setItem(TOKEN_KEY, authResponse.access_token)
        sessionStorage.setItem(USER_KEY, JSON.stringify(authResponse.user))

        setState({
          user: authResponse.user,
          token: authResponse.access_token,
          isAuthenticated: true,
          isLoading: false,
        })

        return { success: true }
      } else {
        const errorMessage = typeof data.detail === 'string'
          ? data.detail
          : data.detail?.message || 'Login failed'
        return { success: false, error: errorMessage }
      }
    } catch (error) {
      console.error('Login error:', error)
      return { success: false, error: 'Unable to connect to server. Please try again.' }
    }
  }, [])

  // Register function
  const register = useCallback(async (credentials: RegisterCredentials): Promise<AuthResult> => {
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      })

      const data = await response.json()

      if (response.ok && data.access_token) {
        const authResponse = data as AuthResponse

        // Store in sessionStorage (Zero-Storage: client-side only)
        sessionStorage.setItem(TOKEN_KEY, authResponse.access_token)
        sessionStorage.setItem(USER_KEY, JSON.stringify(authResponse.user))

        setState({
          user: authResponse.user,
          token: authResponse.access_token,
          isAuthenticated: true,
          isLoading: false,
        })

        return { success: true }
      } else {
        // Handle structured error response
        let errorMessage = 'Registration failed'
        if (typeof data.detail === 'string') {
          errorMessage = data.detail
        } else if (data.detail?.message) {
          errorMessage = data.detail.message
          if (data.detail.issues) {
            errorMessage += ': ' + data.detail.issues.join(', ')
          }
        }
        return { success: false, error: errorMessage }
      }
    } catch (error) {
      console.error('Registration error:', error)
      return { success: false, error: 'Unable to connect to server. Please try again.' }
    }
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

    try {
      const response = await fetch(`${API_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${state.token}`,
        },
      })

      if (response.ok) {
        const user = await response.json() as User
        sessionStorage.setItem(USER_KEY, JSON.stringify(user))
        setState(prev => ({ ...prev, user }))
      } else if (response.status === 401) {
        // Token expired or invalid
        logout()
      }
    } catch (error) {
      console.error('Error refreshing user:', error)
    }
  }, [state.token, logout])

  // Context value
  const contextValue: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
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
