'use client'

/**
 * AuthContext — Backward-compatible facade composing three focused providers.
 *
 * This file now delegates all state and logic to:
 *   - AuthSessionContext   (token storage, refresh dedup, login, logout, register)
 *   - UserProfileContext   (profile reads/writes, password change)
 *   - VerificationContext  (email verification, resend flows)
 *
 * The `AuthProvider` wraps all three in the correct dependency order, and
 * `useAuth()` returns a combined object matching the legacy AuthContextType
 * interface so that existing consumers continue to work without changes.
 *
 * New code should prefer the narrower hooks:
 *   - useAuthSession()       for session state (token, user, login, logout)
 *   - useUserProfile()       for profile/password mutations
 *   - useVerificationContext()  for email verification flows
 */

import { ReactNode, ReactElement } from 'react'
import type { AuthContextType, User, LoginCredentials, RegisterCredentials } from '@/types/auth'
import { AuthSessionProvider, useAuthSession } from './AuthSessionContext'
import { UserProfileProvider, useUserProfile } from './UserProfileContext'
import { VerificationProvider, useVerificationContext } from './VerificationContext'

/**
 * AuthProvider — Nests all three focused providers in dependency order.
 * AuthSession is the outermost (no dependencies), then UserProfile and
 * Verification which both read from AuthSession.
 */
export function AuthProvider({ children }: { children: ReactNode }): ReactElement {
  return (
    <AuthSessionProvider>
      <UserProfileProvider>
        <VerificationProvider>
          {children}
        </VerificationProvider>
      </UserProfileProvider>
    </AuthSessionProvider>
  )
}

/**
 * useAuth — Backward-compatible hook that merges all three contexts.
 *
 * Returns the full AuthContextType interface.  Existing consumers can
 * continue to `import { useAuth } from '@/contexts/AuthContext'` with
 * no changes.  For new code, prefer the narrower hooks above.
 */
export function useAuth(): AuthContextType {
  const session = useAuthSession()
  const profile = useUserProfile()
  const verification = useVerificationContext()

  return {
    // Session state
    user: session.user,
    token: session.token,
    isAuthenticated: session.isAuthenticated,
    isLoading: session.isLoading,
    login: session.login,
    register: session.register,
    logout: session.logout,
    refreshUser: session.refreshUser,
    // Profile operations
    updateProfile: profile.updateProfile,
    changePassword: profile.changePassword,
    // Verification operations
    verifyEmail: verification.verifyEmail,
    resendVerification: verification.resendVerification,
    checkVerificationStatus: verification.checkVerificationStatus,
  }
}

// Re-export types for convenience (backwards compatibility)
export type { User, AuthContextType, LoginCredentials, RegisterCredentials }
