'use client'

/**
 * UpgradeGate — Sprint 368.
 *
 * Wraps gated content with an upgrade CTA when the user's tier is insufficient.
 * Shows children normally when the user has access.
 */

import { useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'
import { trackEvent } from '@/utils/telemetry'

// Tools available per tier (mirrors backend entitlements)
const TIER_TOOLS: Record<string, Set<string>> = {
  free: new Set(['trial_balance', 'flux_analysis']),
  starter: new Set([
    'trial_balance', 'flux_analysis', 'journal_entry_testing',
    'multi_period', 'prior_period', 'adjustments',
  ]),
  // professional, team, enterprise: all tools (empty set = unrestricted)
}

interface UpgradeGateProps {
  /** Tool name to check access for */
  toolName: string
  /** Content to render when access is granted */
  children: React.ReactNode
  /** Optional custom message */
  message?: string
}

export function UpgradeGate({ toolName, children, message }: UpgradeGateProps) {
  const { user } = useAuth()
  const tier = user?.tier ?? 'free'

  // Check if the tier has restricted tools
  const allowedTools = TIER_TOOLS[tier]
  const hasAccess = !allowedTools || allowedTools.has(toolName)

  useEffect(() => {
    if (!hasAccess) {
      trackEvent('view_upgrade_gate', { tool: toolName, tier })
    }
  }, [hasAccess, toolName, tier])

  if (hasAccess) {
    return <>{children}</>
  }

  return (
    <div className="bg-surface-card border border-theme rounded-lg p-8 text-center">
      <div className="mx-auto max-w-md">
        <h3 className="font-serif text-xl text-content-primary mb-3">
          Upgrade Required
        </h3>
        <p className="text-content-secondary mb-6">
          {message ?? `This tool is not available on your current plan. Upgrade to access all diagnostic tools.`}
        </p>
        <Link
          href="/pricing"
          onClick={() => trackEvent('click_upgrade_from_gate', { tool: toolName, tier })}
          className="inline-block px-6 py-3 bg-sage-600 text-white rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors"
        >
          View Plans
        </Link>
        <p className="text-content-muted text-sm mt-4">
          Current plan: <span className="capitalize font-medium">{tier}</span>
        </p>
      </div>
    </div>
  )
}
