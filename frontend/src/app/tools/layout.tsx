'use client'

/**
 * Tools Layout — shared ToolNav + VerificationBanner + Engagement integration.
 *
 * Wraps all /tools/* pages with:
 * 1. ToolNav (derives currentTool from pathname)
 * 2. EngagementProvider + banner + toast (Sprint 103)
 * 3. VerificationBanner (self-contained, shows only for unverified users)
 *
 * Sprint 207: Consolidation — ToolNav + VerificationBanner moved from 11 pages.
 */

import { Suspense, ReactNode } from 'react'
import { usePathname } from 'next/navigation'
import { EngagementProvider, useEngagementContext } from '@/contexts/EngagementContext'
import { EngagementBanner, ToolLinkToast } from '@/components/engagement'
import { ToolNav, type ToolKey } from '@/components/shared'
import { VerificationBanner } from '@/components/auth'

/** Map URL segment → ToolKey for ToolNav highlighting */
const SEGMENT_TO_TOOL: Record<string, ToolKey> = {
  'trial-balance': 'tb-diagnostics',
  'multi-period': 'multi-period',
  'journal-entry-testing': 'je-testing',
  'ap-testing': 'ap-testing',
  'bank-rec': 'bank-rec',
  'payroll-testing': 'payroll-testing',
  'three-way-match': 'three-way-match',
  'revenue-testing': 'revenue-testing',
  'ar-aging': 'ar-aging',
  'fixed-assets': 'fixed-assets',
  'inventory-testing': 'inventory-testing',
  'statistical-sampling': 'statistical-sampling',
}

function ToolsLayoutInner({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const { activeEngagement, clearEngagement, toastMessage, dismissToast } = useEngagementContext()

  const segment = pathname.split('/').pop() || ''
  const currentTool = SEGMENT_TO_TOOL[segment] || 'tb-diagnostics'

  return (
    <>
      <ToolNav currentTool={currentTool} showBrandText={segment === 'trial-balance'} />
      <EngagementBanner
        activeEngagement={activeEngagement}
        onUnlink={clearEngagement}
      />
      <VerificationBanner />
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
