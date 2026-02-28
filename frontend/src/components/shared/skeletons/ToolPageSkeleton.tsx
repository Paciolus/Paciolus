/**
 * ToolPageSkeleton — specialized skeleton for tool page loading states.
 *
 * Renders the common tool page structure: title + subtitle header,
 * upload zone placeholder, and a results section (cards or table rows).
 *
 * Phase LXVII: Visual Polish — B4 tool loading skeletons.
 */

import { CardGridSkeleton } from './CardGridSkeleton'
import { SkeletonPage } from './SkeletonPage'
import { UploadZoneSkeleton } from './UploadZoneSkeleton'

interface ToolPageSkeletonProps {
  /** Title skeleton width (default: 'w-64') */
  titleWidth?: string
  /** Subtitle skeleton width (default: 'w-96') */
  subtitleWidth?: string
  /** Results variant: 'cards' renders card grid, 'table' renders table rows */
  resultsVariant?: 'cards' | 'table'
  /** Number of result items (default: 3 for cards, 5 for table) */
  resultCount?: number
}

function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="animate-pulse bg-surface-card border border-oatmeal-300/30 rounded-xl overflow-hidden relative">
      {/* Table header */}
      <div className="border-b border-oatmeal-300/20 px-6 py-4 flex gap-8">
        <div className="h-3 w-24 bg-oatmeal-200/60 rounded-sm" />
        <div className="h-3 w-32 bg-oatmeal-200/60 rounded-sm" />
        <div className="h-3 w-20 bg-oatmeal-200/60 rounded-sm" />
        <div className="h-3 w-28 bg-oatmeal-200/60 rounded-sm hidden md:block" />
      </div>
      {/* Table rows */}
      {Array.from({ length: rows }, (_, i) => (
        <div
          key={i}
          className="border-b border-oatmeal-300/10 px-6 py-3 flex items-center gap-8"
        >
          <div className="h-3 w-20 bg-oatmeal-200/40 rounded-sm" />
          <div className="h-3 w-36 bg-oatmeal-200/30 rounded-sm" />
          <div className="h-3 w-16 bg-oatmeal-200/30 rounded-sm" />
          <div className="h-3 w-24 bg-oatmeal-200/20 rounded-sm hidden md:block" />
        </div>
      ))}
      <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent" style={{ animation: 'shimmer 1.5s infinite' }} />
    </div>
  )
}

export function ToolPageSkeleton({
  titleWidth = 'w-64',
  subtitleWidth = 'w-96',
  resultsVariant = 'cards',
  resultCount,
}: ToolPageSkeletonProps) {
  const count = resultCount ?? (resultsVariant === 'table' ? 5 : 3)

  return (
    <SkeletonPage titleWidth={titleWidth} subtitleWidth={subtitleWidth}>
      <UploadZoneSkeleton />
      {resultsVariant === 'table' ? (
        <TableSkeleton rows={count} />
      ) : (
        <CardGridSkeleton count={count} columns="grid-cols-1 md:grid-cols-3" />
      )}
    </SkeletonPage>
  )
}
