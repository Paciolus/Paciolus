'use client'

/**
 * VerificationContext — Email verification and resend flows.
 *
 * Depends on AuthSessionContext for the current access token, user
 * object, and isAuthenticated flag.  Provides verifyEmail (public,
 * token-based), resendVerification (authenticated), and
 * checkVerificationStatus (authenticated) operations.  Isolating
 * these keeps the session provider lean and avoids unnecessary
 * re-renders in components that never touch verification.
 */

import {
  createContext,
  useContext,
  useCallback,
  ReactNode,
  ReactElement,
} from 'react'
import type { User, AuthResult } from '@/types/auth'
import type { VerificationStatus } from '@/types/verification'
import { apiPost, apiGet } from '@/utils'
import { useAuthSession } from './AuthSessionContext'

// Non-sensitive user metadata cache key (must match AuthSessionContext)
const USER_KEY = 'paciolus_user'

/**
 * Shape of the Verification context value.
 */
export interface VerificationContextType {
  /** Verify an email address using a one-time token (no auth required) */
  verifyEmail: (token: string) => Promise<AuthResult>
  /** Resend the verification email (requires auth) */
  resendVerification: () => Promise<AuthResult>
  /** Check current verification status (requires auth) */
  checkVerificationStatus: () => Promise<VerificationStatus | null>
}

const VerificationContext = createContext<VerificationContextType | undefined>(undefined)

export function VerificationProvider({ children }: { children: ReactNode }): ReactElement {
  const { token: authToken, refreshUser } = useAuthSession()

  // Verify email with token — no auth required
  const verifyEmail = useCallback(async (verificationToken: string): Promise<AuthResult> => {
    const { error, ok } = await apiPost<{ message: string; user: { id: number; email: string; is_verified: boolean } }>(
      `/auth/verify-email?token=${encodeURIComponent(verificationToken)}`,
      null,
      {}
    )

    if (ok) {
      // If user is logged in, refresh their data to update is_verified
      if (authToken) {
        const { data: userData } = await apiGet<User>('/auth/me', authToken)
        if (userData) {
          sessionStorage.setItem(USER_KEY, JSON.stringify(userData))
          // Sync back to session provider
          await refreshUser()
        }
      }
      return { success: true }
    }

    return { success: false, error: error || 'Email verification failed' }
  }, [authToken, refreshUser])

  // Resend verification email — requires auth
  const resendVerification = useCallback(async (): Promise<AuthResult> => {
    if (!authToken) {
      return { success: false, error: 'Not authenticated' }
    }

    const { error, ok } = await apiPost<{ message: string; cooldown_minutes: number }>(
      '/auth/resend-verification',
      authToken,
      {}
    )

    if (ok) {
      return { success: true }
    }

    return { success: false, error: error || 'Failed to resend verification email' }
  }, [authToken])

  // Check verification status — requires auth
  const checkVerificationStatus = useCallback(async () => {
    if (!authToken) return null

    const { data, ok } = await apiGet<VerificationStatus>(
      '/auth/verification-status',
      authToken
    )

    if (ok && data) return data
    return null
  }, [authToken])

  const contextValue: VerificationContextType = {
    verifyEmail,
    resendVerification,
    checkVerificationStatus,
  }

  return (
    <VerificationContext.Provider value={contextValue}>
      {children}
    </VerificationContext.Provider>
  )
}

/**
 * Hook to consume email verification operations.
 * Provides: verifyEmail, resendVerification, checkVerificationStatus.
 */
export function useVerificationContext(): VerificationContextType {
  const context = useContext(VerificationContext)
  if (context === undefined) {
    throw new Error('useVerificationContext must be used within a VerificationProvider')
  }
  return context
}
