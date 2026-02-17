'use client'

import Link from 'next/link'

/**
 * Auth Route Group Error Boundary
 *
 * Sprint 281: Phase XXXVIII — catches errors in /login, /register,
 * /verify-email, /verification-pending pages.
 *
 * Renders on the dark theme (auth pages are vault exterior).
 */
export default function AuthError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* Error icon */}
        <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-clay-500/15 flex items-center justify-center">
          <svg
            className="w-8 h-8 text-clay-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>

        <h1 className="text-2xl font-serif font-bold text-content-primary mb-3">
          Authentication Error
        </h1>

        <p className="text-content-secondary mb-8 leading-relaxed">
          Something went wrong during authentication. Please try again
          or return to the login page.
        </p>

        {process.env.NODE_ENV === 'development' && (
          <div className="mb-6 p-4 bg-surface-card rounded-lg border border-clay-500/20 text-left">
            <p className="text-xs font-mono text-clay-300 break-all">
              {error.message}
            </p>
            {error.digest && (
              <p className="text-xs font-mono text-content-tertiary mt-2">
                Digest: {error.digest}
              </p>
            )}
          </div>
        )}

        <div className="flex gap-3 justify-center">
          <button
            onClick={() => reset()}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-sage-500 hover:bg-sage-600 text-oatmeal-200 font-bold text-sm rounded-lg transition-colors duration-200 cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Try Again
          </button>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-transparent border border-content-tertiary/30 hover:border-content-tertiary/50 text-content-primary font-bold text-sm rounded-lg transition-colors duration-200"
          >
            Back to Login
          </Link>
        </div>
      </div>
    </div>
  )
}
