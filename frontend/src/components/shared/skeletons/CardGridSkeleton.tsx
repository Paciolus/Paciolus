/**
 * CardGridSkeleton — configurable card grid placeholder.
 *
 * Renders a responsive grid of skeleton cards with animated pulse.
 * Card content adapts to variant: 'default' (title + 2 lines),
 * 'detailed' (title + 2 lines + button), or 'compact' (title + 1 line).
 *
 * Sprint 209: Phase XXVII — Shared Skeleton Components
 */

interface CardGridSkeletonProps {
  /** Number of skeleton cards to render (default: 3) */
  count?: number
  /** Grid columns class (default: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3') */
  columns?: string
  /** Card content variant */
  variant?: 'default' | 'detailed' | 'compact'
}

function CardContent({ variant }: { variant: string }) {
  if (variant === 'detailed') {
    return (
      <>
        <div className="h-5 w-32 bg-oatmeal-200 rounded mb-4" />
        <div className="h-3 w-full bg-oatmeal-200/50 rounded mb-2" />
        <div className="h-3 w-2/3 bg-oatmeal-200/30 rounded mb-4" />
        <div className="h-8 w-24 bg-oatmeal-200/40 rounded" />
      </>
    )
  }

  if (variant === 'compact') {
    return (
      <>
        <div className="h-5 w-36 bg-oatmeal-200 rounded mb-3" />
        <div className="h-3 w-3/4 bg-oatmeal-200/30 rounded" />
      </>
    )
  }

  // default
  return (
    <>
      <div className="h-5 w-24 bg-oatmeal-200 rounded mb-3" />
      <div className="h-3 w-full bg-oatmeal-200/50 rounded mb-2" />
      <div className="h-3 w-3/4 bg-oatmeal-200/30 rounded" />
    </>
  )
}

export function CardGridSkeleton({
  count = 3,
  columns = 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
  variant = 'default',
}: CardGridSkeletonProps) {
  return (
    <div className={`grid ${columns} gap-6`}>
      {Array.from({ length: count }, (_, i) => (
        <div
          key={i}
          className="animate-pulse bg-surface-card border border-oatmeal-300/30 rounded-xl p-6"
        >
          <CardContent variant={variant} />
        </div>
      ))}
    </div>
  )
}
