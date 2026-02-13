/**
 * Tools Loading Skeleton — shown during page transitions between tools.
 *
 * Light-theme aware via semantic tokens. ToolNav renders from layout
 * so the nav bar stays visible during loading.
 *
 * Sprint 207: Phase XXVII — Tool Layout Consolidation
 */
export default function ToolsLoading() {
  return (
    <main className="min-h-screen bg-surface-page">
      <div className="pt-24 pb-16 px-6 max-w-5xl mx-auto">
        {/* Title skeleton */}
        <div className="animate-pulse mb-8">
          <div className="h-8 w-64 bg-oatmeal-200 rounded-lg mb-3" />
          <div className="h-4 w-96 bg-oatmeal-200/60 rounded" />
        </div>

        {/* Upload zone skeleton */}
        <div className="animate-pulse border-2 border-dashed border-oatmeal-300 rounded-xl p-12 mb-8">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 bg-oatmeal-200 rounded-full" />
            <div className="h-4 w-48 bg-oatmeal-200/60 rounded" />
            <div className="h-3 w-32 bg-oatmeal-200/40 rounded" />
          </div>
        </div>

        {/* Info cards skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse bg-surface-card border border-oatmeal-300/30 rounded-xl p-6">
              <div className="h-5 w-24 bg-oatmeal-200 rounded mb-3" />
              <div className="h-3 w-full bg-oatmeal-200/50 rounded mb-2" />
              <div className="h-3 w-3/4 bg-oatmeal-200/30 rounded" />
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
