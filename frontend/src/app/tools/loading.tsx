import { SkeletonPage, CardGridSkeleton, UploadZoneSkeleton } from '@/components/shared'

/**
 * Tools Loading Skeleton — shown during page transitions between tools.
 *
 * ToolNav renders from layout so the nav bar stays visible during loading.
 *
 * Sprint 209: Refactored to use shared skeleton components.
 */
export default function ToolsLoading() {
  return (
    <SkeletonPage titleWidth="w-64" subtitleWidth="w-96">
      <UploadZoneSkeleton />
      <CardGridSkeleton count={3} columns="grid-cols-1 md:grid-cols-3" />
    </SkeletonPage>
  )
}
