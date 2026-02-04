'use client'

import { AuthProvider } from '@/context/AuthContext'
import { DiagnosticProvider } from '@/context/DiagnosticContext'

/**
 * Providers - Day 13
 *
 * Client-side providers wrapper for Next.js App Router.
 * Wraps children with all necessary context providers.
 */
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <DiagnosticProvider>
        {children}
      </DiagnosticProvider>
    </AuthProvider>
  )
}
