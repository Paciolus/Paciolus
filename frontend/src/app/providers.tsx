'use client'

import { AuthProvider } from '@/contexts/AuthContext'
import { DiagnosticProvider } from '@/contexts/DiagnosticContext'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ThemeProvider } from '@/components/ThemeProvider'

/**
 * Providers — Client-side provider chain for Next.js App Router.
 *
 * Order: ErrorBoundary → ThemeProvider → AuthProvider → DiagnosticProvider
 * ThemeProvider sets data-theme on <html> based on route (Sprint 123).
 */
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <DiagnosticProvider>
            {children}
          </DiagnosticProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  )
}
