/**
 * useAuthSession — Thin hook re-exporting the AuthSessionContext consumer.
 *
 * Provides the core authentication session: user, token, isAuthenticated,
 * isLoading, login, register, logout, and refreshUser.  Prefer this hook
 * in components that only need session state and never touch profile or
 * verification operations.
 */

export { useAuthSession } from '@/contexts/AuthSessionContext'
export type { AuthSessionContextType } from '@/contexts/AuthSessionContext'
