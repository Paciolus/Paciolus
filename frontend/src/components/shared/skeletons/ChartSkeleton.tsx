/**
 * ChartSkeleton — fallback placeholder for lazy-loaded chart components.
 *
 * Sprint 772a: shows while next/dynamic resolves recharts (~90 kB gzipped).
 * The default 200px height matches BenfordChart and TrendSparkline render
 * footprints closely enough that there's no visible layout shift when the
 * real component swaps in.
 */

interface ChartSkeletonProps {
  /** Tailwind height class (default: 'h-[200px]') */
  heightClass?: string
}

export function ChartSkeleton({ heightClass = 'h-[200px]' }: ChartSkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-surface-card border border-oatmeal-300/30 rounded-xl ${heightClass} relative overflow-hidden`}
      aria-hidden="true"
    >
      <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-oatmeal-50/10 to-transparent" style={{ animation: 'shimmer 1.5s infinite' }} />
    </div>
  )
}
