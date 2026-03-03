'use client'

/**
 * History Layout — Sprint 475
 *
 * Wraps /history with AuthenticatedShell.
 * Replaces bespoke inline header.
 */

import { type ReactNode } from 'react'
import { AuthenticatedShell } from '@/components/shell'

export default function HistoryLayout({ children }: { children: ReactNode }) {
  return (
    <AuthenticatedShell>
      {children}
    </AuthenticatedShell>
  )
}
