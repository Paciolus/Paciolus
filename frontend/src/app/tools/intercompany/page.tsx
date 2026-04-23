'use client'

/**
 * Intercompany Elimination — Sprint 689c.
 *
 * Standalone tool page for multi-entity consolidation. Accepts a
 * single long-format CSV (one row per account per entity) and pivots
 * client-side into the per-entity JSON payload the backend expects.
 * Renders the consolidation worksheet, proposed elimination journal
 * entries, and a mismatch detail list.
 *
 * Tier gating: Free tier is blocked client-side by UpgradeGate and
 * server-side by the Sprint 689c enforce_tool_access check. All paid
 * tiers (Solo / Professional / Enterprise) have access.
 */

import { useAuthSession } from '@/contexts/AuthSessionContext'
import { IntercompanyFileUpload } from '@/components/intercompany/IntercompanyFileUpload'
import { IntercompanyResults } from '@/components/intercompany/IntercompanyResults'
import {
  Citation,
  CitationFooter,
  DisclaimerBox,
  GuestCTA,
  UnverifiedCTA,
  UpgradeGate,
} from '@/components/shared'
import { useIntercompanyElimination } from '@/hooks/useIntercompanyElimination'

export default function IntercompanyEliminationPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuthSession()
  const isVerified = user?.is_verified !== false
  const { status, result, error, analyze, exportCsv } = useIntercompanyElimination()

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="page-container">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-50 border border-sage-200 mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-sage-700 text-sm font-sans font-medium">
              ASC 810 / IFRS 10 / ISA 600
            </span>
          </div>
          <h1 className="type-tool-title mb-3">Intercompany Elimination</h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Upload a multi-entity trial balance to match reciprocal intercompany balances, propose
            elimination journal entries, and produce a consolidation worksheet &mdash; with mismatch
            detection for unreciprocated, off-amount, and same-direction entries.
          </p>
        </div>

        {!authLoading && !isAuthenticated && (
          <GuestCTA description="Intercompany Elimination requires a verified account. Sign in or create an account to continue." />
        )}

        {!authLoading && isAuthenticated && !isVerified && <UnverifiedCTA />}

        {isAuthenticated && isVerified && (
          <UpgradeGate toolName="intercompany_elimination">
            <div className="max-w-5xl mx-auto space-y-6">
              <IntercompanyFileUpload
                onAnalyze={analyze}
                onExport={exportCsv}
                loading={status === 'loading'}
              />

              {error && (
                <div className="p-4 rounded-lg border border-clay-200 bg-clay-50 text-clay-700 text-sm font-sans">
                  {error}
                </div>
              )}

              {result && <IntercompanyResults result={result} />}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Automatic Direction Inference</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Account names are parsed into intercompany directions (receivable, payable, revenue,
                    expense, investment). Manual overrides can be added by setting the counterparty column
                    on any standalone-looking account.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Configurable Tolerance</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Pairs reconcile when the net residual falls within the supplied tolerance
                    (default <code className="font-mono">$1.00</code>). Values outside tolerance are
                    reported as <code className="font-mono">amount_mismatch</code> rather than silently netted.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Zero-Storage</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Uploaded trial balances are parsed in-browser, posted as JSON, consolidated in
                    memory, and discarded after the response &mdash; consistent with the platform&apos;s
                    Zero-Storage architecture.
                  </p>
                </div>
              </div>

              <DisclaimerBox>
                The consolidation output applies elimination entries on matched reciprocal intercompany
                balances per <Citation code="ASC 810" /> and <Citation code="IFRS 10" />. Identification
                of the reporting group, determination of controlling interests, and accounting policy
                harmonization remain auditor/management judgments; mismatches surfaced here indicate
                candidates for engagement-team follow-up rather than control deficiencies under
                <Citation code="ISA 600" /> group audits.
              </DisclaimerBox>
              <CitationFooter standards={['ASC 810', 'IFRS 10', 'ISA 600']} />
            </div>
          </UpgradeGate>
        )}
      </div>
    </main>
  )
}
