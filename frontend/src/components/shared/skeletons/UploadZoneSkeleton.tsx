/**
 * UploadZoneSkeleton — file upload area placeholder.
 *
 * Renders a dashed-border drop zone with icon, title, and
 * subtitle placeholders. Used by tool pages with file uploads.
 *
 * Sprint 209: Phase XXVII — Shared Skeleton Components
 */

export function UploadZoneSkeleton() {
  return (
    <div className="animate-pulse border-2 border-dashed border-oatmeal-300 rounded-xl p-12 mb-8">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 bg-oatmeal-200 rounded-full" />
        <div className="h-4 w-48 bg-oatmeal-200/60 rounded-sm" />
        <div className="h-3 w-32 bg-oatmeal-200/40 rounded-sm" />
      </div>
    </div>
  )
}
