'use client'

/**
 * FinancialStatementsPreview - Sprint 72 / Sprint 84
 *
 * Inline preview of Balance Sheet, Income Statement, and Cash Flow Statement
 * built client-side from lead sheet grouping data. Includes PDF/Excel export.
 *
 * Sprint 84: Added Cash Flow Statement tab (indirect method, ASC 230 / IAS 7).
 * Requires prior period lead sheet grouping for working capital changes.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Display component only, no data persistence
 * - Transforms existing lead_sheet_grouping client-side
 */

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { formatCurrency } from '@/utils'
import { API_URL } from '@/utils/constants'
import type { LeadSheetGrouping, LeadSheetSummary } from '@/types/leadSheet'

// --- Types ---

interface StatementLineItem {
  label: string
  amount: number
  indentLevel: number   // 0=section header, 1=line item
  isSubtotal: boolean
  isTotal: boolean
  leadSheetRef: string  // "A", "B", etc.
}

interface CashFlowLineItem {
  label: string
  amount: number
  source: string
  indentLevel: number
}

interface CashFlowSection {
  label: string
  items: CashFlowLineItem[]
  subtotal: number
}

interface CashFlowStatement {
  operating: CashFlowSection
  investing: CashFlowSection
  financing: CashFlowSection
  netChange: number
  beginningCash: number
  endingCash: number
  isReconciled: boolean
  reconciliationDifference: number
  hasPriorPeriod: boolean
  notes: string[]
}

interface StatementTotals {
  totalAssets: number
  totalLiabilities: number
  totalEquity: number
  isBalanced: boolean
  balanceDifference: number
  totalRevenue: number
  grossProfit: number
  operatingIncome: number
  netIncome: number
}

interface FinancialStatementsPreviewProps {
  leadSheetGrouping: LeadSheetGrouping
  priorLeadSheetGrouping?: LeadSheetGrouping | null
  filename: string
  token: string | null
  disabled?: boolean
}

type StatementTab = 'balance-sheet' | 'income-statement' | 'cash-flow'
type ExportFormat = 'pdf' | 'excel'

// --- Client-side builder (mirrors backend sign conventions) ---

function getBalance(summaries: LeadSheetSummary[], letter: string): number {
  const summary = summaries.find(s => s.lead_sheet === letter)
  return summary?.net_balance ?? 0
}

