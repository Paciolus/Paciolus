/**
 * SkeletonPage — universal loading page wrapper.
 *
 * Provides the common structure shared by ALL loading.tsx files:
 * <main> + container + animated header (title + subtitle).
 *
 * Sprint 209: Phase XXVII — Shared Skeleton Components
 */

interface SkeletonPageProps {
  /** Container max-width class (default: 'max-w-5xl') */
  maxWidth?: string
  /** Title skeleton width class (default: 'w-56') */
  titleWidth?: string
  /** Subtitle skeleton width class (default: 'w-80') */
  subtitleWidth?: string
  /** Page content below the header */
  children: React.ReactNode
}

export function SkeletonPage({
  maxWidth = 'max-w-5xl',
  titleWidth = 'w-56',
  subtitleWidth = 'w-80',
  children,
}: SkeletonPageProps) {
  return (
    <main className="min-h-screen bg-surface-page">
      <div className={`pt-24 pb-16 px-6 ${maxWidth} mx-auto`}>
        <div className="animate-pulse mb-8">
          <div className={`h-8 ${titleWidth} bg-oatmeal-200 rounded-lg mb-3`} />
          <div className={`h-4 ${subtitleWidth} bg-oatmeal-200/60 rounded`} />
        </div>
        {children}
      </div>
    </main>
  )
}
