'use client'

/**
 * Multi-Currency Conversion — Sprint 689a
 *
 * Standalone page for managing exchange rate tables outside the TB upload flow.
 * Wraps the existing `CurrencyRatePanel` (defaultOpen) so paid tiers can
 * establish rates ahead of a multi-currency TB diagnostic run.
 *
 * Conversion itself still runs during TB upload — this page only manages the
 * session-scoped rate table the conversion engine consumes.
 */

import { useAuthSession } from '@/contexts/AuthSessionContext'
import { CurrencyRatePanel } from '@/components/currencyRates/CurrencyRatePanel'
import {
  GuestCTA,
  UnverifiedCTA,
  UpgradeGate,
  DisclaimerBox,
  Citation,
  CitationFooter,
} from '@/components/shared'

export default function MultiCurrencyPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuthSession()
  const isVerified = user?.is_verified !== false

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="page-container">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-50 border border-sage-200 mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-sage-700 text-sm font-sans font-medium">
              IAS 21 / ASC 830 Foreign Currency
            </span>
          </div>
          <h1 className="type-tool-title mb-3">Multi-Currency Conversion</h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Upload an exchange-rate table or enter rates manually to convert foreign-currency trial
            balances into a single presentation currency &mdash; with ISO 4217 validation, cohort-aware
            staleness detection, and defense-in-depth rate validation.
          </p>
        </div>

        {!authLoading && !isAuthenticated && (
          <GuestCTA description="Multi-Currency Conversion requires a verified account. Sign in or create an account to manage exchange rates." />
        )}

        {!authLoading && isAuthenticated && !isVerified && <UnverifiedCTA />}

        {isAuthenticated && isVerified && (
          <UpgradeGate toolName="currency_rates">
            <div className="max-w-3xl mx-auto">
              <CurrencyRatePanel defaultOpen />

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-10">
                <div className="theme-card p-6">
                  <div className="w-10 h-10 bg-sage-50 rounded-lg flex items-center justify-center mb-3">
                    <svg className="w-5 h-5 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="font-serif text-content-primary text-sm mb-2">ISO 4217 Validation</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Every currency code is checked against the ISO 4217 registry before it reaches the
                    conversion engine &mdash; typos and retired codes are rejected at upload.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <div className="w-10 h-10 bg-sage-50 rounded-lg flex items-center justify-center mb-3">
                    <svg className="w-5 h-5 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="font-serif text-content-primary text-sm mb-2">Staleness Detection</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Rates older than the configured threshold &mdash; or out of cohort with the newest rate
                    in the table &mdash; surface as <code className="font-mono">stale_rate</code> flags on
                    the affected accounts.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <div className="w-10 h-10 bg-sage-50 rounded-lg flex items-center justify-center mb-3">
                    <svg className="w-5 h-5 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                  <h3 className="font-serif text-content-primary text-sm mb-2">Session-Scoped Rates</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Rate tables are stored in the user&apos;s session only and never persisted to long-term
                    storage, consistent with the Zero-Storage architecture applied to financial data.
                  </p>
                </div>
              </div>

              <DisclaimerBox>
                Multi-Currency Conversion applies closing-rate translation to account balances and
                surfaces unconverted items &mdash; missing rates, unknown currencies, zero/negative
                rates, and stale cohort rates &mdash; for auditor review. Historical-rate and
                average-rate translation per <Citation code="IAS 21" /> &sect;39 and{' '}
                <Citation code="ASC 830" />-30 are not applied automatically; select an appropriate
                rate per the engagement&apos;s functional-currency determination.
              </DisclaimerBox>
              <CitationFooter standards={['IAS 21', 'ASC 830']} />
            </div>
          </UpgradeGate>
        )}
      </div>
    </main>
  )
}
