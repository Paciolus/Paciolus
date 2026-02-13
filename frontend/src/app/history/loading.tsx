import { SkeletonPage, ListSkeleton } from '@/components/shared'

/**
 * History Loading Skeleton — shown during page transitions.
 *
 * Sprint 209: Refactored to use shared skeleton components.
 */
export default function HistoryLoading() {
  return (
    <SkeletonPage maxWidth="max-w-4xl" titleWidth="w-44" subtitleWidth="w-64">
      <ListSkeleton rows={5} showAvatar />
    </SkeletonPage>
  )
}
