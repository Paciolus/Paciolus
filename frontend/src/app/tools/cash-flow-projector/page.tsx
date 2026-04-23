'use client'

/**
 * Cash Flow Projector — Sprint 689g.
 *
 * Standalone tool page. Form input (AR + AP aging buckets + recurring
 * flows). Backend returns a 90-day projection across base / stress /
 * best scenarios; UI surfaces scenario-level summaries and the 30/60/90
 * horizon grid. Daily detail lives in the CSV export.
 */

import { useAuthSession } from '@/contexts/AuthSessionContext'
import { CashFlowForm } from '@/components/cashFlowProjector/CashFlowForm'
import { CashFlowResults } from '@/components/cashFlowProjector/CashFlowResults'
import {
  CitationFooter,
  DisclaimerBox,
  GuestCTA,
  UnverifiedCTA,
  UpgradeGate,
} from '@/components/shared'
import { useCashFlowProjector } from '@/hooks/useCashFlowProjector'

export default function CashFlowProjectorPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuthSession()
  const isVerified = user?.is_verified !== false
  const { status, result, error, project, exportCsv } = useCashFlowProjector()

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="page-container">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-50 border border-sage-200 mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-sage-700 text-sm font-sans font-medium">
              Direct-method 90-day forecast
            </span>
          </div>
          <h1 className="type-tool-title mb-3">Cash Flow Projector</h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Project cash position 90 days forward across base, stress, and best scenarios. Uses AR and
            AP aging buckets plus recurring payroll / rent / subscription flows to surface liquidity
            breaches and collection / deferral priorities.
          </p>
        </div>

        {!authLoading && !isAuthenticated && (
          <GuestCTA description="Cash Flow Projector requires a verified account. Sign in or create an account to continue." />
        )}

        {!authLoading && isAuthenticated && !isVerified && <UnverifiedCTA />}

        {isAuthenticated && isVerified && (
          <UpgradeGate toolName="cash_flow_projector">
            <div className="max-w-5xl mx-auto space-y-6">
              <CashFlowForm
                onProject={project}
                onExport={exportCsv}
                loading={status === 'loading'}
              />

              {error && (
                <div className="p-4 rounded-lg border border-clay-200 bg-clay-50 text-clay-700 text-sm font-sans">
                  {error}
                </div>
              )}

              {result && <CashFlowResults result={result} />}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Three-Scenario Forecast</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    The engine runs base, stress, and best scenarios in parallel &mdash; each with its
                    own AR collection and AP deferral assumptions &mdash; so you see the envelope of
                    plausible outcomes, not a single point estimate.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Min-Safe-Cash Alerts</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Provide a minimum operating cash threshold and any scenario that breaches it is
                    flagged with the first-breach day so you can size a revolver draw or defer a
                    planned outflow.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Zero-Storage</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Inputs are posted as JSON, the 90-day forecast computes in memory, and results
                    are discarded after the response &mdash; consistent with the platform&apos;s
                    Zero-Storage architecture.
                  </p>
                </div>
              </div>

              <DisclaimerBox>
                Projections here use mechanical AR collection and AP payment curves derived from the
                supplied aging buckets. Business-judgment overrides (customer-specific risk, vendor
                negotiations, revolver availability) are not modelled; treat the output as a liquidity
                sensitivity, not a budget.
              </DisclaimerBox>
              <CitationFooter standards={[]} />
            </div>
          </UpgradeGate>
        )}
      </div>
    </main>
  )
}
