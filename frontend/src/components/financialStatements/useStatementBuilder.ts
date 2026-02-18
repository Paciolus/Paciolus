import { useMemo } from 'react'
import type { LeadSheetGrouping, LeadSheetSummary } from '@/types/leadSheet'
import type {
  StatementLineItem,
  CashFlowLineItem,
  CashFlowStatement,
  StatementTotals,
  MappingTraceEntry,
  MappingTraceAccount,
} from './types'

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

const CHANGE_THRESHOLD = 0.005

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
  notes.push('Depreciation add-back available in PDF/Excel export only')

  if (hasPrior) {
    const deltaB = change('B')
    if (Math.abs(deltaB) > CHANGE_THRESHOLD) operatingItems.push({ label: 'Change in Accounts Receivable', amount: -deltaB, source: 'B', indentLevel: 1 })
    const deltaC = change('C')
    if (Math.abs(deltaC) > CHANGE_THRESHOLD) operatingItems.push({ label: 'Change in Inventory', amount: -deltaC, source: 'C', indentLevel: 1 })
    const deltaD = change('D')
    if (Math.abs(deltaD) > CHANGE_THRESHOLD) operatingItems.push({ label: 'Change in Prepaid Expenses', amount: -deltaD, source: 'D', indentLevel: 1 })
    const deltaG = change('G')
    if (Math.abs(deltaG) > CHANGE_THRESHOLD) operatingItems.push({ label: 'Change in Accounts Payable', amount: -deltaG, source: 'G', indentLevel: 1 })
    const deltaH = change('H')
    if (Math.abs(deltaH) > CHANGE_THRESHOLD) operatingItems.push({ label: 'Change in Accrued Liabilities', amount: -deltaH, source: 'H', indentLevel: 1 })
  } else {
    notes.push('Prior period required for working capital changes')
  }

  const operatingSubtotal = operatingItems.reduce((sum, i) => sum + i.amount, 0)

  // Investing
  const investingItems: CashFlowLineItem[] = []
  if (hasPrior) {
    const deltaE = change('E')
    if (Math.abs(deltaE) > CHANGE_THRESHOLD) investingItems.push({ label: 'Capital Expenditures (PPE)', amount: -deltaE, source: 'E', indentLevel: 1 })
    const deltaF = change('F')
    if (Math.abs(deltaF) > CHANGE_THRESHOLD) investingItems.push({ label: 'Change in Other Non-Current Assets', amount: -deltaF, source: 'F', indentLevel: 1 })
  }
  const investingSubtotal = investingItems.reduce((sum, i) => sum + i.amount, 0)

  // Financing
  const financingItems: CashFlowLineItem[] = []
  if (hasPrior) {
    const deltaI = change('I')
    if (Math.abs(deltaI) > CHANGE_THRESHOLD) financingItems.push({ label: 'Change in Long-Term Debt', amount: -deltaI, source: 'I', indentLevel: 1 })
    const deltaJ = change('J')
    if (Math.abs(deltaJ) > CHANGE_THRESHOLD) financingItems.push({ label: 'Change in Other Long-Term Liabilities', amount: -deltaJ, source: 'J', indentLevel: 1 })
    const deltaK = change('K')
    const equityChangeDisplayed = -deltaK
    const financingEquityChange = equityChangeDisplayed - netIncome
    if (Math.abs(financingEquityChange) > CHANGE_THRESHOLD) financingItems.push({ label: 'Equity Changes (excl. Retained Earnings)', amount: financingEquityChange, source: 'K', indentLevel: 1 })
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

const SIGN_CORRECTED_LETTERS = new Set(['G', 'H', 'I', 'J', 'K', 'L', 'O'])

const STATEMENT_LINE_MAP: [string, string, string][] = [
  ['Balance Sheet', 'Cash and Cash Equivalents', 'A'],
  ['Balance Sheet', 'Receivables', 'B'],
  ['Balance Sheet', 'Inventory', 'C'],
  ['Balance Sheet', 'Prepaid Expenses', 'D'],
  ['Balance Sheet', 'Property, Plant & Equipment', 'E'],
  ['Balance Sheet', 'Other Assets & Intangibles', 'F'],
  ['Balance Sheet', 'AP & Accrued Liabilities', 'G'],
  ['Balance Sheet', 'Other Current Liabilities', 'H'],
  ['Balance Sheet', 'Long-term Debt', 'I'],
  ['Balance Sheet', 'Other Long-term Liabilities', 'J'],
  ['Balance Sheet', "Stockholders' Equity", 'K'],
  ['Income Statement', 'Revenue', 'L'],
  ['Income Statement', 'Cost of Goods Sold', 'M'],
  ['Income Statement', 'Operating Expenses', 'N'],
  ['Income Statement', 'Other Income / (Expense), Net', 'O'],
]

function buildMappingTrace(
  grouping: LeadSheetGrouping,
  balanceSheet: StatementLineItem[],
  incomeStatement: StatementLineItem[],
): MappingTraceEntry[] {
  // Index summaries by lead sheet letter
  const summaryIndex = new Map<string, LeadSheetSummary>()
  for (const summary of grouping.summaries) {
    summaryIndex.set(summary.lead_sheet, summary)
  }

  // Index statement amounts by lead sheet ref
  const stmtAmounts = new Map<string, number>()
  for (const item of balanceSheet) {
    if (item.leadSheetRef) stmtAmounts.set(item.leadSheetRef, item.amount)
  }
  for (const item of incomeStatement) {
    if (item.leadSheetRef) stmtAmounts.set(item.leadSheetRef, item.amount)
  }

  return STATEMENT_LINE_MAP.map(([stmtName, lineLabel, ref]) => {
    const summary = summaryIndex.get(ref)
    const statementAmount = stmtAmounts.get(ref) ?? 0

    if (!summary) {
      return {
        statement: stmtName,
        lineLabel,
        leadSheetRef: ref,
        leadSheetName: lineLabel,
        statementAmount,
        accountCount: 0,
        accounts: [],
        isTied: true,
        tieDifference: 0,
        rawAggregate: 0,
        signCorrectionApplied: SIGN_CORRECTED_LETTERS.has(ref),
      }
    }

    const accounts: MappingTraceAccount[] = []
    let rawSum = 0

    for (const acct of summary.accounts) {
      const debit = acct.debit ?? 0
      const credit = acct.credit ?? 0
      const net = debit - credit
      rawSum += net
      accounts.push({
        accountName: acct.account,
        debit,
        credit,
        netBalance: net,
        confidence: acct.confidence ?? 1,
        matchedKeywords: [],
      })
    }

    const tieDiff = Math.abs(rawSum - summary.net_balance)
    return {
      statement: stmtName,
      lineLabel,
      leadSheetRef: ref,
      leadSheetName: summary.lead_sheet_name,
      statementAmount,
      accountCount: accounts.length,
      accounts,
      isTied: tieDiff < 0.01,
      tieDifference: tieDiff,
      rawAggregate: rawSum,
      signCorrectionApplied: SIGN_CORRECTED_LETTERS.has(ref),
    }
  })
}

export interface UseStatementBuilderReturn {
  balanceSheet: StatementLineItem[];
  incomeStatement: StatementLineItem[];
  totals: StatementTotals;
  cashFlow: CashFlowStatement;
  mappingTrace: MappingTraceEntry[];
}

export function useStatementBuilder(
  leadSheetGrouping: LeadSheetGrouping,
  priorLeadSheetGrouping?: LeadSheetGrouping | null,
): UseStatementBuilderReturn {
  const { balanceSheet, incomeStatement, totals } = useMemo(
    () => buildStatements(leadSheetGrouping),
    [leadSheetGrouping]
  )

  const cashFlow = useMemo(
    () => buildCashFlowStatement(leadSheetGrouping, priorLeadSheetGrouping, totals.netIncome),
    [leadSheetGrouping, priorLeadSheetGrouping, totals.netIncome]
  )

  const mappingTrace = useMemo(
    () => buildMappingTrace(leadSheetGrouping, balanceSheet, incomeStatement),
    [leadSheetGrouping, balanceSheet, incomeStatement]
  )

  return { balanceSheet, incomeStatement, totals, cashFlow, mappingTrace }
}
