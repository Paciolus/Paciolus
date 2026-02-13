import Link from 'next/link'

/**
 * Custom 404 — branded "Not Found" page.
 *
 * Oat & Obsidian dark theme (vault exterior). Uses explicit color
 * classes since ThemeProvider will default to light for unknown routes.
 *
 * Server Component — no 'use client' needed.
 *
 * Sprint 204: Phase XXVII — Next.js App Router Hardening
 */
export default function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-obsidian flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* 404 badge */}
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-obsidian-700/60 border border-oatmeal-200/10 mb-6">
          <span className="text-3xl font-mono font-bold text-oatmeal-400">404</span>
        </div>

        <h1 className="text-2xl font-serif font-bold text-oatmeal-200 mb-3">
          Page not found
        </h1>

        <p className="text-oatmeal-400 mb-8 leading-relaxed">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
          If you believe this is an error, please contact support.
        </p>

        <div className="flex gap-3 justify-center">
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-sage-500 hover:bg-sage-600 text-oatmeal-200 font-bold text-sm rounded-lg transition-colors duration-200"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Back to Home
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-transparent border border-oatmeal-200/20 hover:border-oatmeal-200/40 text-oatmeal-200 font-bold text-sm rounded-lg transition-colors duration-200"
          >
            Go to Login
          </Link>
        </div>
      </div>
    </div>
  )
}
