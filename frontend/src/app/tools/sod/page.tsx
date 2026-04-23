'use client'

/**
 * Segregation of Duties Checker — Sprint 689b.
 *
 * Standalone Enterprise-only tool page. Accepts a dual CSV upload
 * (user-to-role + role-to-permission matrices), parses client-side,
 * and posts JSON to /audit/sod/analyze. Results render inline with an
 * optional CSV export.
 *
 * Enterprise gating: the standard UpgradeGate only blocks Free tier, so
 * this page layers FeatureGate(feature="sod_checker") on top to block
 * Solo/Professional as well — matching the backend 403 payload.
 */

import { useEffect } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import {
  Citation,
  CitationFooter,
  DisclaimerBox,
  GuestCTA,
  UnverifiedCTA,
} from '@/components/shared'
import { FeatureGate } from '@/components/shared/FeatureGate'
import { SODFileUpload } from '@/components/sod/SODFileUpload'
import { SODResults } from '@/components/sod/SODResults'
import { SODRulesReference } from '@/components/sod/SODRulesReference'
import { useSOD } from '@/hooks/useSOD'

export default function SODPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuthSession()
  const isVerified = user?.is_verified !== false
  const isEnterprise = user?.tier === 'enterprise'
  const { status, result, rules, error, analyze, exportCsv, loadRules } = useSOD()

  useEffect(() => {
    if (isAuthenticated && isVerified && isEnterprise) {
      loadRules()
    }
  }, [isAuthenticated, isVerified, isEnterprise, loadRules])

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="page-container">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-50 border border-sage-200 mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-sage-700 text-sm font-sans font-medium">
              SOC 1 / AICPA / COSO 2013
            </span>
          </div>
          <h1 className="type-tool-title mb-3">Segregation of Duties Checker</h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Upload your user-to-role and role-to-permission matrices to detect incompatible access
            combinations across AP, revenue, payroll, journal entry, inventory, and system administration.
            Per-user risk ranking with mitigating control suggestions.
          </p>
        </div>

        {!authLoading && !isAuthenticated && (
          <GuestCTA description="The SoD Checker requires a verified Enterprise account. Sign in or create an account to continue." />
        )}

        {!authLoading && isAuthenticated && !isVerified && <UnverifiedCTA />}

        {isAuthenticated && isVerified && (
          <FeatureGate
            feature="sod_checker"
            message="The Segregation of Duties Checker is available on the Enterprise plan. Upgrade to analyze user-role matrices against the hardcoded SoD rule library with per-user risk ranking."
          >
            <div className="max-w-5xl mx-auto space-y-6">
              <SODFileUpload
                onAnalyze={analyze}
                onExport={exportCsv}
                loading={status === 'loading'}
              />

              {error && (
                <div className="p-4 rounded-lg border border-clay-200 bg-clay-50 text-clay-700 text-sm font-sans">
                  {error}
                </div>
              )}

              {result && <SODResults result={result} />}

              <SODRulesReference rules={rules} />

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Hardcoded Rule Library</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Twelve standards-backed SoD rules spanning AP, journal entry, payroll, revenue, inventory,
                    and system administration. Custom rules supplied at request time are additive.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Per-User Risk Ranking</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Risk score = <code className="font-mono">3&times;high + 2&times;medium + 1&times;low</code>;
                    tier thresholds: <code className="font-mono">&ge;6 high</code>,{' '}
                    <code className="font-mono">&ge;3 moderate</code>, otherwise <code className="font-mono">low</code>.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Zero-Storage</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Matrices are processed in-memory and discarded after analysis &mdash; consistent
                    with the platform&apos;s Zero-Storage architecture for privileged access data.
                  </p>
                </div>
              </div>

              <DisclaimerBox>
                The SoD Checker evaluates permission combinations against a standards-informed rule library
                derived from <Citation code="SOC 1" />, AICPA segregation-of-incompatible-duties guidance,
                and <Citation code="COSO 2013" /> Principle 10 (selects and develops control activities).
                Detected conflicts are candidates for auditor review; suitability of compensating controls
                and the classification of any deficiency remain a judgment call per
                ISA 265 / AU-C 265.
              </DisclaimerBox>
              <CitationFooter standards={['SOC 1', 'COSO 2013']} />
            </div>
          </FeatureGate>
        )}
      </div>
    </main>
  )
}
