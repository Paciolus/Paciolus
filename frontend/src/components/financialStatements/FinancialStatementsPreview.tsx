'use client'

import { useState } from 'react'
import { motion, AnimatePresence, type Variants } from 'framer-motion'
import { apiDownload, downloadBlob } from '@/utils/apiClient'
import { formatCurrency } from '@/utils'
import { CashFlowTable } from './CashFlowTable'
import { MappingTraceTable } from './MappingTraceTable'
import { StatementTable } from './StatementTable'
import { useStatementBuilder } from './useStatementBuilder'
import type { FinancialStatementsPreviewProps, StatementTab, ExportFormat } from './types'

const TABS: { key: StatementTab; label: string }[] = [
  { key: 'balance-sheet', label: 'Balance Sheet' },
  { key: 'income-statement', label: 'Income Statement' },
  { key: 'cash-flow', label: 'Cash Flow' },
  { key: 'mapping-trace', label: 'Mapping Trace' },
]

const spinnerVariants = {
  animate: {
    rotate: 360,
    transition: { duration: 1, repeat: Infinity, ease: 'linear' as const },
  },
}

export function FinancialStatementsPreview({
  leadSheetGrouping,
  priorLeadSheetGrouping,
  filename,
  token,
  disabled = false,
}: FinancialStatementsPreviewProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [activeTab, setActiveTab] = useState<StatementTab>('balance-sheet')
  const [isExporting, setIsExporting] = useState<ExportFormat | null>(null)
  const [error, setError] = useState<string | null>(null)

  const { balanceSheet, incomeStatement, totals, cashFlow, mappingTrace } = useStatementBuilder(
    leadSheetGrouping,
    priorLeadSheetGrouping,
  )

  const handleExport = async (format: ExportFormat) => {
    if (isExporting || disabled) return
    setIsExporting(format)
    setError(null)

    try {
      const defaultFilename = format === 'pdf'
        ? 'FinancialStatements.pdf'
        : 'FinancialStatements.xlsx'

      const { blob, filename: downloadFilename, error: downloadError, ok } = await apiDownload(
        `/export/financial-statements?format=${format}`,
        token,
        {
          method: 'POST',
          body: {
            lead_sheet_grouping: leadSheetGrouping,
            ...(priorLeadSheetGrouping ? { prior_lead_sheet_grouping: priorLeadSheetGrouping } : {}),
            filename,
          } as Record<string, unknown>,
        }
      )

      if (!ok || !blob) {
        throw new Error(downloadError || 'Failed to generate export')
      }

      downloadBlob(blob, downloadFilename || defaultFilename)
    } catch (err) {
      console.error(`Financial statements ${format} export error:`, err)
      setError(err instanceof Error ? err.message : 'Failed to generate export')
    } finally {
      setIsExporting(null)
    }
  }

  return (
    <section className={`mt-8 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-surface-card border border-theme rounded-xl overflow-hidden"
      >
        {/* Collapsible Header */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          disabled={disabled}
          className="w-full flex items-center justify-between p-4 text-left"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-sage-500/10 rounded-lg">
              <svg className="w-5 h-5 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <div>
              <h3 className="font-serif text-content-primary text-sm font-medium">
                Financial Statements
              </h3>
              <p className="text-content-tertiary text-xs font-sans">
                Balance Sheet, Income Statement & Cash Flow
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {totals.isBalanced ? (
              <span className="text-xs font-mono px-2 py-1 rounded-full bg-sage-500/20 text-sage-400 border border-sage-500/30">
                BALANCED
              </span>
            ) : (
              <span className="text-xs font-mono px-2 py-1 rounded-full bg-clay-500/20 text-clay-400 border border-clay-500/30">
                OUT OF BALANCE
              </span>
            )}

            <motion.svg
              animate={{ rotate: isExpanded ? 180 : 0 }}
              className="w-5 h-5 text-content-secondary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </motion.svg>
          </div>
        </button>

        {/* Expanded Content */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="border-t border-theme p-4 space-y-4">
                {/* Tab Switcher */}
                <div className="flex gap-1 p-1 bg-surface-card-secondary rounded-lg w-fit">
                  {TABS.map(tab => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key)}
                      className={`
                        px-4 py-1.5 rounded-md text-sm font-sans font-medium transition-colors
                        ${activeTab === tab.key
                          ? 'bg-surface-card text-content-primary shadow-sm'
                          : 'text-content-tertiary hover:text-content-primary'
                        }
                      `}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* Statement Table */}
                <div className="bg-surface-card rounded-lg border border-theme p-3">
                  {activeTab === 'cash-flow' ? (
                    <CashFlowTable cashFlow={cashFlow} />
                  ) : activeTab === 'mapping-trace' ? (
                    <MappingTraceTable entries={mappingTrace} />
                  ) : (
                    <StatementTable
                      items={activeTab === 'balance-sheet' ? balanceSheet : incomeStatement}
                    />
                  )}
                </div>

                {/* Balance difference warning */}
                {!totals.isBalanced && (
                  <div className="flex items-center gap-2 p-3 bg-clay-500/10 border border-clay-500/30 rounded-lg">
                    <svg className="w-4 h-4 text-clay-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                      />
                    </svg>
                    <p className="text-xs text-clay-400 font-sans">
                      Balance Sheet is out of balance by{' '}
                      <span className="font-mono font-medium">{formatCurrency(totals.balanceDifference)}</span>.
                      This may indicate unclassified accounts or mapping gaps.
                    </p>
                  </div>
                )}

                {/* Key Metrics */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { label: 'Total Assets', value: totals.totalAssets },
                    { label: 'Total Liabilities', value: totals.totalLiabilities },
                    { label: 'Revenue', value: totals.totalRevenue },
                    { label: 'Net Income', value: totals.netIncome, colored: true },
                  ].map(metric => (
                    <div key={metric.label} className="p-3 bg-surface-card-secondary rounded-lg text-center">
                      <div className="text-[10px] uppercase tracking-wider text-content-tertiary font-sans mb-1">{metric.label}</div>
                      <div className={`font-mono text-sm ${metric.colored
                        ? (metric.value >= 0 ? 'text-sage-400' : 'text-clay-400')
                        : 'text-content-primary'
                      }`}>
                        {formatCurrency(metric.value)}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Export Buttons */}
                <div className="flex flex-wrap gap-3 pt-2">
                  <ExportButton
                    format="pdf"
                    label="Download PDF"
                    primary
                    isExporting={isExporting}
                    disabled={disabled}
                    onExport={handleExport}
                    spinnerVariants={spinnerVariants}
                  />
                  <ExportButton
                    format="excel"
                    label="Download Excel"
                    isExporting={isExporting}
                    disabled={disabled}
                    onExport={handleExport}
                    spinnerVariants={spinnerVariants}
                  />
                </div>

                {/* Export Error */}
                <AnimatePresence>
                  {error && (
                    <motion.p
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className="text-clay-400 text-xs font-sans text-center"
                    >
                      {error}
                    </motion.p>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </section>
  )
}

function ExportButton({
  format,
  label,
  primary,
  isExporting,
  disabled,
  onExport,
  spinnerVariants,
}: {
  format: ExportFormat
  label: string
  primary?: boolean
  isExporting: ExportFormat | null
  disabled: boolean
  onExport: (format: ExportFormat) => void
  spinnerVariants: Variants
}) {
  const isActive = isExporting === format
  const isDisabled = disabled || isExporting !== null

  const icon = format === 'pdf'
    ? 'M12 10v6m0 0l-3-3m3 3l3-3M6 19a2 2 0 01-2-2V7a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H6z'
    : 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'

  return (
    <motion.button
      onClick={() => onExport(format)}
      disabled={isDisabled}
      whileHover={{ scale: isDisabled ? 1 : 1.02 }}
      whileTap={{ scale: isDisabled ? 1 : 0.98 }}
      className={`flex-1 min-w-[140px] flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
        font-sans text-sm font-medium transition-colors
        ${primary
          ? (isDisabled
            ? 'bg-surface-card-secondary text-content-tertiary cursor-not-allowed'
            : 'bg-sage-500 text-obsidian-900 hover:bg-sage-400')
          : (isDisabled
            ? 'bg-surface-card-secondary border border-theme text-content-tertiary cursor-not-allowed'
            : 'bg-surface-card-secondary border border-sage-500/30 text-sage-400 hover:bg-surface-card hover:border-sage-500/50')
        }`}
    >
      {isActive ? (
        <>
          <motion.svg variants={spinnerVariants} animate="animate" className="w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </motion.svg>
          <span>Generating...</span>
        </>
      ) : (
        <>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={icon} />
          </svg>
          <span>{label}</span>
        </>
      )}
    </motion.button>
  )
}

export default FinancialStatementsPreview
