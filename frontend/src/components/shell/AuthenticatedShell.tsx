'use client'

/**
 * AuthenticatedShell — Sprint 475
 *
 * Unified wrapper for all authenticated pages. Renders the
 * UnifiedToolbar (fixed top) and applies content offset so
 * individual pages don't need padding-top.
 *
 * Also renders VerificationBanner for unverified users.
 */

import { type ReactNode } from 'react'
import { VerificationBanner } from '@/components/auth'
import { UnifiedToolbar } from '@/components/shared/UnifiedToolbar'

interface AuthenticatedShellProps {
  children: ReactNode
}

export function AuthenticatedShell({ children }: AuthenticatedShellProps) {
  return (
    <>
      <UnifiedToolbar />
      <div style={{ paddingTop: 'var(--toolbar-height, 56px)' }}>
        <VerificationBanner />
        {children}
      </div>
    </>
  )
}
