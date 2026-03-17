/**
 * useUserProfile — Thin hook re-exporting the UserProfileContext consumer.
 *
 * Provides profile mutation operations: updateProfile and changePassword,
 * plus the current user object.  Use this in settings pages that manage
 * account metadata; most other components should prefer useAuthSession.
 */

export { useUserProfile } from '@/contexts/UserProfileContext'
export type { UserProfileContextType } from '@/contexts/UserProfileContext'
