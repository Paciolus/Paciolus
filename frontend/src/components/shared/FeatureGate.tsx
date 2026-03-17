'use client'

/**
 * FeatureGate — Phase LXIX Pricing v3.
 *
 * Gates feature-level access (not tool access — use UpgradeGate for tools).
 * Checks whether the user's tier meets the minimum required for a feature.
 *
 * Features:
 *   export_sharing    — Professional+
 *   activity_logs     — Professional+
 *   admin_dashboard   — Professional+
 *   bulk_upload       — Enterprise
 *   custom_branding   — Enterprise
 */

import { useEffect } from 'react'
import Link from 'next/link'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { trackEvent } from '@/utils/telemetry'

type FeatureName =
  | 'export_sharing'
  | 'activity_logs'
  | 'admin_dashboard'
  | 'bulk_upload'
  | 'custom_branding'

const TIER_ORDER = ['free', 'solo', 'professional', 'enterprise'] as const

const FEATURE_MIN_TIER: Record<FeatureName, typeof TIER_ORDER[number]> = {
  export_sharing: 'professional',
  activity_logs: 'professional',
  admin_dashboard: 'professional',
  bulk_upload: 'enterprise',
  custom_branding: 'enterprise',
}

const FEATURE_DISPLAY_NAMES: Record<FeatureName, string> = {
  export_sharing: 'Export Sharing',
  activity_logs: 'Activity Logs',
  admin_dashboard: 'Admin Dashboard',
  bulk_upload: 'Bulk Upload',
  custom_branding: 'Custom PDF Branding',
}

const TIER_DISPLAY_NAMES: Record<string, string> = {
  free: 'Free',
  solo: 'Solo',
  professional: 'Professional',
  enterprise: 'Enterprise',
}

interface FeatureGateProps {
  /** Feature to check access for */
  feature: FeatureName
  /** Content to render when access is granted */
  children: React.ReactNode
  /** Optional custom message */
  message?: string
  /** If true, render nothing instead of the upgrade CTA (for hiding UI elements) */
  hidden?: boolean
}

export function FeatureGate({ feature, children, message, hidden }: FeatureGateProps) {
  const { user } = useAuthSession()
  const tier = user?.tier ?? 'free'

  const tierIdx = TIER_ORDER.indexOf(tier as typeof TIER_ORDER[number])
  const minTierIdx = TIER_ORDER.indexOf(FEATURE_MIN_TIER[feature])
  const hasAccess = tierIdx >= minTierIdx

  useEffect(() => {
    if (!hasAccess) {
      trackEvent('view_feature_gate', { feature, tier })
    }
  }, [hasAccess, feature, tier])

  if (hasAccess) {
    return <>{children}</>
  }

  if (hidden) {
    return null
  }

  const requiredTier = FEATURE_MIN_TIER[feature]

  return (
    <div className="bg-surface-card border border-theme rounded-lg p-8 text-center">
      <div className="mx-auto max-w-md">
        <h3 className="font-serif text-xl text-content-primary mb-3">
          {FEATURE_DISPLAY_NAMES[feature]}
        </h3>
        <p className="text-content-secondary mb-6">
          {message ?? `This feature requires a ${TIER_DISPLAY_NAMES[requiredTier]} plan or higher.`}
        </p>
        <Link
          href="/pricing"
          onClick={() => trackEvent('click_upgrade_from_feature_gate', { feature, tier })}
          className="inline-block px-6 py-3 bg-sage-600 text-white rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors"
        >
          View Plans
        </Link>
        <p className="text-content-muted text-sm mt-4">
          Current plan: <span className="font-medium">{TIER_DISPLAY_NAMES[tier] ?? tier}</span>
        </p>
      </div>
    </div>
  )
}
