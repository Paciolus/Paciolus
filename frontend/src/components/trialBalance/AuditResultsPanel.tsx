'use client'

import { useMappings } from '@/contexts/MappingContext'
import { AccountType } from '@/types/mapping'
import type { AuditResult } from '@/types/diagnostic'
import type { BenchmarkComparisonResponse } from '@/hooks'
import type { DisplayMode } from '@/components/sensitivity'
import { RiskDashboard } from '@/components/risk'
import { DownloadReportButton } from '@/components/export'
import { KeyMetricsSection } from '@/components/analytics'
import { ClassificationQualitySection } from '@/components/diagnostics/ClassificationQualitySection'
import { AccrualCompletenessSection } from '@/components/trialBalance/AccrualCompletenessSection'
import { ExpenseCategorySection } from '@/components/trialBalance/ExpenseCategorySection'
import { PopulationProfileSection } from '@/components/trialBalance/PopulationProfileSection'
import { SensitivityToolbar } from '@/components/sensitivity'
import { MappingToolbar } from '@/components/mapping'
import { BenchmarkSection } from '@/components/benchmark'
import { LeadSheetSection } from '@/components/leadSheet'
import { FinancialStatementsPreview } from '@/components/financialStatements'

interface AuditResultsPanelProps {
  result: AuditResult
  isRecalculating: boolean
  filename: string
  token: string | null
  materialityThreshold: number
  setMaterialityThreshold: (v: number) => void
  displayMode: DisplayMode
  onDisplayModeChange: (mode: DisplayMode) => void
  selectedIndustry: string
  availableIndustries: string[]
  comparisonResults: BenchmarkComparisonResponse | null
  isLoadingComparison: boolean
  onIndustryChange: (industry: string) => Promise<void>
  onRerunAudit: () => void
  onReset: () => void
  onExportPopulationProfilePDF?: () => void
  onExportPopulationProfileCSV?: () => void
  onExportExpenseCategoryPDF?: () => void
  onExportExpenseCategoryCSV?: () => void
  onExportAccrualCompletenessPDF?: () => void
  onExportAccrualCompletenessCSV?: () => void
}

