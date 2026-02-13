import { SkeletonPage, CardGridSkeleton } from '@/components/shared'

/**
 * Status Page Loading Skeleton — health check cards.
 *
 * Sprint 209: Phase XXVII — Shared Skeleton Components
 */
export default function StatusLoading() {
  return (
    <SkeletonPage maxWidth="max-w-4xl" titleWidth="w-48" subtitleWidth="w-72">
      <CardGridSkeleton count={4} columns="grid-cols-1 md:grid-cols-2" />
    </SkeletonPage>
  )
}
