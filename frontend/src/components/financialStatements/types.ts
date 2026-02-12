import type { LeadSheetGrouping } from '@/types/leadSheet'

export interface StatementLineItem {
  label: string
  amount: number
  indentLevel: number   // 0=section header, 1=line item
  isSubtotal: boolean
  isTotal: boolean
  leadSheetRef: string  // "A", "B", etc.
}

export interface CashFlowLineItem {
  label: string
  amount: number
  source: string
  indentLevel: number
}

export interface CashFlowSection {
  label: string
  items: CashFlowLineItem[]
  subtotal: number
}

export interface CashFlowStatement {
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

export interface StatementTotals {
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

export interface FinancialStatementsPreviewProps {
  leadSheetGrouping: LeadSheetGrouping
  priorLeadSheetGrouping?: LeadSheetGrouping | null
  filename: string
  token: string | null
  disabled?: boolean
}

export type StatementTab = 'balance-sheet' | 'income-statement' | 'cash-flow'
export type ExportFormat = 'pdf' | 'excel'
