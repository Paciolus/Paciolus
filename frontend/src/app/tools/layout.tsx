'use client'

/**
 * Tools Layout — Sprint 103: Tool-Engagement Integration
 *
 * Wraps all /tools/* pages in EngagementProvider + banner + toast.
 * Reads ?engagement=X from URL to auto-link tool runs to a workspace.
 */

import { Suspense, ReactNode } from 'react'
import { EngagementProvider } from '@/contexts/EngagementContext'
import { useEngagementContext } from '@/contexts/EngagementContext'
import { EngagementBanner, ToolLinkToast } from '@/components/engagement'

function ToolsLayoutInner({ children }: { children: ReactNode }) {
  const { activeEngagement, clearEngagement, toastMessage, dismissToast } = useEngagementContext()

  return (
    <>
      <EngagementBanner
        activeEngagement={activeEngagement}
        onUnlink={clearEngagement}
      />
      {children}
      <ToolLinkToast
        message={toastMessage}
        onDismiss={dismissToast}
      />
    </>
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
