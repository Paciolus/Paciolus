'use client'

import { AuthProvider } from '@/context/AuthContext'
import { DiagnosticProvider } from '@/context/DiagnosticContext'
import { ErrorBoundary } from '@/components/ErrorBoundary'

/**
 * Providers - Day 13 (Updated Sprint 25)
 *
 * Client-side providers wrapper for Next.js App Router.
 * Wraps children with all necessary context providers.
 *
 * Sprint 25: Added global ErrorBoundary for stability.
 */
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <DiagnosticProvider>
          {children}
        </DiagnosticProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}
