import { SkeletonPage, CardGridSkeleton } from '@/components/shared'

/**
 * Reconciliation Loading Skeleton — stats cards + score table.
 *
 * Sprint 209: Phase XXVII — Shared Skeleton Components
 */
export default function ReconLoading() {
  return (
    <SkeletonPage titleWidth="w-72" subtitleWidth="w-96" maxWidth="max-w-7xl">
      <CardGridSkeleton count={3} columns="grid-cols-1 md:grid-cols-3" />
    </SkeletonPage>
  )
}
