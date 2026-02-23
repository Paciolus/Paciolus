'use client'

import { MotionConfig } from 'framer-motion'
import { AuthProvider } from '@/contexts/AuthContext'
import { CommandPaletteProvider } from '@/contexts/CommandPaletteContext'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { GlobalCommandPalette } from '@/components/shared'
import { ThemeProvider } from '@/components/ThemeProvider'

/**
 * Providers — Client-side provider chain for Next.js App Router.
 *
 * Order: ErrorBoundary → ThemeProvider → AuthProvider → CommandPaletteProvider
 * ThemeProvider sets data-theme on <html> based on route (Sprint 123).
 * CommandPaletteProvider must be inside AuthProvider (needs user context) (Sprint 396).
 *
 * DiagnosticProvider scoped locally to flux + recon pages (Sprint 208).
 */
export function Providers({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <ErrorBoundary>
      <MotionConfig reducedMotion="user">
        <ThemeProvider>
          <AuthProvider>
            <CommandPaletteProvider>
              {children}
              <GlobalCommandPalette />
            </CommandPaletteProvider>
          </AuthProvider>
        </ThemeProvider>
      </MotionConfig>
    </ErrorBoundary>
  )
}
