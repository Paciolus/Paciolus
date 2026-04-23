'use client'

/**
 * Book-to-Tax Reconciliation — Sprint 689f.
 *
 * Standalone tool page. Pure form input (no CSV upload). Loads the
 * STANDARD_ADJUSTMENTS catalog on mount to seed the row-level picker,
 * then POSTs the full request to /audit/book-to-tax.
 */

import { useEffect } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { BookToTaxForm } from '@/components/bookToTax/BookToTaxForm'
import { BookToTaxResults } from '@/components/bookToTax/BookToTaxResults'
import {
  CitationFooter,
  DisclaimerBox,
  GuestCTA,
  UnverifiedCTA,
  UpgradeGate,
} from '@/components/shared'
import { useBookToTax } from '@/hooks/useBookToTax'

export default function BookToTaxPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuthSession()
  const isVerified = user?.is_verified !== false
  const hasPaidTier = user?.tier && user.tier !== 'free'
  const { status, result, standardAdjustments, error, analyze, exportCsv, loadStandardAdjustments } = useBookToTax()

  useEffect(() => {
    if (isAuthenticated && isVerified && hasPaidTier) {
      loadStandardAdjustments()
    }
  }, [isAuthenticated, isVerified, hasPaidTier, loadStandardAdjustments])

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="page-container">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-50 border border-sage-200 mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-sage-700 text-sm font-sans font-medium">
              Form 1120 Schedule M-1 / M-3 &middot; ASC 740
            </span>
          </div>
          <h1 className="type-tool-title mb-3">Book-to-Tax Reconciliation</h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Bridge book pretax income to taxable income with a Schedule M-1 / M-3 reconciliation,
            roll forward deferred taxes under <span className="font-mono">ASC 740</span>, and compute a
            federal and state tax provision with effective-rate reconciliation.
          </p>
        </div>

        {!authLoading && !isAuthenticated && (
          <GuestCTA description="Book-to-Tax Reconciliation requires a verified account. Sign in or create an account to continue." />
        )}

        {!authLoading && isAuthenticated && !isVerified && <UnverifiedCTA />}

        {isAuthenticated && isVerified && (
          <UpgradeGate toolName="book_to_tax">
            <div className="max-w-5xl mx-auto space-y-6">
              <BookToTaxForm
                onAnalyze={analyze}
                onExport={exportCsv}
                loading={status === 'loading'}
                standardAdjustments={standardAdjustments}
              />

              {error && (
                <div className="p-4 rounded-lg border border-clay-200 bg-clay-50 text-clay-700 text-sm font-sans">
                  {error}
                </div>
              )}

              {result && <BookToTaxResults result={result} />}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">M-1 / M-3 Auto-Select</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Entities with total assets of $10 million or more are presented on Schedule M-3 with
                    the permanent / temporary split per column; smaller entities get the classic M-1
                    layout.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">ASC 740 Rollforward</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Temporary differences flow into the deferred tax rollforward at the configured rate;
                    the resulting movement becomes the deferred component of the tax provision &mdash;
                    closing the gap between current tax and book tax expense.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Standard Adjustments Catalog</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Common adjustments (meals &sect;274(n), fines &sect;162(f), tax-exempt interest,
                    depreciation differences) are pre-populated from the backend; pick one to auto-set
                    the permanent / temporary and add / subtract defaults.
                  </p>
                </div>
              </div>

              <DisclaimerBox>
                The M-1 / M-3 reconciliation and provision computed here apply the rates you supply to
                the adjustments you enter. Classification of an item as permanent versus temporary, and
                the application of uncertain-tax-position analysis under <span className="font-mono">ASC 740</span>, remain preparer
                judgments; the output is a working-paper draft, not a filed return.
              </DisclaimerBox>
              <CitationFooter standards={[]} />
            </div>
          </UpgradeGate>
        )}
      </div>
    </main>
  )
}
