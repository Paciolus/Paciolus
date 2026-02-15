'use client'

import { AuthProvider } from '@/contexts/AuthContext'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ThemeProvider } from '@/components/ThemeProvider'
import { MotionConfig } from 'framer-motion'

/**
 * Providers — Client-side provider chain for Next.js App Router.
 *
 * Order: ErrorBoundary → ThemeProvider → AuthProvider
 * ThemeProvider sets data-theme on <html> based on route (Sprint 123).
 *
 * DiagnosticProvider scoped locally to flux + recon pages (Sprint 208).
 */
export function Providers({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <ErrorBoundary>
      <MotionConfig reducedMotion="user">
        <ThemeProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </ThemeProvider>
      </MotionConfig>
    </ErrorBoundary>
  )
}
