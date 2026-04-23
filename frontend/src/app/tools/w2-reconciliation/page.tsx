'use client'

/**
 * W-2 / W-3 Reconciliation — Sprint 689d.
 *
 * Standalone tool page. Accepts three CSVs (payroll YTD + optional
 * W-2 drafts + optional Form 941 quarterlies), posts to
 * /audit/w2-reconciliation, and renders discrepancies, 941 mismatches,
 * and the W-3 totals. Free tier blocked by UpgradeGate + backend gate
 * added in Sprint 689d.
 */

import { useAuthSession } from '@/contexts/AuthSessionContext'
import {
  CitationFooter,
  DisclaimerBox,
  GuestCTA,
  UnverifiedCTA,
  UpgradeGate,
} from '@/components/shared'
import { W2FileUpload } from '@/components/w2Reconciliation/W2FileUpload'
import { W2Results } from '@/components/w2Reconciliation/W2Results'
import { useW2Reconciliation } from '@/hooks/useW2Reconciliation'

export default function W2ReconciliationPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuthSession()
  const isVerified = user?.is_verified !== false
  const { status, result, error, analyze, exportCsv } = useW2Reconciliation()

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="page-container">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-50 border border-sage-200 mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-sage-700 text-sm font-sans font-medium">
              IRC &sect;6051 / Form W-2 &middot; W-3 &middot; 941
            </span>
          </div>
          <h1 className="type-tool-title mb-3">W-2 / W-3 Reconciliation</h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Reconcile payroll year-to-date totals to draft W-2s and Form 941 quarterly filings before
            year-end filing. Detects per-employee box mismatches, SS wage-base overages, retirement plan
            limit breaches, and 941-to-W-2 reconciliation gaps.
          </p>
        </div>

        {!authLoading && !isAuthenticated && (
          <GuestCTA description="W-2 / W-3 Reconciliation requires a verified account. Sign in or create an account to continue." />
        )}

        {!authLoading && isAuthenticated && !isVerified && <UnverifiedCTA />}

        {isAuthenticated && isVerified && (
          <UpgradeGate toolName="w2_reconciliation">
            <div className="max-w-5xl mx-auto space-y-6">
              <W2FileUpload
                onAnalyze={analyze}
                onExport={exportCsv}
                loading={status === 'loading'}
              />

              {error && (
                <div className="p-4 rounded-lg border border-clay-200 bg-clay-50 text-clay-700 text-sm font-sans">
                  {error}
                </div>
              )}

              {result && <W2Results result={result} />}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Per-Box Reconciliation</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Compares payroll YTD against draft W-2 Box 1–6 plus Box 12 codes W (HSA), D (401k),
                    and S (SIMPLE IRA). Severity reflects the size of the box-level delta relative to
                    your configured tolerance.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Form 941 Tie-Out</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Rolls quarterly 941 totals into a YTD comparison against W-2 aggregates &mdash;
                    flags the common &ldquo;941 over-reported, W-2 under-reported&rdquo; pattern that
                    triggers IRS CP2100B notices.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Zero-Storage</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    CSVs are parsed in-browser, posted as JSON, reconciled in memory, and discarded
                    after the response. No payroll data persists to long-term storage.
                  </p>
                </div>
              </div>

              <DisclaimerBox>
                Discrepancies surfaced here identify candidates for review before filing W-2 / W-3 with
                SSA and the matching 941 with the IRS. Classification of any error as a material
                misstatement, or the decision to file Form W-2c / 941-X, remains an auditor or preparer
                judgment per IRC &sect;6051 and the Form 941 instructions.
              </DisclaimerBox>
              <CitationFooter standards={[]} />
            </div>
          </UpgradeGate>
        )}
      </div>
    </main>
  )
}