function buildStatements(grouping: LeadSheetGrouping): {
  balanceSheet: StatementLineItem[]
  incomeStatement: StatementLineItem[]
  totals: StatementTotals
} {
  const s = grouping.summaries
  const bal = (letter: string) => getBalance(s, letter)

  // --- Balance Sheet ---
  const balanceSheet: StatementLineItem[] = []

  // ASSETS
  balanceSheet.push({ label: 'ASSETS', amount: 0, indentLevel: 0, isSubtotal: false, isTotal: false, leadSheetRef: '' })

  balanceSheet.push({ label: 'Current Assets', amount: 0, indentLevel: 0, isSubtotal: false, isTotal: false, leadSheetRef: '' })
  const cash = bal('A')
  const receivables = bal('B')
  const inventory = bal('C')
  const prepaid = bal('D')
  balanceSheet.push({ label: 'Cash and Cash Equivalents', amount: cash, indentLevel: 1, isSubtotal: false, isTotal: false, leadSheetRef: 'A' })
  balanceSheet.push({ label: 'Receivables', amount: receivables, indentLevel: 1, isSubtotal: false, isTotal: false, leadSheetRef: 'B' })
  balanceSheet.push({ label: 'Inventory', amount: inventory, indentLevel: 1, isSubtotal: false, isTotal: false, leadSheetRef: 'C' })
  balanceSheet.push({ label: 'Prepaid Expenses', amount: prepaid, indentLevel: 1, isSubtotal: false, isTotal: false, leadSheetRef: 'D' })
  const totalCurrentAssets = cash + receivables + inventory + prepaid
  balanceSheet.push({ label: 'Total Current Assets', amount: totalCurrentAssets, indentLevel: 1, isSubtotal: true, isTotal: false, leadSheetRef: '' })

  balanceSheet.push({ label: 'Non-Current Assets', amount: 0, indentLevel: 0, isSubtotal: false, isTotal: false, leadSheetRef: '' })
  const ppe = bal('E')
  const intangibles = bal('F')
  balanceSheet.push({ label: 'Property, Plant & Equipment', amount: ppe, indentLevel: 1, isSubtotal: false, isTotal: false, leadSheetRef: 'E' })
  balanceSheet.push({ label: 'Other Assets & Intangibles', amount: intangibles, indentLevel: 1, isSubtotal: false, isTotal: false, leadSheetRef: 'F' })
  const totalNoncurrentAssets = ppe + intangibles
  balanceSheet.push({ label: 'Total Non-Current Assets', amount: totalNoncurrentAssets, indentLevel: 1, isSubtotal: true, isTotal: false, leadSheetRef: '' })

  const totalAssets = totalCurrentAssets + totalNoncurrentAssets
  balanceSheet.push({ label: 'TOTAL ASSETS', amount: totalAssets, indentLevel: 0, isSubtotal: false, isTotal: true, leadSheetRef: '' })

  // LIABILITIES & EQUITY
  balanceSheet.push({ label: 'LIABILITIES & EQUITY', amount: 0, indentLevel: 0, isSubtotal: false, isTotal: false, leadSheetRef: '' })

  balanceSheet.push({ label: 'Current Liabilities', amount: 0, indentLevel: 0, isSubtotal: false, isTotal: false, leadSheetRef: '' })
  const ap = -bal('G')
  const otherCl = -bal('H')
  balanceSheet.push({ label: 'AP & Accrued Liabilities', amount: ap, indentLevel: 1, isSubtotal: false, isTotal: false, leadSheetRef: 'G' })
  balanceSheet.push({ label: 'Other Current Liabilities', amount: otherCl, indentLevel: 1, isSubtotal: false, isTotal: false, leadSheetRef: 'H' })
  const totalCurrentLiabilities = ap + otherCl
  balanceSheet.push({ label: 'Total Current Liabilities', amount: totalCurrentLiabilities, indentLevel: 1, isSubtotal: true, isTotal: false, leadSheetRef: '' })

  balanceSheet.push({ label: 'Non-Current Liabilities', amount: 0, indentLevel: 0, isSubtotal: false, isTotal: false, leadSheetRef: '' })
  const ltDebt = -bal('I')
  const otherLt = -bal('J')
  balanceSheet.push({ label: 'Long-term Debt', amount: ltDebt, indentLevel: 1, isSubtotal: false, isTotal: false, leadSheetRef: 'I' })
  balanceSheet.push({ label: 'Other Long-term Liabilities', amount: otherLt, indentLevel: 1, isSubtotal: false, isTotal: false, leadSheetRef: 'J' })
  const totalNoncurrentLiabilities = ltDebt + otherLt
  balanceSheet.push({ label: 'Total Non-Current Liabilities', amount: totalNoncurrentLiabilities, indentLevel: 1, isSubtotal: true, isTotal: false, leadSheetRef: '' })

  const totalLiabilities = totalCurrentLiabilities + totalNoncurrentLiabilities
  balanceSheet.push({ label: 'Total Liabilities', amount: totalLiabilities, indentLevel: 0, isSubtotal: true, isTotal: false, leadSheetRef: '' })

  const equity = -bal('K')
  balanceSheet.push({ label: "Stockholders' Equity", amount: equity, indentLevel: 1, isSubtotal: false, isTotal: false, leadSheetRef: 'K' })

  const totalLE = totalLiabilities + equity
  balanceSheet.push({ label: 'TOTAL LIABILITIES & EQUITY', amount: totalLE, indentLevel: 0, isSubtotal: false, isTotal: true, leadSheetRef: '' })

  // --- Income Statement ---
  const incomeStatement: StatementLineItem[] = []

  const revenue = -bal('L')
  incomeStatement.push({ label: 'Revenue', amount: revenue, indentLevel: 0, isSubtotal: false, isTotal: false, leadSheetRef: 'L' })

  const cogs = bal('M')
  incomeStatement.push({ label: 'Cost of Goods Sold', amount: cogs, indentLevel: 0, isSubtotal: false, isTotal: false, leadSheetRef: 'M' })

  const grossProfit = revenue - cogs
  incomeStatement.push({ label: 'GROSS PROFIT', amount: grossProfit, indentLevel: 0, isSubtotal: true, isTotal: false, leadSheetRef: '' })

  const opex = bal('N')
  incomeStatement.push({ label: 'Operating Expenses', amount: opex, indentLevel: 0, isSubtotal: false, isTotal: false, leadSheetRef: 'N' })

  const operatingIncome = grossProfit - opex
  incomeStatement.push({ label: 'OPERATING INCOME', amount: operatingIncome, indentLevel: 0, isSubtotal: true, isTotal: false, leadSheetRef: '' })

  const otherNet = -bal('O')
  incomeStatement.push({ label: 'Other Income / (Expense), Net', amount: otherNet, indentLevel: 0, isSubtotal: false, isTotal: false, leadSheetRef: 'O' })

  const netIncome = operatingIncome + otherNet
  incomeStatement.push({ label: 'NET INCOME', amount: netIncome, indentLevel: 0, isSubtotal: false, isTotal: true, leadSheetRef: '' })

  // Balance check
  const balanceDifference = totalAssets - (totalLiabilities + equity)
  const isBalanced = Math.abs(balanceDifference) < 0.01

  return {
    balanceSheet,
    incomeStatement,
    totals: {
      totalAssets,
      totalLiabilities,
      totalEquity: equity,
      isBalanced,
      balanceDifference,
      totalRevenue: revenue,
      grossProfit,
      operatingIncome,
      netIncome,
    },
  }
}

