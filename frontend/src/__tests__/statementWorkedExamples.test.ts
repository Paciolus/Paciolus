/**
 * Worked examples for the financial statement builder (Sprints 867 / 882).
 *
 * Review findings TQ-01, TQ-02 and TQ-03 (read-only review at ef5e567). The
 * backend suite `backend/tests/test_statement_worked_examples.py` runs the same
 * examples against `FinancialStatementBuilder`, so the page's own builder and
 * the exported statements cannot drift. Every expected figure is fixed by hand
 * from the example's bookkeeping, never computed from the builder's output.
 */
import { renderHook } from '@testing-library/react'
import { useStatementBuilder, UNCLOSED_EARNINGS_LABEL } from '@/components/financialStatements/useStatementBuilder'
import type { LeadSheetGrouping, LeadSheetSummary, LeadSheetAccount } from '@/types/leadSheet'

// Exact statement wording under review — the backend suite asserts the same string.
const EARNINGS_LABEL = 'Current-Period Earnings (Not Yet Closed)'

type Row = [letter: string, account: string, debit: number, credit: number]

/** Lead sheet grouping from (letter, account, debit, credit) rows; must balance. */
function makeGrouping(rows: Row[]): LeadSheetGrouping {
  const byLetter = new Map<string, LeadSheetSummary>()
  for (const [letter, account, debit, credit] of rows) {
    const summary = byLetter.get(letter) ?? {
      lead_sheet: letter as LeadSheetSummary['lead_sheet'],
      lead_sheet_name: letter,
      category: '',
      accounts: [] as LeadSheetAccount[],
      total_debit: 0,
      total_credit: 0,
      net_balance: 0,
      account_count: 0,
    }
    summary.accounts.push({
      account,
      debit,
      credit,
      confidence: 1,
      lead_sheet: letter as LeadSheetAccount['lead_sheet'],
      lead_sheet_name: letter,
      match_reason: 'worked example',
    })
    summary.total_debit += debit
    summary.total_credit += credit
    summary.net_balance = summary.total_debit - summary.total_credit
    summary.account_count += 1
    byLetter.set(letter, summary)
  }
  const debits = rows.reduce((sum, r) => sum + r[2], 0)
  const credits = rows.reduce((sum, r) => sum + r[3], 0)
  if (Math.abs(debits - credits) >= 0.005) throw new Error('worked example must be a balanced trial balance')
  const summaries = [...byLetter.keys()].sort().map(letter => byLetter.get(letter)!)
  return {
    summaries,
    unclassified_count: 0,
    unclassified_accounts: [],
    total_accounts: rows.length,
  }
}

function build(current: Row[], prior?: Row[]) {
  const currentGrouping = makeGrouping(current)
  const priorGrouping = prior ? makeGrouping(prior) : undefined
  return renderHook(() => useStatementBuilder(currentGrouping, priorGrouping)).result.current
}

// ===========================================================================
// TQ-01 — equity leaves out the period's earnings
// ===========================================================================

// Cash 900 Dr; Expenses 300 Dr; Accounts payable 300 Cr; Opening equity 500 Cr; Revenue 400 Cr.
const PROFIT_TB: Row[] = [
  ['A', 'Cash', 900, 0],
  ['N', 'Operating Expenses', 300, 0],
  ['G', 'Accounts Payable', 0, 300],
  ['K', 'Opening Equity', 0, 500],
  ['L', 'Revenue', 0, 400],
]

// Cash 700 Dr; Expenses 300 Dr; Accounts payable 300 Cr; Opening equity 500 Cr; Revenue 200 Cr.
const LOSS_TB: Row[] = [
  ['A', 'Cash', 700, 0],
  ['N', 'Operating Expenses', 300, 0],
  ['G', 'Accounts Payable', 0, 300],
  ['K', 'Opening Equity', 0, 500],
  ['L', 'Revenue', 0, 200],
]

