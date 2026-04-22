'use client'

/**
 * Typography Preview Layout — Sprint 703 pre-work
 *
 * Authenticated-only wrapper for the typography decision route.
 * Shares the AuthenticatedShell with the rest of /internal so the
 * auth redirect + session handling is consistent.
 */

import { AuthenticatedShell } from '@/components/shell'

export default function TypographyPreviewLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <AuthenticatedShell>{children}</AuthenticatedShell>
}