// --- Cash Flow Builder (indirect method, mirrors backend) ---

function buildCashFlowStatement(
  currentGrouping: LeadSheetGrouping,
  priorGrouping: LeadSheetGrouping | null | undefined,
  netIncome: number,
): CashFlowStatement {
  const s = currentGrouping.summaries
  const bal = (letter: string) => getBalance(s, letter)
  const priorBal = (letter: string) =>
    priorGrouping ? getBalance(priorGrouping.summaries, letter) : 0
  const change = (letter: string) =>
    priorGrouping ? bal(letter) - priorBal(letter) : 0

  const hasPrior = !!priorGrouping
  const notes: string[] = []

  // Operating
  const operatingItems: CashFlowLineItem[] = [
    { label: 'Net Income', amount: netIncome, source: 'computed', indentLevel: 1 },
  ]
  // Note: depreciation detection requires account-level detail not available client-side
  notes.push('Depreciation add-back available in PDF/Excel export only')

  if (hasPrior) {
    const deltaB = change('B')
    if (Math.abs(deltaB) > 0.005) operatingItems.push({ label: 'Change in Accounts Receivable', amount: -deltaB, source: 'B', indentLevel: 1 })
    const deltaC = change('C')
    if (Math.abs(deltaC) > 0.005) operatingItems.push({ label: 'Change in Inventory', amount: -deltaC, source: 'C', indentLevel: 1 })
    const deltaD = change('D')
    if (Math.abs(deltaD) > 0.005) operatingItems.push({ label: 'Change in Prepaid Expenses', amount: -deltaD, source: 'D', indentLevel: 1 })
    const deltaG = change('G')
    if (Math.abs(deltaG) > 0.005) operatingItems.push({ label: 'Change in Accounts Payable', amount: -deltaG, source: 'G', indentLevel: 1 })
    const deltaH = change('H')
    if (Math.abs(deltaH) > 0.005) operatingItems.push({ label: 'Change in Accrued Liabilities', amount: -deltaH, source: 'H', indentLevel: 1 })
  } else {
    notes.push('Prior period required for working capital changes')
  }

  const operatingSubtotal = operatingItems.reduce((sum, i) => sum + i.amount, 0)

  // Investing
  const investingItems: CashFlowLineItem[] = []
  if (hasPrior) {
    const deltaE = change('E')
    if (Math.abs(deltaE) > 0.005) investingItems.push({ label: 'Capital Expenditures (PPE)', amount: -deltaE, source: 'E', indentLevel: 1 })
    const deltaF = change('F')
    if (Math.abs(deltaF) > 0.005) investingItems.push({ label: 'Change in Other Non-Current Assets', amount: -deltaF, source: 'F', indentLevel: 1 })
  }
  const investingSubtotal = investingItems.reduce((sum, i) => sum + i.amount, 0)

  // Financing
  const financingItems: CashFlowLineItem[] = []
  if (hasPrior) {
    const deltaI = change('I')
    if (Math.abs(deltaI) > 0.005) financingItems.push({ label: 'Change in Long-Term Debt', amount: -deltaI, source: 'I', indentLevel: 1 })
    const deltaJ = change('J')
    if (Math.abs(deltaJ) > 0.005) financingItems.push({ label: 'Change in Other Long-Term Liabilities', amount: -deltaJ, source: 'J', indentLevel: 1 })
    const deltaK = change('K')
    const equityChangeDisplayed = -deltaK
    const financingEquityChange = equityChangeDisplayed - netIncome
    if (Math.abs(financingEquityChange) > 0.005) financingItems.push({ label: 'Equity Changes (excl. Retained Earnings)', amount: financingEquityChange, source: 'K', indentLevel: 1 })
  }
  const financingSubtotal = financingItems.reduce((sum, i) => sum + i.amount, 0)

  const netChange = operatingSubtotal + investingSubtotal + financingSubtotal
  const endingCash = bal('A')
  const beginningCash = hasPrior ? priorBal('A') : 0

  let isReconciled = false
  let reconciliationDifference = 0
  if (hasPrior) {
    const expectedEnding = beginningCash + netChange
    reconciliationDifference = endingCash - expectedEnding
    isReconciled = Math.abs(reconciliationDifference) < 0.01
  }

  return {
    operating: { label: 'Cash Flows from Operating Activities', items: operatingItems, subtotal: operatingSubtotal },
    investing: { label: 'Cash Flows from Investing Activities', items: investingItems, subtotal: investingSubtotal },
    financing: { label: 'Cash Flows from Financing Activities', items: financingItems, subtotal: financingSubtotal },
    netChange,
    beginningCash,
    endingCash,
    isReconciled,
    reconciliationDifference,
    hasPriorPeriod: hasPrior,
    notes,
  }
}

