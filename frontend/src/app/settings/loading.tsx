/**
 * Settings Loading Skeleton — shown during page transitions.
 *
 * Covers /settings, /settings/profile, /settings/practice.
 *
 * Sprint 208: Phase XXVII — Route Boundary Files
 */
export default function SettingsLoading() {
  return (
    <main className="min-h-screen bg-surface-page">
      <div className="pt-24 pb-16 px-6 max-w-3xl mx-auto">
        <div className="animate-pulse mb-8">
          <div className="h-8 w-40 bg-oatmeal-200 rounded-lg mb-3" />
          <div className="h-4 w-64 bg-oatmeal-200/60 rounded" />
        </div>
        <div className="space-y-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse bg-surface-card border border-oatmeal-300/30 rounded-xl p-6">
              <div className="h-5 w-28 bg-oatmeal-200 rounded mb-4" />
              <div className="h-10 w-full bg-oatmeal-200/40 rounded mb-3" />
              <div className="h-10 w-full bg-oatmeal-200/40 rounded mb-3" />
              <div className="h-10 w-2/3 bg-oatmeal-200/40 rounded" />
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
