'use client'

/**
 * Settings Layout — Sprint 475
 *
 * Wraps all /settings/* pages with AuthenticatedShell.
 * Replaces per-page inline nav bars.
 */

import { type ReactNode } from 'react'
import { AuthenticatedShell } from '@/components/shell'

export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <AuthenticatedShell>
      {children}
    </AuthenticatedShell>
  )
}