describe('worked examples — TQ-01 pre-closing equity', () => {
  it('uses the reviewed wording for the earnings line', () => {
    expect(UNCLOSED_EARNINGS_LABEL).toBe(EARNINGS_LABEL)
  })

  it('profit: equity includes the period result and the statement balances', () => {
    const { totals, balanceSheet } = build(PROFIT_TB)

    expect(totals.netIncome).toBe(100)
    expect(totals.totalEquity).toBe(600)
    expect(totals.totalLiabilities + totals.totalEquity).toBe(900)
    expect(totals.balanceDifference).toBe(0)
    expect(totals.isBalanced).toBe(true)

    const labels = balanceSheet.map(i => i.label)
    const earnings = balanceSheet.find(i => i.label === EARNINGS_LABEL)
    expect(earnings?.amount).toBe(100)
    expect(earnings?.leadSheetRef).toBe('')
    expect(earnings?.indentLevel).toBe(1)
    expect(balanceSheet.find(i => i.label === "Stockholders' Equity")?.amount).toBe(500)
    expect(balanceSheet.find(i => i.label === 'TOTAL LIABILITIES & EQUITY')?.amount).toBe(900)
    expect(labels.indexOf("Stockholders' Equity") + 1).toBe(labels.indexOf(EARNINGS_LABEL))
    expect(labels.indexOf(EARNINGS_LABEL) + 1).toBe(labels.indexOf('TOTAL LIABILITIES & EQUITY'))
  })

  it('loss: equity includes the period result and the statement balances', () => {
    const { totals, balanceSheet } = build(LOSS_TB)

    expect(totals.netIncome).toBe(-100)
    expect(totals.totalEquity).toBe(400)
    expect(totals.totalLiabilities + totals.totalEquity).toBe(700)
    expect(totals.balanceDifference).toBe(0)
    expect(totals.isBalanced).toBe(true)
    expect(balanceSheet.find(i => i.label === EARNINGS_LABEL)?.amount).toBe(-100)
  })

  it('closed books: no earnings line', () => {
    const { totals, balanceSheet } = build([
      ['A', 'Cash', 900, 0],
      ['G', 'Accounts Payable', 0, 300],
      ['K', 'Opening Equity', 0, 600],
    ])
    expect(balanceSheet.some(i => i.label === EARNINGS_LABEL)).toBe(false)
    expect(totals.totalEquity).toBe(600)
    expect(totals.isBalanced).toBe(true)
  })
})

// ===========================================================================
// TQ-02 — unclosed income creates a financing cash flow that didn't happen
// ===========================================================================

// Opening: cash 100, equity 100.
const OPENING_100: Row[] = [
  ['A', 'Cash', 100, 0],
  ['K', "Owner's Capital", 0, 100],
]
// In the period, services are sold for 50 cash. Revenue is not yet closed.
const SOLD_SERVICES_FOR_50: Row[] = [
  ['A', 'Cash', 150, 0],
  ['K', "Owner's Capital", 0, 100],
  ['L', 'Service Revenue', 0, 50],
]

describe('worked examples — TQ-02 unclosed income in the cash flow', () => {
  it('a cash sale is operating and nothing is financing', () => {
    const { cashFlow } = build(SOLD_SERVICES_FOR_50, OPENING_100)

    expect(cashFlow.operating.subtotal).toBe(50)
    expect(cashFlow.investing.subtotal).toBe(0)
    expect(cashFlow.financing.subtotal).toBe(0)
    expect(cashFlow.financing.items).toEqual([])
    expect(cashFlow.netChange).toBe(50)
    expect(cashFlow.beginningCash).toBe(100)
    expect(cashFlow.endingCash).toBe(150)
    expect(cashFlow.reconciliationDifference).toBe(0)
    expect(cashFlow.isReconciled).toBe(true)
  })

  it('prior-year earnings closed into equity are not financing', () => {
    // Prior year-end TB, pre-closing: equity accounts 70 + revenue 30 open.
    // Closing moved the 30 into equity, so this year's equity accounts hold 100.
    const { cashFlow } = build(SOLD_SERVICES_FOR_50, [
      ['A', 'Cash', 100, 0],
      ['K', "Owner's Capital", 0, 70],
      ['L', 'Service Revenue', 0, 30],
    ])

    expect(cashFlow.operating.subtotal).toBe(50)
    expect(cashFlow.financing.subtotal).toBe(0)
    expect(cashFlow.netChange).toBe(50)
    expect(cashFlow.endingCash).toBe(150)
    expect(cashFlow.isReconciled).toBe(true)
  })

  it('a real owner distribution is still financing', () => {
    const { cashFlow } = build(
      [
        ['A', 'Cash', 130, 0],
        ['K', "Owner's Capital", 0, 100],
        ['K', 'Owner Distributions', 20, 0],
        ['L', 'Service Revenue', 0, 50],
      ],
      OPENING_100,
    )

    expect(cashFlow.operating.subtotal).toBe(50)
    expect(cashFlow.financing.subtotal).toBe(-20)
    expect(cashFlow.financing.items.map(i => [i.label, i.amount])).toEqual([
      ['Equity Changes (excl. Retained Earnings)', -20],
    ])
    expect(cashFlow.netChange).toBe(30)
    expect(cashFlow.endingCash).toBe(130)
    expect(cashFlow.reconciliationDifference).toBe(0)
    expect(cashFlow.isReconciled).toBe(true)
  })
})

