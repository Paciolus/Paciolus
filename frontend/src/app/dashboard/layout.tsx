'use client'

/**
 * Dashboard Layout — Sprint 475
 *
 * Wraps /dashboard with AuthenticatedShell.
 */

import { type ReactNode } from 'react'
import { AuthenticatedShell } from '@/components/shell'

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <AuthenticatedShell>
      {children}
    </AuthenticatedShell>
  )
}
