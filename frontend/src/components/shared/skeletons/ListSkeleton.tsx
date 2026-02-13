/**
 * ListSkeleton — list/timeline row placeholder.
 *
 * Renders stacked row items with optional avatar circle,
 * title/subtitle lines, and trailing element.
 *
 * Sprint 209: Phase XXVII — Shared Skeleton Components
 */

interface ListSkeletonProps {
  /** Number of rows (default: 5) */
  rows?: number
  /** Show avatar circle on left (default: true) */
  showAvatar?: boolean
  /** Gap between rows (default: 'gap-4') */
  gap?: string
}

export function ListSkeleton({
  rows = 5,
  showAvatar = true,
  gap = 'gap-4',
}: ListSkeletonProps) {
  return (
    <div className={`flex flex-col ${gap}`}>
      {Array.from({ length: rows }, (_, i) => (
        <div
          key={i}
          className="animate-pulse bg-surface-card border border-oatmeal-300/30 rounded-xl p-5 flex items-center gap-4"
        >
          {showAvatar && (
            <div className="w-10 h-10 bg-oatmeal-200 rounded-full flex-shrink-0" />
          )}
          <div className="flex-1">
            <div className="h-4 w-48 bg-oatmeal-200 rounded mb-2" />
            <div className="h-3 w-32 bg-oatmeal-200/50 rounded" />
          </div>
          <div className="h-3 w-20 bg-oatmeal-200/40 rounded" />
        </div>
      ))}
    </div>
  )
}
