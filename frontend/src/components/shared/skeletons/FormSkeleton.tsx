/**
 * FormSkeleton — form fields placeholder.
 *
 * Renders stacked form sections with animated input field placeholders.
 * Each section has a title + configurable number of input rows.
 *
 * Sprint 209: Phase XXVII — Shared Skeleton Components
 */

interface FormSkeletonProps {
  /** Number of form sections (default: 3) */
  sections?: number
  /** Number of input fields per section (default: 3) */
  fieldsPerSection?: number
}

export function FormSkeleton({
  sections = 3,
  fieldsPerSection = 3,
}: FormSkeletonProps) {
  return (
    <div className="space-y-6">
      {Array.from({ length: sections }, (_, i) => (
        <div
          key={i}
          className="animate-pulse bg-surface-card border border-oatmeal-300/30 rounded-xl p-6"
        >
          <div className="h-5 w-28 bg-oatmeal-200 rounded mb-4" />
          {Array.from({ length: fieldsPerSection }, (_, j) => (
            <div
              key={j}
              className={`h-10 bg-oatmeal-200/40 rounded ${
                j === fieldsPerSection - 1 ? 'w-2/3' : 'w-full mb-3'
              }`}
            />
          ))}
        </div>
      ))}
    </div>
  )
}
