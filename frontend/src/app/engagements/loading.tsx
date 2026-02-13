/**
 * Engagements Loading Skeleton — shown during page transitions.
 *
 * Sprint 208: Phase XXVII — Route Boundary Files
 */
export default function EngagementsLoading() {
  return (
    <main className="min-h-screen bg-surface-page">
      <div className="pt-24 pb-16 px-6 max-w-6xl mx-auto">
        <div className="animate-pulse mb-8">
          <div className="h-8 w-56 bg-oatmeal-200 rounded-lg mb-3" />
          <div className="h-4 w-80 bg-oatmeal-200/60 rounded" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse bg-surface-card border border-oatmeal-300/30 rounded-xl p-6">
              <div className="h-5 w-32 bg-oatmeal-200 rounded mb-4" />
              <div className="h-3 w-full bg-oatmeal-200/50 rounded mb-2" />
              <div className="h-3 w-2/3 bg-oatmeal-200/30 rounded mb-4" />
              <div className="h-8 w-24 bg-oatmeal-200/40 rounded" />
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
