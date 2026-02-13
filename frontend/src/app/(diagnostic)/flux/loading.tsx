import { SkeletonPage, CardGridSkeleton, UploadZoneSkeleton } from '@/components/shared'

/**
 * Flux Analysis Loading Skeleton — dual file upload + parameters.
 *
 * Sprint 209: Phase XXVII — Shared Skeleton Components
 */
export default function FluxLoading() {
  return (
    <SkeletonPage titleWidth="w-72" subtitleWidth="w-96" maxWidth="max-w-7xl">
      <CardGridSkeleton count={3} columns="grid-cols-1 md:grid-cols-3" />
    </SkeletonPage>
  )
}
