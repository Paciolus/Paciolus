'use client'

import { PayrollScoreCard, PayrollTestResultGrid, PayrollDataQualityBadge, FlaggedEmployeeTable } from '@/components/payrollTesting'
import { DisclaimerBox, CitationFooter, SavedSettingsNotice } from '@/components/shared'
import { ProofSummaryBar, ProofPanel, extractPayrollProof } from '@/components/shared/proof'
import { SingleFileTestingPage } from '@/components/shared/testing/SingleFileTestingPage'
import { usePayrollTesting } from '@/hooks/usePayrollTesting'
import { testCountFor } from '@/content/tool-ledger'

/**
 * Payroll & Employee Testing — Full Tool (Sprint 87)
 *
 * Standalone tool for automated payroll register analysis.
 * Upload -> Process -> Results with 11-test battery.
 * Sprint 88: Added export buttons (PDF memo + CSV).
 * Sprint 125: Migrated to semantic theme tokens (light theme).
 *
 * Sprint 893 (17C): the page shell is shared (SingleFileTestingPage); this file holds what is
 * specific to the tool.
 */
export default function PayrollTestingPage() {
  const tool = usePayrollTesting()
  return (
    <SingleFileTestingPage
      toolName="payroll_testing"
      tool={tool}
      settingsToolKey="payroll"
      hero={{
        badge: <>References ISA 240 · ISA 500</>,
        title: <>Payroll &amp; Employee Testing</>,
        subtitle: (
          <>
            Upload a Payroll Register for automated testing &mdash; {testCountFor('payroll_testing')}-test battery
            for ghost-employee indicators, duplicate payments, and statistical anomalies.
          </>
        ),
      }}
      guestDescription="Payroll &amp; Employee Testing requires a verified account. Sign in or create an account to analyze your payroll data."
      upload={{
        title: <>Upload Payroll Register</>,
        prompt: <>Drop your payroll register here or click to browse</>,
        iconClassName: 'w-8 h-8 text-content-secondary',
        iconPath:
          'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
      }}
      spinnerClassName="w-5 h-5 border-2 border-sage-500/30 border-t-sage-500 rounded-full animate-spin"
      loadingText={name => <>Running {testCountFor('payroll_testing')}-test battery on {name}...</>}
      exports={{
        memoEndpoint: '/export/payroll-testing-memo',
        csvEndpoint: '/export/csv/payroll-testing',
        memoFilename: 'PayrollTesting_Memo.pdf',
        csvFilename: 'PayrollTesting_Flagged.csv',
        defaultStem: 'payroll_testing',
      }}
      extraExportFields={result => ({
        // Sprint 836: the memo states which thresholds differed from the defaults.
        settings_applied: result.settings_applied ?? null,
        settings_ignored: result.settings_ignored ?? null,
        // Sprint 886 (OUT-12): register total, department distribution, headcount roll-forward.
        payroll_register_total: result.payroll_register_total ?? null,
        department_summary: result.department_summary ?? null,
        headcount_rollforward: result.headcount_rollforward ?? null,
      })}
      renderResult={result => (
        <>
          {/* Sprint 836: saved settings that changed a threshold, or were not applied */}
          <SavedSettingsNotice tool="payroll" applied={result.settings_applied} ignored={result.settings_ignored} />

          {/* Evidence Summary */}
          <ProofSummaryBar proof={extractPayrollProof(result)} />
          <ProofPanel proof={extractPayrollProof(result)} />

          {/* Score Card */}
          <PayrollScoreCard score={result.composite_score} />

          {/* Data Quality — full width */}
          <PayrollDataQualityBadge quality={result.data_quality} />

          {/* Test Results Grid */}
          <div>
            <h2 className="type-tool-section mb-4">Test Results</h2>
            <PayrollTestResultGrid results={result.test_results} />
          </div>

          {/* Flagged Employee Table */}
          <div>
            <h2 className="type-tool-section mb-4">Flagged Employees</h2>
            <FlaggedEmployeeTable results={result.test_results} />
          </div>

          <DisclaimerBox>
            This automated payroll testing
            tool provides analytical procedures to assist professional auditors. Results should be interpreted in
            the context of the specific engagement and are not a substitute for professional judgment. Ghost employee
            indicators and fraud pattern tests use standard thresholds that may require adjustment for specific
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
              Duplicate employees, missing fields, round amounts, post-termination payments, check number gaps
            </p>
          </div>
          <div className="theme-card p-6">
            <div className="text-2xl mb-3">3 Tests</div>
            <h3 className="font-serif text-content-primary text-sm mb-2">Statistical Tests</h3>
            <p className="font-sans text-content-secondary text-xs">
              Unusual pay amounts, pay frequency anomalies, Benford&apos;s Law analysis on gross pay
            </p>
          </div>
          <div className="theme-card p-6">
            <div className="text-2xl mb-3">3 Tests</div>
            <h3 className="font-serif text-content-primary text-sm mb-2">Fraud Indicators</h3>
            <p className="font-sans text-content-secondary text-xs">
              Ghost employee patterns, duplicate bank accounts/addresses, duplicate tax IDs
            </p>
          </div>
        </>
      }
    />
  )
}
