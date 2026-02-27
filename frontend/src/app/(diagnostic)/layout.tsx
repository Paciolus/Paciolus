'use client'

import { DiagnosticProvider } from '@/contexts/DiagnosticContext'

/**
 * Diagnostic Layout — wraps /flux and /recon in shared DiagnosticProvider.
 *
 * Scoped from global providers.tsx so only these two pages
 * pay the cost of diagnostic state. URL-transparent route group.
 *
 * Sprint 208: Phase XXVII — Provider Scoping
 */
export default function DiagnosticLayout({ children }: { children: React.ReactNode }) {
  return (
    <DiagnosticProvider>
      {children}
    </DiagnosticProvider>
  )
}