// ===========================================================================
// TQ-03 — depreciation is shown as cash from investing
// ===========================================================================

const PURCHASES_LABEL = 'Purchases of Property, Plant & Equipment'
const NOT_SEPARABLE_LABEL =
  'Net Change in Property, Plant & Equipment (Purchases and Disposals Not Separable)'

// Opening: cash 100, gross fixed assets 100, accumulated depreciation 20, equity 180.
const FIXED_ASSET_OPENING: Row[] = [
  ['A', 'Cash', 100, 0],
  ['E', 'Equipment', 100, 0],
  ['E', 'Accumulated Depreciation', 0, 20],
  ['K', "Owner's Capital", 0, 180],
]
// In the period, depreciation of 10 and nothing else.
const DEPRECIATION_ONLY: Row[] = [
  ['A', 'Cash', 100, 0],
  ['E', 'Equipment', 100, 0],
  ['E', 'Accumulated Depreciation', 0, 30],
  ['K', "Owner's Capital", 0, 180],
  ['N', 'Depreciation Expense', 10, 0],
]
// Same, plus a cash purchase of fixed assets for 20.
const DEPRECIATION_AND_PURCHASE: Row[] = [
  ['A', 'Cash', 80, 0],
  ['E', 'Equipment', 120, 0],
  ['E', 'Accumulated Depreciation', 0, 30],
  ['K', "Owner's Capital", 0, 180],
  ['N', 'Depreciation Expense', 10, 0],
]

describe('worked examples — TQ-03 depreciation is not investing cash', () => {
  it('depreciation alone moves no cash', () => {
    const { cashFlow } = build(DEPRECIATION_ONLY, FIXED_ASSET_OPENING)

    expect(cashFlow.operating.items.filter(i => i.label === 'Depreciation & Amortization').map(i => i.amount)).toEqual([10])
    expect(cashFlow.operating.subtotal).toBe(0)
    expect(cashFlow.investing.subtotal).toBe(0)
    expect(cashFlow.investing.items).toEqual([])
    expect(cashFlow.financing.subtotal).toBe(0)
    expect(cashFlow.netChange).toBe(0)
    expect(cashFlow.endingCash).toBe(100)
    expect(cashFlow.reconciliationDifference).toBe(0)
    expect(cashFlow.isReconciled).toBe(true)
  })

  it('a cash purchase is the only investing flow', () => {
    const { cashFlow } = build(DEPRECIATION_AND_PURCHASE, FIXED_ASSET_OPENING)

    expect(cashFlow.operating.subtotal).toBe(0)
    expect(cashFlow.investing.items.map(i => [i.label, i.amount])).toEqual([[PURCHASES_LABEL, -20]])
    expect(cashFlow.investing.subtotal).toBe(-20)
    expect(cashFlow.financing.subtotal).toBe(0)
    expect(cashFlow.netChange).toBe(-20)
    expect(cashFlow.endingCash).toBe(80)
    expect(cashFlow.reconciliationDifference).toBe(0)
    expect(cashFlow.isReconciled).toBe(true)
  })

  it('a disposal is reported as a limitation, not a capital expenditure', () => {
    // Equipment costing 30 with 15 accumulated depreciation is sold for 15 cash
    // (no gain or loss); depreciation of 10 is charged. Gross PPE 100 -> 70,
    // accumulated depreciation 20 + 10 - 15 = 15. Cash 100 + 15 = 115.
    const { cashFlow } = build(
      [
        ['A', 'Cash', 115, 0],
        ['E', 'Equipment', 70, 0],
        ['E', 'Accumulated Depreciation', 0, 15],
        ['K', "Owner's Capital", 0, 180],
        ['N', 'Depreciation Expense', 10, 0],
      ],
      FIXED_ASSET_OPENING,
    )

    expect(cashFlow.investing.items.map(i => [i.label, i.amount])).toEqual([[NOT_SEPARABLE_LABEL, 15]])
    expect(cashFlow.notes.some(n => n.includes('cannot be told apart'))).toBe(true)
    expect(cashFlow.operating.subtotal).toBe(0)
    expect(cashFlow.netChange).toBe(15)
    expect(cashFlow.endingCash).toBe(115)
    expect(cashFlow.isReconciled).toBe(true)
  })

  it('no line is labelled capital expenditures', () => {
    for (const current of [DEPRECIATION_ONLY, DEPRECIATION_AND_PURCHASE]) {
      const { cashFlow } = build(current, FIXED_ASSET_OPENING)
      expect(cashFlow.investing.items.some(i => i.label.includes('Capital Expenditures'))).toBe(false)
    }
  })
})
