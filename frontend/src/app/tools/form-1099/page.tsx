'use client'

/**
 * Form 1099 Preparation — Sprint 689e.
 *
 * Standalone tool page. Dual CSV upload (vendors + payments),
 * pivoted client-side into the JSON payload; backend returns filing
 * candidates, data-quality issues, and a W-9 collection queue.
 */

import { useAuthSession } from '@/contexts/AuthSessionContext'
import { Form1099FileUpload } from '@/components/form1099/Form1099FileUpload'
import { Form1099Results } from '@/components/form1099/Form1099Results'
import {
  CitationFooter,
  DisclaimerBox,
  GuestCTA,
  UnverifiedCTA,
  UpgradeGate,
} from '@/components/shared'
import { useForm1099 } from '@/hooks/useForm1099'

export default function Form1099Page() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuthSession()
  const isVerified = user?.is_verified !== false
  const { status, result, error, analyze, exportCsv } = useForm1099()

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="page-container">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-50 border border-sage-200 mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-sage-700 text-sm font-sans font-medium">
              IRS 1099-NEC / 1099-MISC / 1099-INT
            </span>
          </div>
          <h1 className="type-tool-title mb-3">Form 1099 Preparation</h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Identify vendors that meet 1099-NEC / 1099-MISC / 1099-INT reporting thresholds. Applies
            IRS corporation safe-harbor, processor-reported exemptions, and flags vendors that need a
            W-9 on file before filing.
          </p>
        </div>

        {!authLoading && !isAuthenticated && (
          <GuestCTA description="Form 1099 Preparation requires a verified account. Sign in or create an account to continue." />
        )}

        {!authLoading && isAuthenticated && !isVerified && <UnverifiedCTA />}

        {isAuthenticated && isVerified && (
          <UpgradeGate toolName="form_1099">
            <div className="max-w-5xl mx-auto space-y-6">
              <Form1099FileUpload
                onAnalyze={analyze}
                onExport={exportCsv}
                loading={status === 'loading'}
              />

              {error && (
                <div className="p-4 rounded-lg border border-clay-200 bg-clay-50 text-clay-700 text-sm font-sans">
                  {error}
                </div>
              )}

              {result && <Form1099Results result={result} />}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">IRS Thresholds Built-In</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Applies the 1099-NEC $600 threshold, 1099-MISC category thresholds, and the $10 1099-INT
                    floor. Medical and legal payments retain their reporting requirement even for corporate
                    vendors (per IRC §6041A).
                  </p>
                </div>
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Processor Safe-Harbor</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Credit card and PayPal payments are excluded from 1099-NEC / MISC reporting under the
                    processor-reported safe-harbor (reported on 1099-K by the processor, not by the payer).
                  </p>
                </div>
                <div className="theme-card p-6">
                  <h3 className="font-serif text-content-primary text-sm mb-2">Zero-Storage</h3>
                  <p className="font-sans text-content-tertiary text-xs">
                    Vendor master and payment register data are parsed in-browser, posted as JSON, analyzed
                    in memory, and discarded after the response.
                  </p>
                </div>
              </div>

              <DisclaimerBox>
                Filing candidates surfaced here reflect the IRS monetary thresholds and the corporate /
                processor safe-harbors under IRC §6041 and §6041A. Final classification of any payment
                (especially the medical / legal carve-out) and the decision to request a W-9 via Form W-9
                remains a preparer judgment; consult Publication 1220 for electronic-filing specifications.
              </DisclaimerBox>
              <CitationFooter standards={[]} />
            </div>
          </UpgradeGate>
        )}
      </div>
    </main>
  )
}
