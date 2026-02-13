'use client'

import Link from 'next/link'

/**
 * Engagements Error Boundary — catches errors in engagement pages.
 *
 * Sprint 208: Phase XXVII — Route Boundary Files
 */
export default function EngagementsError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <main className="min-h-screen bg-surface-page">
      <div className="pt-24 pb-16 px-6 max-w-2xl mx-auto flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-16 h-16 mb-6 rounded-full bg-clay-50 border border-clay-200 flex items-center justify-center">
          <svg className="w-8 h-8 text-clay-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>

        <h1 className="text-2xl font-serif font-bold text-content-primary mb-3 text-center">
          Workspace Error
        </h1>
        <p className="text-content-secondary text-center mb-8 leading-relaxed max-w-md">
          The diagnostic workspace encountered an error. Your engagement data is safe.
        </p>

        {process.env.NODE_ENV === 'development' && (
          <div className="mb-6 p-4 w-full bg-surface-card rounded-lg border border-clay-200/30 text-left">
            <p className="text-xs font-mono text-clay-500 break-all">{error.message}</p>
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={() => reset()}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-sage-500 hover:bg-sage-600 text-oatmeal-200 font-bold text-sm rounded-lg transition-colors duration-200 cursor-pointer"
          >
            Try Again
          </button>
          <Link
            href="/engagements"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-surface-card border border-oatmeal-300/30 hover:border-oatmeal-300/50 text-content-primary font-bold text-sm rounded-lg transition-colors duration-200"
          >
            Back to Workspaces
          </Link>
        </div>
      </div>
    </main>
  )
}
