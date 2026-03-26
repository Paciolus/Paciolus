'use client'

/**
 * Internal Admin Console Layout — Sprint 590
 *
 * Superadmin-only layout. Redirects non-superadmin users to dashboard.
 */

import { AuthenticatedShell } from '@/components/shell'

export default function InternalAdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <AuthenticatedShell>{children}</AuthenticatedShell>
}
