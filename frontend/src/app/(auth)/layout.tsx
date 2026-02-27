'use client'

import Link from 'next/link'

/**
 * Auth Route Group Layout — shared centering + "Back to Paciolus" footer.
 *
 * Wraps: login, register, verify-email, verification-pending.
 * Route groups are URL-transparent — paths remain /login, /register, etc.
 *
 * Dark theme (vault exterior) applied via bg-gradient-obsidian.
 *
 * Sprint 206: Phase XXVII — Auth Route Group
 */
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <main className="min-h-screen bg-gradient-obsidian flex items-center justify-center p-6">
      <div className="relative z-10 w-full max-w-md">
        {children}
        <div className="mt-6 text-center">
          <Link
            href="/"
            className="text-oatmeal-500 hover:text-oatmeal-400 text-sm font-sans transition-colors inline-flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Paciolus
          </Link>
        </div>
      </div>
    </main>
  )
}
