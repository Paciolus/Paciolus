'use client'

import { FixedAssetScoreCard, FixedAssetTestResultGrid, FixedAssetDataQualityBadge, FlaggedFixedAssetTable } from '@/components/fixedAssetTesting'
import { DisclaimerBox, Citation, CitationFooter } from '@/components/shared'
import { ProofSummaryBar, ProofPanel, extractFAProof } from '@/components/shared/proof'
import { SingleFileTestingPage } from '@/components/shared/testing/SingleFileTestingPage'
import { useFixedAssetTesting } from '@/hooks/useFixedAssetTesting'
import { testCountFor } from '@/content/tool-ledger'

/**
 * Fixed Asset Testing — Tool 10 (Sprint 116)
 *
 * IAS 16 / ISA 540: PP&E assertions and accounting estimates.
 * Upload a fixed asset register for automated testing — 9-test battery
 * for fixed asset anomaly indicators across structural, statistical, and advanced tiers.
 *
 * Sprint 892 (17C): the page shell is shared (SingleFileTestingPage); this file holds what is
 * specific to the tool.
 */
export default function FixedAssetTestingPage() {
  const tool = useFixedAssetTesting()
  return (
    <SingleFileTestingPage
      toolName="fixed_asset_testing"
      tool={tool}
      hero={{
        badge: <>IAS 16 / ISA 540 PP&amp;E Analysis</>,
        title: <>Fixed Asset Testing</>,
        subtitle: (
          <>
            Upload a fixed asset register for automated testing &mdash; {testCountFor('fixed_asset_testing')}-test battery
            for PP&amp;E anomaly indicators per IAS 16 and ISA 540.
          </>
        ),
      }}
      guestDescription="Fixed Asset Testing requires a verified account. Sign in or create an account to analyze your fixed asset register."
      upload={{
        title: <>Upload Fixed Asset Register</>,
        prompt: <>Drop your fixed asset register here or click to browse</>,
        iconClassName: 'w-8 h-8 text-content-secondary',
      }}
      spinnerClassName="w-5 h-5 border-2 border-sage-500/30 border-t-sage-400 rounded-full animate-spin"
      loadingText={name => <>Running {testCountFor('fixed_asset_testing')}-test fixed asset battery on {name}...</>}
      exports={{
        memoEndpoint: '/export/fixed-asset-memo',
        csvEndpoint: '/export/csv/fixed-assets',
        memoFilename: 'FixedAssetTesting_Memo.pdf',
        csvFilename: 'FixedAssetTesting_Flagged.csv',
        defaultStem: 'fixed_asset_testing',
      }}
      renderResult={result => (
        <>
          {/* Evidence Summary */}
          <ProofSummaryBar proof={extractFAProof(result)} />
          <ProofPanel proof={extractFAProof(result)} />

          {/* Score Card */}
          <FixedAssetScoreCard score={result.composite_score} />

          {/* Data Quality */}
          <FixedAssetDataQualityBadge quality={result.data_quality} />

          {/* Test Results Grid */}
          <div>
            <h2 className="type-tool-section mb-4">Test Results</h2>
            <FixedAssetTestResultGrid results={result.test_results} />
          </div>

          {/* Flagged Fixed Asset Table */}
          <div>
            <h2 className="type-tool-section mb-4">Flagged Fixed Assets</h2>
            <FlaggedFixedAssetTable results={result.test_results} />
          </div>

          <DisclaimerBox>
            This automated fixed asset testing
            tool provides analytical procedures to assist professional auditors in evaluating PP&amp;E register
            anomaly indicators per <Citation code="IAS 16" /> and <Citation code="ISA 540" />.
            Results are not depreciation adequacy conclusions or impairment determinations and should be interpreted
            in the context of the specific engagement. They are not a substitute for professional judgment or
            sufficient audit evidence per <Citation code="ISA 500" />.
          </DisclaimerBox>
          <CitationFooter standards={['IAS 16', 'ISA 540', 'ISA 500']} />
        </>
      )}
      infoCards={
        <>
          <div className="theme-card p-6">
            <div className="text-2xl mb-3">4 Tests</div>
            <h3 className="font-serif text-content-primary text-sm mb-2">Structural Tests</h3>
            <p className="font-sans text-content-secondary text-xs">
              Fully depreciated assets, missing required fields, negative values, over-depreciation
            </p>
          </div>
          <div className="theme-card p-6">
            <div className="text-2xl mb-3">3 Tests</div>
            <h3 className="font-serif text-content-primary text-sm mb-2">Statistical Tests</h3>
            <p className="font-sans text-content-secondary text-xs">
              Useful life outliers, cost z-score outliers, asset age concentration
            </p>
          </div>
          <div className="theme-card p-6">
            <div className="text-2xl mb-3">2 Tests</div>
            <h3 className="font-serif text-content-primary text-sm mb-2">Advanced Tests</h3>
            <p className="font-sans text-content-secondary text-xs">
              Duplicate asset detection, residual value anomalies
            </p>
          </div>
        </>
      }
    />
  )
}
