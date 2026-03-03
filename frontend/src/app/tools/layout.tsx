'use client'

/**
 * Tools Layout — AuthenticatedShell + Engagement integration.
 *
 * Wraps all /tools/* pages with:
 * 1. AuthenticatedShell (UnifiedToolbar + VerificationBanner)
 * 2. EngagementProvider + banner + toast (Sprint 103)
 * 3. SonificationToggle (Sprint 406)
 *
 * Sprint 475: Replaced ToolNav with AuthenticatedShell.
 */

import { Suspense, ReactNode } from 'react'
import { EngagementProvider, useEngagementContext } from '@/contexts/EngagementContext'
import { EngagementBanner, ToolLinkToast } from '@/components/engagement'
import { SonificationToggle } from '@/components/shared/SonificationToggle'
import { AuthenticatedShell } from '@/components/shell'

function ToolsLayoutInner({ children }: { children: ReactNode }) {
  const { activeEngagement, clearEngagement, toastMessage, dismissToast } = useEngagementContext()

  return (
    <AuthenticatedShell>
      <EngagementBanner
        activeEngagement={activeEngagement}
        onUnlink={clearEngagement}
      />
      {children}
      <ToolLinkToast
        message={toastMessage}
        onDismiss={dismissToast}
      />
      <div className="fixed bottom-4 right-4 z-10">
        <SonificationToggle />
      </div>
    </AuthenticatedShell>
  )
}

export default function ToolsLayout({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={null}>
      <EngagementProvider>
        <ToolsLayoutInner>
          {children}
        </ToolsLayoutInner>
      </EngagementProvider>
    </Suspense>
  )
}
