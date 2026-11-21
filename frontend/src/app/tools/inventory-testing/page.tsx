'use client'

import { InventoryScoreCard, InventoryTestResultGrid, InventoryDataQualityBadge, FlaggedInventoryTable } from '@/components/inventoryTesting'
import { DisclaimerBox, Citation, CitationFooter } from '@/components/shared'
import { ProofSummaryBar, ProofPanel, extractInventoryProof } from '@/components/shared/proof'
import { SingleFileTestingPage } from '@/components/shared/testing/SingleFileTestingPage'
import { useInventoryTesting } from '@/hooks/useInventoryTesting'
import { testCountFor } from '@/content/tool-ledger'

/**
 * Inventory Testing — Tool 11 (Sprint 119)
 *
 * IAS 2 / ISA 500 / ISA 540: inventory register anomaly indicators (no count attendance — ISA 501 not cited).
 * Upload an inventory register for automated testing — 9-test battery
 * for inventory anomaly indicators across structural, statistical, and advanced tiers.
 *
 * Sprint 892 (17C): the page shell is shared (SingleFileTestingPage); this file holds what is
 * specific to the tool.
 */
export default function InventoryTestingPage() {
  const tool = useInventoryTesting()
  return (
    <SingleFileTestingPage
      toolName="inventory_testing"
      tool={tool}
      hero={{
        badge: <>IAS 2 / ISA 500 Inventory Analysis</>,
        title: <>Inventory Testing</>,
        subtitle: (
          <>
            Upload an inventory register for automated testing &mdash; 10-test battery
            for inventory anomaly indicators per IAS 2.
          </>
        ),
      }}
      guestDescription="Inventory Testing requires a verified account. Sign in or create an account to analyze your inventory register."
      upload={{
        title: <>Upload Inventory Register</>,
        prompt: <>Drop your inventory register here or click to browse</>,
        iconClassName: 'w-8 h-8 text-content-tertiary',
      }}
      spinnerClassName="w-5 h-5 border-2 border-sage-500/30 border-t-sage-500 rounded-full animate-spin"
      loadingText={name => <>Running {testCountFor('inventory_testing')}-test inventory battery on {name}...</>}
      exports={{
        memoEndpoint: '/export/inventory-memo',
        csvEndpoint: '/export/csv/inventory',
        memoFilename: 'InventoryTesting_Memo.pdf',
        csvFilename: 'InventoryTesting_Flagged.csv',
        defaultStem: 'inventory_testing',
      }}
      renderResult={result => (
        <>
          {/* Evidence Summary */}
          <ProofSummaryBar proof={extractInventoryProof(result)} />
          <ProofPanel proof={extractInventoryProof(result)} />

          {/* Score Card */}
          <InventoryScoreCard score={result.composite_score} />

          {/* Data Quality */}
          <InventoryDataQualityBadge quality={result.data_quality} />

          {/* Test Results Grid */}
          <div>
            <h2 className="type-tool-section mb-4">Test Results</h2>
            <InventoryTestResultGrid results={result.test_results} />
          </div>

          {/* Flagged Inventory Table */}
          <div>
            <h2 className="type-tool-section mb-4">Flagged Inventory Items</h2>
            <FlaggedInventoryTable results={result.test_results} />
          </div>

          <DisclaimerBox>
            This automated inventory testing
            tool provides analytical procedures to assist professional auditors in evaluating inventory register
            anomaly indicators per <Citation code="IAS 2" /> and <Citation code="ISA 540" />. It analyses
            register data only and does not replace attendance at a physical inventory count.
            Results are not NRV adequacy conclusions or obsolescence determinations and should be interpreted
            in the context of the specific engagement. They are not a substitute for professional judgment or
            sufficient audit evidence per <Citation code="ISA 500" />.
          </DisclaimerBox>
          <CitationFooter standards={['IAS 2', 'ISA 540', 'ISA 500']} />
        </>
      )}
      infoCards={
        <>
          <div className="theme-card p-6">
            <div className="text-2xl mb-3">3 Tests</div>
            <h3 className="font-serif text-content-primary text-sm mb-2">Structural Tests</h3>
            <p className="font-sans text-content-secondary text-xs">
              Missing fields, negative values, extended value mismatch
            </p>
          </div>
          <div className="theme-card p-6">
            <div className="text-2xl mb-3">4 Tests</div>
            <h3 className="font-serif text-content-primary text-sm mb-2">Statistical Tests</h3>
            <p className="font-sans text-content-secondary text-xs">
              Unit cost outliers, quantity outliers, slow-moving inventory, category concentration
            </p>
          </div>
          <div className="theme-card p-6">
            <div className="text-2xl mb-3">2 Tests</div>
            <h3 className="font-serif text-content-primary text-sm mb-2">Advanced Tests</h3>
            <p className="font-sans text-content-secondary text-xs">
              Duplicate items, zero-value items
            </p>
          </div>
        </>
      }
    />
  )
}
