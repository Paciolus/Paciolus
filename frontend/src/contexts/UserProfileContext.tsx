'use client'

/**
 * UserProfileContext — Profile reads/writes and password management.
 *
 * Depends on AuthSessionContext for the current access token and user
 * object.  Provides updateProfile and changePassword operations that
 * mutate the authenticated user's account metadata.  Keeps profile
 * concerns isolated so that components which only read session state
 * (token, isAuthenticated) do not re-render when profile mutations
 * occur.
 */

import {
  createContext,
  useContext,
  useCallback,
  ReactNode,
  ReactElement,
} from 'react'
import type { ProfileUpdate, PasswordChange, AuthResult, User } from '@/types/auth'
import { apiPut } from '@/utils'
import { useAuthSession } from './AuthSessionContext'

// Non-sensitive user metadata cache key (must match AuthSessionContext)
const USER_KEY = 'paciolus_user'

/**
 * Shape of the UserProfile context value.
 */
export interface UserProfileContextType {
  /** Current user (delegated from AuthSessionContext) */
  user: User | null
  /** Update display name or email */
  updateProfile: (data: ProfileUpdate) => Promise<AuthResult>
  /** Change the account password */
  changePassword: (data: PasswordChange) => Promise<AuthResult>
}

const UserProfileContext = createContext<UserProfileContextType | undefined>(undefined)

export function UserProfileProvider({ children }: { children: ReactNode }): ReactElement {
  const { token, user, refreshUser } = useAuthSession()

  // Update user profile
  const updateProfile = useCallback(async (profileData: ProfileUpdate): Promise<AuthResult> => {
    if (!token) {
      return { success: false, error: 'Not authenticated' }
    }

    const { data, error, ok } = await apiPut<User>(
      '/users/me',
      token,
      { ...profileData } as Record<string, unknown>
    )

    if (ok && data) {
      // Update stored user data — refresh via session provider
      sessionStorage.setItem(USER_KEY, JSON.stringify(data))
      // Trigger a refreshUser to sync state back to AuthSessionContext
      await refreshUser()
      return { success: true }
    }

    return { success: false, error: error || 'Failed to update profile' }
  }, [token, refreshUser])

  // Change password
  const changePassword = useCallback(async (passwordData: PasswordChange): Promise<AuthResult> => {
    if (!token) {
      return { success: false, error: 'Not authenticated' }
    }

    const { error, ok } = await apiPut<{ message: string }>(
      '/users/me/password',
      token,
      { ...passwordData } as Record<string, unknown>
    )

    if (ok) {
      return { success: true }
    }

    return { success: false, error: error || 'Failed to change password' }
  }, [token])

  const contextValue: UserProfileContextType = {
    user,
    updateProfile,
    changePassword,
  }

  return (
    <UserProfileContext.Provider value={contextValue}>
      {children}
    </UserProfileContext.Provider>
  )
}

/**
 * Hook to consume profile operations.
 * Provides: user, updateProfile, changePassword.
 */
export function useUserProfile(): UserProfileContextType {
  const context = useContext(UserProfileContext)
  if (context === undefined) {
    throw new Error('useUserProfile must be used within a UserProfileProvider')
  }
  return context
}
