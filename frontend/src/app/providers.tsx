'use client'

import type { ReactElement } from 'react'
import dynamic from 'next/dynamic'
import { MotionConfig } from 'framer-motion'
import { AuthProvider } from '@/contexts/AuthContext'
import { CommandPaletteProvider } from '@/contexts/CommandPaletteContext'
import { ToastProvider } from '@/contexts/ToastContext'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ToastContainer } from '@/components/shared'
import { ImpersonationBanner } from '@/components/shared/ImpersonationBanner'
import { ThemeProvider } from '@/components/ThemeProvider'

// Sprint 772a: GlobalCommandPalette mounts on every route but only
// renders when isOpen + isAuthenticated. The Cmd+K listener lives in
// CommandPaletteContext (eagerly mounted) so the palette UI itself can
// be split into a separate chunk — loaded async on every page, not
// blocking first paint of marketing/auth/error routes.
const GlobalCommandPalette = dynamic(
  () => import('@/components/shared/CommandPalette/GlobalCommandPalette').then(m => ({ default: m.GlobalCommandPalette })),
  { ssr: false },
)

/**
 * Providers — Client-side provider chain for Next.js App Router.
 *
 * Order: ErrorBoundary → ThemeProvider → AuthProvider → CommandPaletteProvider
 * ThemeProvider sets data-theme on <html> based on route (Sprint 123).
 * CommandPaletteProvider must be inside AuthProvider (needs user context) (Sprint 396).
 *
 * DiagnosticProvider scoped locally to flux + recon pages (Sprint 208).
 */
export function Providers({ children }: { children: React.ReactNode }): ReactElement {
  return (
    <ErrorBoundary>
      <MotionConfig reducedMotion="user">
        <ThemeProvider>
          <AuthProvider>
            <ToastProvider>
              <CommandPaletteProvider>
                <ImpersonationBanner />
                {children}
                <GlobalCommandPalette />
                <ToastContainer />
              </CommandPaletteProvider>
            </ToastProvider>
          </AuthProvider>
        </ThemeProvider>
      </MotionConfig>
    </ErrorBoundary>
  )
}
