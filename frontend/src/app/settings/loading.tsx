import { SkeletonPage, FormSkeleton } from '@/components/shared'

/**
 * Settings Loading Skeleton — covers /settings, /settings/profile, /settings/practice.
 *
 * Sprint 209: Refactored to use shared skeleton components.
 */
export default function SettingsLoading() {
  return (
    <SkeletonPage maxWidth="max-w-3xl" titleWidth="w-40" subtitleWidth="w-64">
      <FormSkeleton sections={3} fieldsPerSection={3} />
    </SkeletonPage>
  )
}
