import { SkeletonPage, CardGridSkeleton } from '@/components/shared'

/**
 * Engagements Loading Skeleton — shown during page transitions.
 *
 * Sprint 209: Refactored to use shared skeleton components.
 */
export default function EngagementsLoading() {
  return (
    <SkeletonPage maxWidth="max-w-6xl">
      <CardGridSkeleton count={3} variant="detailed" />
    </SkeletonPage>
  )
}