// --- Cash Flow Table ---

function CashFlowTable({ cashFlow }: { cashFlow: CashFlowStatement }) {
  return (
    <div className="overflow-x-auto space-y-4">
      {[cashFlow.operating, cashFlow.investing, cashFlow.financing].map(section => (
        <div key={section.label}>
          <div className="font-serif text-oatmeal-200 text-sm font-medium mb-2 pt-2">{section.label}</div>
          <table className="w-full text-sm mb-1">
            <tbody>
              {section.items.map((item, idx) => (
                <tr key={`${item.label}-${idx}`}>
                  <td className="py-1 px-3 pl-8 text-oatmeal-300 font-sans">
                    {item.label}
                    {item.source && (
                      <span className="ml-2 text-[10px] text-oatmeal-600 font-mono">[{item.source}]</span>
                    )}
                  </td>
                  <td className={`py-1 px-3 text-right font-mono w-40 ${item.amount < 0 ? 'text-clay-400' : 'text-oatmeal-300'}`}>
                    {formatCurrency(item.amount)}
                  </td>
                </tr>
              ))}
              <tr className="border-t border-obsidian-600">
                <td className="py-1.5 px-3 pl-8 font-sans font-medium text-oatmeal-200">
                  Net {section.label.replace('Cash Flows from ', '')}
                </td>
                <td className={`py-1.5 px-3 text-right font-mono font-medium w-40 ${section.subtotal < 0 ? 'text-clay-400' : 'text-oatmeal-200'}`}>
                  {formatCurrency(section.subtotal)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      ))}

      {/* Net Change */}
      <div className="border-t-2 border-double border-obsidian-500 pt-2">
        <table className="w-full text-sm">
          <tbody>
            <tr>
              <td className="py-1.5 px-3 font-serif font-bold text-oatmeal-100">NET CHANGE IN CASH</td>
              <td className={`py-1.5 px-3 text-right font-mono font-bold w-40 ${cashFlow.netChange < 0 ? 'text-clay-400' : 'text-oatmeal-100'}`}>
                {formatCurrency(cashFlow.netChange)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Reconciliation */}
      {cashFlow.hasPriorPeriod && (
        <div className="pt-2">
          <table className="w-full text-sm">
            <tbody>
              <tr>
                <td className="py-1 px-3 text-oatmeal-300 font-sans">Beginning Cash</td>
                <td className="py-1 px-3 text-right font-mono text-oatmeal-300 w-40">{formatCurrency(cashFlow.beginningCash)}</td>
              </tr>
              <tr>
                <td className="py-1 px-3 text-oatmeal-300 font-sans">Net Change in Cash</td>
                <td className="py-1 px-3 text-right font-mono text-oatmeal-300 w-40">{formatCurrency(cashFlow.netChange)}</td>
              </tr>
              <tr className="border-t-2 border-double border-obsidian-500">
                <td className="py-1.5 px-3 font-serif font-bold text-oatmeal-100">Ending Cash</td>
                <td className="py-1.5 px-3 text-right font-mono font-bold text-oatmeal-100 w-40">{formatCurrency(cashFlow.endingCash)}</td>
              </tr>
            </tbody>
          </table>

          <div className="mt-3 flex justify-center">
            {cashFlow.isReconciled ? (
              <span className="text-xs font-mono px-3 py-1 rounded-full bg-sage-500/20 text-sage-400 border border-sage-500/30">
                RECONCILED
              </span>
            ) : (
              <span className="text-xs font-mono px-3 py-1 rounded-full bg-clay-500/20 text-clay-400 border border-clay-500/30">
                UNRECONCILED ({formatCurrency(cashFlow.reconciliationDifference)})
              </span>
            )}
          </div>
        </div>
      )}

      {/* Notes */}
      {cashFlow.notes.length > 0 && (
        <div className="pt-2 space-y-1">
          {cashFlow.notes.map((note, idx) => (
            <p key={idx} className="text-xs text-oatmeal-500 font-sans italic">
              Note: {note}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

// --- Statement Table ---

function StatementTable({ items }: { items: StatementLineItem[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-obsidian-600">
            <th className="text-left py-2 px-3 text-oatmeal-500 text-xs uppercase tracking-wider font-sans font-medium">
              Description
            </th>
            <th className="text-right py-2 px-3 text-oatmeal-500 text-xs uppercase tracking-wider font-sans font-medium w-40">
              Amount
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, idx) => {
            const isSectionHeader = item.indentLevel === 0 && !item.isSubtotal && !item.isTotal && item.amount === 0
            const isLineItem = item.indentLevel === 1 && !item.isSubtotal && !item.isTotal

            return (
              <tr
                key={`${item.label}-${idx}`}
                className={`
                  ${item.isTotal ? 'border-t-2 border-double border-obsidian-500' : ''}
                  ${item.isSubtotal ? 'border-t border-obsidian-600' : ''}
                `}
              >
                <td
                  className={`
                    py-1.5 px-3
                    ${isSectionHeader ? 'font-serif font-semibold text-oatmeal-200 pt-4' : ''}
                    ${isLineItem ? 'pl-8 text-oatmeal-300 font-sans' : ''}
                    ${item.isSubtotal ? 'pl-8 font-sans font-medium text-oatmeal-200' : ''}
                    ${item.isTotal ? 'font-serif font-bold text-oatmeal-100' : ''}
                  `}
                >
                  <span>{item.label}</span>
                  {item.leadSheetRef && (
                    <span className="ml-2 text-[10px] text-oatmeal-600 font-mono">
                      [{item.leadSheetRef}]
                    </span>
                  )}
                </td>
                <td
                  className={`
                    py-1.5 px-3 text-right font-mono
                    ${isSectionHeader ? 'text-transparent' : ''}
                    ${isLineItem ? 'text-oatmeal-300' : ''}
                    ${item.isSubtotal ? 'font-medium text-oatmeal-200 border-t border-obsidian-600' : ''}
                    ${item.isTotal ? 'font-bold text-oatmeal-100' : ''}
                    ${!isSectionHeader && item.amount < 0 ? 'text-clay-400' : ''}
                  `}
                >
                  {isSectionHeader ? '' : formatCurrency(item.amount)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// --- Main Component ---

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

  const { balanceSheet, incomeStatement, totals } = useMemo(
    () => buildStatements(leadSheetGrouping),
    [leadSheetGrouping]
  )

  const cashFlow = useMemo(
    () => buildCashFlowStatement(leadSheetGrouping, priorLeadSheetGrouping, totals.netIncome),
    [leadSheetGrouping, priorLeadSheetGrouping, totals.netIncome]
  )

  const handleExport = async (format: ExportFormat) => {
    if (isExporting || disabled) return
    setIsExporting(format)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/export/financial-statements?format=${format}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          lead_sheet_grouping: leadSheetGrouping,
          ...(priorLeadSheetGrouping ? { prior_lead_sheet_grouping: priorLeadSheetGrouping } : {}),
          filename,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const detail = errorData.detail
        const msg = typeof detail === 'object' && detail !== null
          ? (detail.message || detail.code || 'Failed to generate export')
          : (detail || 'Failed to generate export')
        throw new Error(msg)
      }

      const blob = await response.blob()
      const contentDisposition = response.headers.get('Content-Disposition')
      let downloadFilename = format === 'pdf'
        ? 'FinancialStatements.pdf'
        : 'FinancialStatements.xlsx'

      if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+)"/)
        if (match) downloadFilename = match[1]
      }

      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = downloadFilename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error(`Financial statements ${format} export error:`, err)
      setError(err instanceof Error ? err.message : 'Failed to generate export')
    } finally {
      setIsExporting(null)
    }
  }

  const spinnerVariants = {
    animate: {
      rotate: 360,
      transition: { duration: 1, repeat: Infinity, ease: 'linear' as const },
    },
  }

  const tabs: { key: StatementTab; label: string }[] = [
    { key: 'balance-sheet', label: 'Balance Sheet' },
    { key: 'income-statement', label: 'Income Statement' },
    { key: 'cash-flow', label: 'Cash Flow' },
  ]

  return (
    <section className={`mt-8 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      {/* Section Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-obsidian-800/50 border border-obsidian-600/50 rounded-xl overflow-hidden"
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
              <h3 className="font-serif text-oatmeal-200 text-sm font-medium">
                Financial Statements
              </h3>
              <p className="text-oatmeal-500 text-xs font-sans">
                Balance Sheet, Income Statement & Cash Flow
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Balance verification badge */}
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
              className="w-5 h-5 text-oatmeal-400"
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
              <div className="border-t border-obsidian-600/50 p-4 space-y-4">
                {/* Tab Switcher */}
                <div className="flex gap-1 p-1 bg-obsidian-700/50 rounded-lg w-fit">
                  {tabs.map(tab => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key)}
                      className={`
                        px-4 py-1.5 rounded-md text-sm font-sans font-medium transition-colors
                        ${activeTab === tab.key
                          ? 'bg-obsidian-600 text-oatmeal-100 shadow-sm'
                          : 'text-oatmeal-500 hover:text-oatmeal-300'
                        }
                      `}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* Statement Table */}
                <div className="bg-obsidian-800/50 rounded-lg border border-obsidian-700 p-3">
                  {activeTab === 'cash-flow' ? (
                    <CashFlowTable cashFlow={cashFlow} />
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
                  <div className="p-3 bg-obsidian-700/50 rounded-lg text-center">
                    <div className="text-[10px] uppercase tracking-wider text-oatmeal-500 font-sans mb-1">Total Assets</div>
                    <div className="font-mono text-sm text-oatmeal-200">{formatCurrency(totals.totalAssets)}</div>
                  </div>
                  <div className="p-3 bg-obsidian-700/50 rounded-lg text-center">
                    <div className="text-[10px] uppercase tracking-wider text-oatmeal-500 font-sans mb-1">Total Liabilities</div>
                    <div className="font-mono text-sm text-oatmeal-200">{formatCurrency(totals.totalLiabilities)}</div>
                  </div>
                  <div className="p-3 bg-obsidian-700/50 rounded-lg text-center">
                    <div className="text-[10px] uppercase tracking-wider text-oatmeal-500 font-sans mb-1">Revenue</div>
                    <div className="font-mono text-sm text-oatmeal-200">{formatCurrency(totals.totalRevenue)}</div>
                  </div>
                  <div className="p-3 bg-obsidian-700/50 rounded-lg text-center">
                    <div className="text-[10px] uppercase tracking-wider text-oatmeal-500 font-sans mb-1">Net Income</div>
                    <div className={`font-mono text-sm font-medium ${totals.netIncome >= 0 ? 'text-sage-400' : 'text-clay-400'}`}>
                      {formatCurrency(totals.netIncome)}
                    </div>
                  </div>
                </div>

                {/* Export Buttons */}
                <div className="flex flex-wrap gap-3 pt-2">
                  <motion.button
                    onClick={() => handleExport('pdf')}
                    disabled={disabled || isExporting !== null}
                    whileHover={{ scale: disabled || isExporting ? 1 : 1.02 }}
                    whileTap={{ scale: disabled || isExporting ? 1 : 0.98 }}
                    className={`flex-1 min-w-[140px] flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
                      font-sans text-sm font-medium transition-colors
                      ${disabled || isExporting
                        ? 'bg-obsidian-600 text-oatmeal-500 cursor-not-allowed'
                        : 'bg-sage-500 text-obsidian-900 hover:bg-sage-400'
                      }`}
                  >
                    {isExporting === 'pdf' ? (
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
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M12 10v6m0 0l-3-3m3 3l3-3M6 19a2 2 0 01-2-2V7a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H6z"
                          />
                        </svg>
                        <span>Download PDF</span>
                      </>
                    )}
                  </motion.button>

                  <motion.button
                    onClick={() => handleExport('excel')}
                    disabled={disabled || isExporting !== null}
                    whileHover={{ scale: disabled || isExporting ? 1 : 1.02 }}
                    whileTap={{ scale: disabled || isExporting ? 1 : 0.98 }}
                    className={`flex-1 min-w-[140px] flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
                      font-sans text-sm font-medium transition-colors border
                      ${disabled || isExporting
                        ? 'bg-obsidian-700 border-obsidian-600 text-oatmeal-500 cursor-not-allowed'
                        : 'bg-obsidian-700 border-sage-500/30 text-sage-400 hover:bg-obsidian-600 hover:border-sage-500/50'
                      }`}
                  >
                    {isExporting === 'excel' ? (
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
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                        <span>Download Excel</span>
                      </>
                    )}
                  </motion.button>
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

export default FinancialStatementsPreview
