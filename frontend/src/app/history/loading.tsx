/**
 * History Loading Skeleton — shown during page transitions.
 *
 * Sprint 208: Phase XXVII — Route Boundary Files
 */
export default function HistoryLoading() {
  return (
    <main className="min-h-screen bg-surface-page">
      <div className="pt-24 pb-16 px-6 max-w-4xl mx-auto">
        <div className="animate-pulse mb-8">
          <div className="h-8 w-44 bg-oatmeal-200 rounded-lg mb-3" />
          <div className="h-4 w-64 bg-oatmeal-200/60 rounded" />
        </div>
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="animate-pulse bg-surface-card border border-oatmeal-300/30 rounded-xl p-5 flex items-center gap-4">
              <div className="w-10 h-10 bg-oatmeal-200 rounded-full flex-shrink-0" />
              <div className="flex-1">
                <div className="h-4 w-48 bg-oatmeal-200 rounded mb-2" />
                <div className="h-3 w-32 bg-oatmeal-200/50 rounded" />
              </div>
              <div className="h-3 w-20 bg-oatmeal-200/40 rounded" />
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