export function AuditResultsPanel({
  result,
  isRecalculating,
  filename,
  token,
  materialityThreshold,
  setMaterialityThreshold,
  displayMode,
  onDisplayModeChange,
  selectedIndustry,
  availableIndustries,
  comparisonResults,
  isLoadingComparison,
  onIndustryChange,
  onRerunAudit,
  onReset,
  onExportPopulationProfilePDF,
  onExportPopulationProfileCSV,
  onExportExpenseCategoryPDF,
  onExportExpenseCategoryCSV,
  onExportAccrualCompletenessPDF,
  onExportAccrualCompletenessCSV,
}: AuditResultsPanelProps) {
  const mappingContext = useMappings()

  return (
    <div className="space-y-4 transition-opacity">
      {isRecalculating && (
        <div className="space-y-4">
          <div className="flex items-center justify-center gap-2 bg-sage-50 border border-sage-200 rounded-lg px-4 py-2">
            <div className="w-4 h-4 border-2 border-sage-200 border-t-sage-500 rounded-full animate-spin"></div>
            <span className="text-sage-700 text-sm font-sans font-medium">Recalculating with new threshold...</span>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 rounded-full bg-oatmeal-200 animate-pulse relative overflow-hidden">
              <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-oatmeal-100 to-transparent" />
            </div>
            <div className="w-24 h-6 mt-3 rounded bg-oatmeal-200 animate-pulse relative overflow-hidden">
              <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-oatmeal-100 to-transparent" />
            </div>
          </div>
          <div className="bg-surface-card border border-theme rounded-xl p-4 max-w-sm mx-auto">
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex justify-between">
                  <div className="w-24 h-4 rounded bg-oatmeal-200 animate-pulse relative overflow-hidden">
                    <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-oatmeal-100 to-transparent" />
                  </div>
                  <div className="w-20 h-4 rounded bg-oatmeal-200 animate-pulse relative overflow-hidden">
                    <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-oatmeal-100 to-transparent" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className={isRecalculating ? 'hidden' : ''}>
        {result.balanced ? (
          <>
            <div className="w-16 h-16 bg-sage-50 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-10 h-10 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-sage-600 text-xl font-serif font-semibold">Balanced</p>
          </>
        ) : (
          <>
            <div className="w-16 h-16 bg-clay-50 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-10 h-10 text-clay-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <p className="text-clay-600 text-xl font-serif font-semibold">Out of Balance</p>
          </>
        )}

        <div className="theme-card p-4 text-left max-w-sm mx-auto">
          <div className="grid grid-cols-2 gap-2 text-sm font-sans">
            <span className="text-content-secondary">Total Debits:</span>
            <span className="text-content-primary text-right font-mono">${result.total_debits.toLocaleString()}</span>
            <span className="text-content-secondary">Total Credits:</span>
            <span className="text-content-primary text-right font-mono">${result.total_credits.toLocaleString()}</span>
            <span className="text-content-secondary">Difference:</span>
            <span className={`text-right font-mono ${result.difference === 0 ? 'text-sage-600' : 'text-clay-600'}`}>
              ${result.difference.toLocaleString()}
            </span>
            <span className="text-content-secondary">Rows Analyzed:</span>
            <span className="text-content-primary text-right font-mono">{result.row_count}</span>
          </div>
        </div>

        {(result.material_count > 0 || result.immaterial_count > 0) && (
          <div className="max-w-md mx-auto mt-4">
            <MappingToolbar
              disabled={isRecalculating}
              onRerunAudit={onRerunAudit}
            />
          </div>
        )}

        <div className="mt-6 max-w-2xl mx-auto">
          <SensitivityToolbar
            threshold={materialityThreshold}
            displayMode={displayMode}
            onThresholdChange={setMaterialityThreshold}
            onDisplayModeChange={onDisplayModeChange}
            disabled={isRecalculating}
          />
        </div>

        {(result.material_count > 0 || result.immaterial_count > 0) && (
          <div className="mt-4">
            <RiskDashboard
              anomalies={result.abnormal_balances}
              riskSummary={result.risk_summary}
              materialityThreshold={result.materiality_threshold}
              disabled={isRecalculating}
              getMappingForAccount={(accountName) => {
                const mapping = mappingContext.mappings.get(accountName)
                const anomaly = result.abnormal_balances.find(a => a.account === accountName)
                return {
                  currentType: mapping?.overrideType || (anomaly?.category as AccountType) || 'unknown',
                  isManual: mapping?.isManual || false,
                }
              }}
              onTypeChange={(accountName, type, detectedType) => {
                mappingContext.setAccountType(accountName, type, detectedType)
              }}
            />
          </div>
        )}

        {result.classification_quality && (
          <div className="mt-4">
            <ClassificationQualitySection data={result.classification_quality} />
          </div>
        )}

        {result.population_profile && (
          <div className="mt-4">
            <PopulationProfileSection
              data={result.population_profile}
              onExportPDF={onExportPopulationProfilePDF}
              onExportCSV={onExportPopulationProfileCSV}
            />
          </div>
        )}

        {result.expense_category_analytics && (
          <div className="mt-4">
            <ExpenseCategorySection
              data={result.expense_category_analytics}
              onExportPDF={onExportExpenseCategoryPDF}
              onExportCSV={onExportExpenseCategoryCSV}
            />
          </div>
        )}

        {result.accrual_completeness && result.accrual_completeness.accrual_account_count > 0 && (
          <div className="mt-4">
            <AccrualCompletenessSection
              data={result.accrual_completeness}
              onExportPDF={onExportAccrualCompletenessPDF}
              onExportCSV={onExportAccrualCompletenessCSV}
            />
          </div>
        )}

        {result.analytics && (
          <div className="mt-6">
            <KeyMetricsSection
              analytics={result.analytics}
              disabled={isRecalculating}
            />
          </div>
        )}

        {result.analytics && availableIndustries.length > 0 && (
          <div className="mt-6 p-4 theme-card">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
              <div>
                <h4 className="font-serif text-sm font-medium text-content-primary mb-1">
                  Industry Benchmark Comparison
                </h4>
                <p className="text-xs text-content-tertiary">
                  Compare your ratios against industry benchmarks
                </p>
              </div>
              <select
                value={selectedIndustry}
                onChange={(e) => onIndustryChange(e.target.value)}
                disabled={isRecalculating || isLoadingComparison}
                className="
                  px-3 py-2 rounded-lg text-sm font-sans
                  bg-surface-input border border-theme text-content-primary
                  focus:outline-none focus:ring-2 focus:ring-sage-500/50 focus:border-sage-500
                  disabled:opacity-50 disabled:cursor-not-allowed
                "
              >
                <option value="">Select an industry...</option>
                {availableIndustries.map((industry) => (
                  <option key={industry} value={industry}>
                    {industry.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                  </option>
                ))}
              </select>
            </div>

            {selectedIndustry && (
              <BenchmarkSection
                data={comparisonResults}
                isLoading={isLoadingComparison}
                industryDisplay={selectedIndustry.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                disabled={isRecalculating}
              />
            )}
          </div>
        )}

        {result.lead_sheet_grouping && (
          <LeadSheetSection
            data={result.lead_sheet_grouping}
            disabled={isRecalculating}
          />
        )}

        {result.lead_sheet_grouping && (
          <FinancialStatementsPreview
            leadSheetGrouping={result.lead_sheet_grouping}
            filename={filename}
            token={token}
            disabled={isRecalculating}
          />
        )}

        {/* Disclaimer */}
        <div className="bg-surface-card-secondary border border-theme rounded-xl p-4 mt-8">
          <p className="font-sans text-xs text-content-tertiary leading-relaxed">
            <span className="text-content-secondary font-medium">Disclaimer:</span> This automated trial balance
            diagnostic tool provides analytical procedures to assist professional auditors. Results should be
            interpreted in the context of the specific engagement and are not a substitute for professional
            judgment or sufficient audit evidence per ISA 500.
          </p>
        </div>

        <div className="mt-6 pt-4 border-t border-theme">
          <DownloadReportButton
            auditResult={result}
            filename={filename}
            disabled={isRecalculating}
            token={token}
          />
        </div>

        <button
          onClick={onReset}
          className="text-sage-600 hover:text-sage-700 text-sm font-sans font-medium mt-2"
          disabled={isRecalculating}
        >
          Upload another file
        </button>
      </div>
    </div>
  )
}
