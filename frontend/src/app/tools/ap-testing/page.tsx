'use client'

import { APScoreCard, APTestResultGrid, APDataQualityBadge, FlaggedPaymentTable } from '@/components/apTesting'
import { DisclaimerBox, CitationFooter, SavedSettingsNotice } from '@/components/shared'
import { ProofSummaryBar, ProofPanel, extractAPProof } from '@/components/shared/proof'
import { SingleFileTestingPage } from '@/components/shared/testing/SingleFileTestingPage'
import { useAPTesting } from '@/hooks/useAPTesting'
import { testCountFor } from '@/content/tool-ledger'

/**
 * AP Payment Testing — Full Tool (Sprint 75)
 *
 * Standalone tool for automated AP payment analysis.
 * Upload → Process → Results with 13-test battery.
 *
 * Sprint 893 (17C): the page shell is shared (SingleFileTestingPage); this file holds what is
 * specific to the tool.
 */
export default function APTestingPage() {
  const tool = useAPTesting()
  return (
    <SingleFileTestingPage
      toolName="ap_testing"
      tool={tool}
      settingsToolKey="ap"
      hero={{
        badge: <>References ISA 240 · ISA 500</>,
        title: <>AP Payment Testing</>,
        subtitle: (
          <>
            Upload an AP Payment Register for automated testing &mdash; {testCountFor('ap_testing')}-test battery
            for duplicate payments, vendor anomalies, and fraud indicators.
          </>
        ),
      }}
      guestDescription="AP Payment Testing requires a verified account. Sign in or create an account to analyze your payment data."
      upload={{
        title: <>Upload AP Payment Register</>,
        prompt: <>Drop your payment register here or click to browse</>,
        iconClassName: 'w-8 h-8 text-content-secondary',
      }}
      spinnerClassName="w-5 h-5 border-2 border-sage-500/30 border-t-sage-500 rounded-full animate-spin"
      loadingText={name => <>Running {testCountFor('ap_testing')}-test battery on {name}...</>}
      exports={{
        memoEndpoint: '/export/ap-testing-memo',
        csvEndpoint: '/export/csv/ap-testing',
        memoFilename: 'APTesting_Memo.pdf',
        csvFilename: 'APTesting_Flagged.csv',
        defaultStem: 'ap_testing',
      }}
      extraExportFields={result => ({
        // Sprint 836: the memo states which thresholds differed from the defaults.
        settings_applied: result.settings_applied ?? null,
        settings_ignored: result.settings_ignored ?? null,
        // Sprint 886 (OUT-12): the memo's Duplicate Payment Recovery Summary.
        duplicate_payment_summary: result.duplicate_payment_summary ?? null,
      })}
      renderResult={result => (
        <>
          {/* Sprint 836: saved settings that changed a threshold, or were not applied */}
          <SavedSettingsNotice tool="ap" applied={result.settings_applied} ignored={result.settings_ignored} />

          {/* Evidence Summary */}
          <ProofSummaryBar proof={extractAPProof(result)} />
          <ProofPanel proof={extractAPProof(result)} />

          {/* Score Card */}
          <APScoreCard score={result.composite_score} />

          {/* Data Quality — full width */}
          <APDataQualityBadge quality={result.data_quality} />

          {/* Test Results Grid */}
          <div>
            <h2 className="type-tool-section mb-4">Test Results</h2>
            <APTestResultGrid results={result.test_results} />
          </div>

          {/* Flagged Payment Table */}
          <div>
            <h2 className="type-tool-section mb-4">Flagged Payments</h2>
            <FlaggedPaymentTable results={result.test_results} />
          </div>

          <DisclaimerBox>
            This automated AP payment testing
            tool provides analytical procedures to assist professional auditors. Results should be interpreted in
            the context of the specific engagement and are not a substitute for professional judgment. Duplicate
            detection and fraud indicator tests use standard thresholds that may require adjustment for specific
            industries or entity sizes.
          </DisclaimerBox>
          <CitationFooter standards={['ISA 240', 'ISA 500']} />
        </>
      )}
      infoCards={
        <>
          <div className="theme-card p-6">
            <div className="text-2xl mb-3">5 Tests</div>
            <h3 className="font-serif text-content-primary text-sm mb-2">Structural Tests</h3>
            <p className="font-sans text-content-secondary text-xs">
              Exact duplicates, near-duplicates, missing fields, round amounts, unusual payment amounts
            </p>
          </div>
          <div className="theme-card p-6">
            <div className="text-2xl mb-3">5 Tests</div>
            <h3 className="font-serif text-content-primary text-sm mb-2">Statistical Tests</h3>
            <p className="font-sans text-content-secondary text-xs">
              Vendor concentration, payment timing, amount clustering, invoice sequence gaps, payment splitting
            </p>
          </div>
          <div className="theme-card p-6">
            <div className="text-2xl mb-3">3 Tests</div>
            <h3 className="font-serif text-content-primary text-sm mb-2">Fraud Indicators</h3>
            <p className="font-sans text-content-secondary text-xs">
              Ghost vendor patterns, rush payments, approval threshold circumvention
            </p>
          </div>
        </>
      }
    />
  )
}
