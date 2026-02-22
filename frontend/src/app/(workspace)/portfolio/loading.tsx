import { SkeletonPage, CardGridSkeleton } from '@/components/shared'

/**
 * Portfolio Loading Skeleton — shown during page transitions.
 *
 * Sprint 209: Refactored to use shared skeleton components.
 * Sprint 385: Moved to (workspace) route group.
 */
export default function PortfolioLoading() {
  return (
    <SkeletonPage maxWidth="max-w-6xl" titleWidth="w-48" subtitleWidth="w-72">
      <CardGridSkeleton count={6} variant="compact" />
    </SkeletonPage>
  )
}
