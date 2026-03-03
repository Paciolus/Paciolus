'use client'

import { DiagnosticProvider } from '@/contexts/DiagnosticContext'
import { AuthenticatedShell } from '@/components/shell'

/**
 * Diagnostic Layout — wraps /flux and /recon in shared DiagnosticProvider.
 *
 * Sprint 208: Phase XXVII — Provider Scoping
 * Sprint 475: Added AuthenticatedShell wrapper.
 */
export default function DiagnosticLayout({ children }: { children: React.ReactNode }) {
  return (
    <DiagnosticProvider>
      <AuthenticatedShell>
        {children}
      </AuthenticatedShell>
    </DiagnosticProvider>
  )
}
