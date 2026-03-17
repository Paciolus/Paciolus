import { renderHook } from '@testing-library/react'
import { useStatementBuilder } from '@/components/financialStatements/useStatementBuilder'
import type { LeadSheetGrouping, LeadSheetSummary, LeadSheetAccount } from '@/types/leadSheet'

// ---------------------------------------------------------------------------
// Helper: build a LeadSheetAccount for a given lead sheet letter
// ---------------------------------------------------------------------------
function makeAccount(
  name: string,
  debit: number,
  credit: number,
  opts?: { confidence?: number; lead_sheet?: string; lead_sheet_name?: string },
): LeadSheetAccount {
  return {
    account: name,
    debit,
    credit,
    confidence: opts?.confidence ?? 1,
    lead_sheet: (opts?.lead_sheet ?? 'A') as LeadSheetAccount['lead_sheet'],
    lead_sheet_name: opts?.lead_sheet_name ?? 'Cash',
    match_reason: 'test',
  }
}

// ---------------------------------------------------------------------------
// Helper: build a single LeadSheetSummary
// ---------------------------------------------------------------------------
function makeSummary(
  letter: string,
  name: string,
  netBalance: number,
  accounts?: LeadSheetAccount[],
  category = 'asset',
): LeadSheetSummary {
  const defaultAccounts: LeadSheetAccount[] = accounts ?? [
    makeAccount(name, Math.max(netBalance, 0), Math.max(-netBalance, 0), {
      lead_sheet: letter,
      lead_sheet_name: name,
    }),
  ]
  return {
    lead_sheet: letter as LeadSheetSummary['lead_sheet'],
    lead_sheet_name: name,
    category,
    accounts: defaultAccounts,
    total_debit: defaultAccounts.reduce((s, a) => s + a.debit, 0),
    total_credit: defaultAccounts.reduce((s, a) => s + a.credit, 0),
    net_balance: netBalance,
    account_count: defaultAccounts.length,
  }
}

// ---------------------------------------------------------------------------
// Helper: build a full LeadSheetGrouping with all 15 letters (A-O)
// ---------------------------------------------------------------------------
function makeFullGrouping(overrides?: Partial<Record<string, number>>): LeadSheetGrouping {
  // Default balanced trial balance (natural sign convention):
  //   Assets (A-F): positive net_balance (debit balances)
  //   Liabilities (G-J), Equity (K): negative net_balance (credit balances)
  //   Revenue (L): negative net_balance (credit balance)
  //   Expenses (M-N): positive net_balance (debit balances)
  //   Other (O): negative net_balance (credit balance)
  const defaults: Record<string, { name: string; balance: number; category: string }> = {
    A: { name: 'Cash', balance: 50000, category: 'asset' },
    B: { name: 'Receivables', balance: 30000, category: 'asset' },
    C: { name: 'Inventory', balance: 20000, category: 'asset' },
    D: { name: 'Prepaid Expenses', balance: 10000, category: 'asset' },
    E: { name: 'Property, Plant & Equipment', balance: 40000, category: 'asset' },
    F: { name: 'Other Assets & Intangibles', balance: 15000, category: 'asset' },
    G: { name: 'AP & Accrued Liabilities', balance: -25000, category: 'liability' },
    H: { name: 'Other Current Liabilities', balance: -10000, category: 'liability' },
    I: { name: 'Long-term Debt', balance: -30000, category: 'liability' },
    J: { name: 'Other Long-term Liabilities', balance: -5000, category: 'liability' },
    K: { name: "Stockholders' Equity", balance: -95000, category: 'equity' },
    L: { name: 'Revenue', balance: -100000, category: 'revenue' },
    M: { name: 'Cost of Goods Sold', balance: 60000, category: 'expense' },
    N: { name: 'Operating Expenses', balance: 30000, category: 'expense' },
    O: { name: 'Other Income / (Expense), Net', balance: -5000, category: 'other' },
  }

  const summaries: LeadSheetSummary[] = Object.entries(defaults).map(([letter, def]) => {
    const balance = overrides?.[letter] ?? def.balance
    return makeSummary(letter, def.name, balance, undefined, def.category)
  })

  return {
    summaries,
    unmapped_count: 0,
    total_accounts: summaries.reduce((s, su) => s + su.account_count, 0),
  }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useStatementBuilder', () => {
  // ========================================================================
  // 1. Initial state shape
  // ========================================================================
  describe('return shape', () => {
    it('returns all expected keys', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(result.current).toHaveProperty('balanceSheet')
      expect(result.current).toHaveProperty('incomeStatement')
      expect(result.current).toHaveProperty('totals')
      expect(result.current).toHaveProperty('cashFlow')
      expect(result.current).toHaveProperty('mappingTrace')
    })

    it('balanceSheet is an array of StatementLineItem objects', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(Array.isArray(result.current.balanceSheet)).toBe(true)
      expect(result.current.balanceSheet.length).toBeGreaterThan(0)
      const first = result.current.balanceSheet[0]!
      expect(first).toHaveProperty('label')
      expect(first).toHaveProperty('amount')
      expect(first).toHaveProperty('indentLevel')
      expect(first).toHaveProperty('isSubtotal')
      expect(first).toHaveProperty('isTotal')
      expect(first).toHaveProperty('leadSheetRef')
    })

    it('incomeStatement is an array of StatementLineItem objects', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(Array.isArray(result.current.incomeStatement)).toBe(true)
      expect(result.current.incomeStatement.length).toBeGreaterThan(0)
    })

    it('totals has all expected fields', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      const { totals } = result.current
      expect(totals).toHaveProperty('totalAssets')
      expect(totals).toHaveProperty('totalLiabilities')
      expect(totals).toHaveProperty('totalEquity')
      expect(totals).toHaveProperty('isBalanced')
      expect(totals).toHaveProperty('balanceDifference')
      expect(totals).toHaveProperty('totalRevenue')
      expect(totals).toHaveProperty('grossProfit')
      expect(totals).toHaveProperty('operatingIncome')
      expect(totals).toHaveProperty('netIncome')
    })

    it('cashFlow has all expected fields', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      const { cashFlow } = result.current
      expect(cashFlow).toHaveProperty('operating')
      expect(cashFlow).toHaveProperty('investing')
      expect(cashFlow).toHaveProperty('financing')
      expect(cashFlow).toHaveProperty('netChange')
      expect(cashFlow).toHaveProperty('beginningCash')
      expect(cashFlow).toHaveProperty('endingCash')
      expect(cashFlow).toHaveProperty('isReconciled')
      expect(cashFlow).toHaveProperty('reconciliationDifference')
      expect(cashFlow).toHaveProperty('hasPriorPeriod')
      expect(cashFlow).toHaveProperty('notes')
    })
  })

  // ========================================================================
  // 2. Balance sheet line items
  // ========================================================================
  describe('balance sheet', () => {
    it('includes all expected section headers and line items', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const labels = result.current.balanceSheet.map(i => i.label)

      expect(labels).toContain('ASSETS')
      expect(labels).toContain('Current Assets')
      expect(labels).toContain('Cash and Cash Equivalents')
      expect(labels).toContain('Receivables')
      expect(labels).toContain('Inventory')
      expect(labels).toContain('Prepaid Expenses')
      expect(labels).toContain('Total Current Assets')
      expect(labels).toContain('Non-Current Assets')
      expect(labels).toContain('Property, Plant & Equipment')
      expect(labels).toContain('Other Assets & Intangibles')
      expect(labels).toContain('Total Non-Current Assets')
      expect(labels).toContain('TOTAL ASSETS')
      expect(labels).toContain('LIABILITIES & EQUITY')
      expect(labels).toContain('AP & Accrued Liabilities')
      expect(labels).toContain('Other Current Liabilities')
      expect(labels).toContain('Long-term Debt')
      expect(labels).toContain('Other Long-term Liabilities')
      expect(labels).toContain("Stockholders' Equity")
      expect(labels).toContain('TOTAL LIABILITIES & EQUITY')
    })

    it('maps lead sheet letters to correct amounts (assets)', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const bs = result.current.balanceSheet

      const cash = bs.find(i => i.leadSheetRef === 'A')
      expect(cash?.amount).toBe(50000)

      const receivables = bs.find(i => i.leadSheetRef === 'B')
      expect(receivables?.amount).toBe(30000)

      const inventory = bs.find(i => i.leadSheetRef === 'C')
      expect(inventory?.amount).toBe(20000)

      const prepaid = bs.find(i => i.leadSheetRef === 'D')
      expect(prepaid?.amount).toBe(10000)

      const ppe = bs.find(i => i.leadSheetRef === 'E')
      expect(ppe?.amount).toBe(40000)

      const intangibles = bs.find(i => i.leadSheetRef === 'F')
      expect(intangibles?.amount).toBe(15000)
    })

    it('applies sign correction for liability letters (G-J)', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const bs = result.current.balanceSheet

      // G has net_balance = -25000, displayed as -bal('G') = -(-25000) = 25000
      const ap = bs.find(i => i.leadSheetRef === 'G')
      expect(ap?.amount).toBe(25000)

      const otherCl = bs.find(i => i.leadSheetRef === 'H')
      expect(otherCl?.amount).toBe(10000)

      const ltDebt = bs.find(i => i.leadSheetRef === 'I')
      expect(ltDebt?.amount).toBe(30000)

      const otherLt = bs.find(i => i.leadSheetRef === 'J')
      expect(otherLt?.amount).toBe(5000)
    })

    it('applies sign correction for equity letter (K)', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const bs = result.current.balanceSheet

      // K has net_balance = -95000, displayed as -bal('K') = 95000
      const equity = bs.find(i => i.leadSheetRef === 'K')
      expect(equity?.amount).toBe(95000)
    })

    it('calculates subtotals correctly', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const bs = result.current.balanceSheet

      const totalCurrentAssets = bs.find(i => i.label === 'Total Current Assets')
      expect(totalCurrentAssets?.amount).toBe(50000 + 30000 + 20000 + 10000)
      expect(totalCurrentAssets?.isSubtotal).toBe(true)

      const totalNoncurrentAssets = bs.find(i => i.label === 'Total Non-Current Assets')
      expect(totalNoncurrentAssets?.amount).toBe(40000 + 15000)

      const totalAssets = bs.find(i => i.label === 'TOTAL ASSETS')
      expect(totalAssets?.amount).toBe(165000)
      expect(totalAssets?.isTotal).toBe(true)

      const totalCurrentLiabilities = bs.find(i => i.label === 'Total Current Liabilities')
      expect(totalCurrentLiabilities?.amount).toBe(25000 + 10000)

      const totalNoncurrentLiabilities = bs.find(i => i.label === 'Total Non-Current Liabilities')
      expect(totalNoncurrentLiabilities?.amount).toBe(30000 + 5000)

      const totalLiabilities = bs.find(i => i.label === 'Total Liabilities')
      expect(totalLiabilities?.amount).toBe(70000)

      const totalLE = bs.find(i => i.label === 'TOTAL LIABILITIES & EQUITY')
      expect(totalLE?.amount).toBe(70000 + 95000) // 165000
    })

    it('uses indentLevel 0 for section headers and 1 for line items', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const bs = result.current.balanceSheet

      const assetsHeader = bs.find(i => i.label === 'ASSETS')
      expect(assetsHeader?.indentLevel).toBe(0)

      const cashLine = bs.find(i => i.label === 'Cash and Cash Equivalents')
      expect(cashLine?.indentLevel).toBe(1)
    })
  })

  // ========================================================================
  // 3. Income statement line items
  // ========================================================================
  describe('income statement', () => {
    it('includes all expected line items', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const labels = result.current.incomeStatement.map(i => i.label)

      expect(labels).toContain('Revenue')
      expect(labels).toContain('Cost of Goods Sold')
      expect(labels).toContain('GROSS PROFIT')
      expect(labels).toContain('Operating Expenses')
      expect(labels).toContain('OPERATING INCOME')
      expect(labels).toContain('Other Income / (Expense), Net')
      expect(labels).toContain('NET INCOME')
    })

    it('applies sign correction for revenue (L) and other income (O)', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const is = result.current.incomeStatement

      // L has net_balance = -100000, displayed as -bal('L') = 100000
      const revenue = is.find(i => i.leadSheetRef === 'L')
      expect(revenue?.amount).toBe(100000)

      // O has net_balance = -5000, displayed as -bal('O') = 5000
      const other = is.find(i => i.leadSheetRef === 'O')
      expect(other?.amount).toBe(5000)
    })

    it('does NOT sign-correct expenses (M, N)', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const is = result.current.incomeStatement

      const cogs = is.find(i => i.leadSheetRef === 'M')
      expect(cogs?.amount).toBe(60000)

      const opex = is.find(i => i.leadSheetRef === 'N')
      expect(opex?.amount).toBe(30000)
    })

    it('calculates gross profit, operating income, and net income', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const is = result.current.incomeStatement

      const grossProfit = is.find(i => i.label === 'GROSS PROFIT')
      expect(grossProfit?.amount).toBe(100000 - 60000) // 40000

      const operatingIncome = is.find(i => i.label === 'OPERATING INCOME')
      expect(operatingIncome?.amount).toBe(40000 - 30000) // 10000

      const netIncome = is.find(i => i.label === 'NET INCOME')
      expect(netIncome?.amount).toBe(10000 + 5000) // 15000
    })

    it('marks GROSS PROFIT and OPERATING INCOME as subtotals, NET INCOME as total', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const is = result.current.incomeStatement

      const grossProfit = is.find(i => i.label === 'GROSS PROFIT')
      expect(grossProfit?.isSubtotal).toBe(true)
      expect(grossProfit?.isTotal).toBe(false)

      const operatingIncome = is.find(i => i.label === 'OPERATING INCOME')
      expect(operatingIncome?.isSubtotal).toBe(true)

      const netIncome = is.find(i => i.label === 'NET INCOME')
      expect(netIncome?.isTotal).toBe(true)
    })
  })

  // ========================================================================
  // 4. Totals
  // ========================================================================
  describe('totals', () => {
    it('calculates totalAssets, totalLiabilities, totalEquity correctly', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const { totals } = result.current

      // Assets: A(50k) + B(30k) + C(20k) + D(10k) + E(40k) + F(15k) = 165k
      expect(totals.totalAssets).toBe(165000)
      // Liabilities: G(25k) + H(10k) + I(30k) + J(5k) = 70k
      expect(totals.totalLiabilities).toBe(70000)
      // Equity: K = 95k
      expect(totals.totalEquity).toBe(95000)
    })

    it('calculates income statement totals correctly', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const { totals } = result.current

      expect(totals.totalRevenue).toBe(100000)
      expect(totals.grossProfit).toBe(40000)
      expect(totals.operatingIncome).toBe(10000)
      expect(totals.netIncome).toBe(15000)
    })
  })

  // ========================================================================
  // 5. isBalanced = true when assets === liabilities + equity
  // ========================================================================
  describe('balance check', () => {
    it('isBalanced is true when assets equal liabilities plus equity', () => {
      // Default grouping: assets = 165k, liabilities + equity = 70k + 95k = 165k
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(result.current.totals.isBalanced).toBe(true)
      expect(result.current.totals.balanceDifference).toBe(0)
    })

    it('isBalanced is true for negligible rounding differences (< $0.01)', () => {
      // Tweak cash by a tiny amount that keeps abs(diff) < 0.01
      const grouping = makeFullGrouping({ A: 50000.005 })
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(result.current.totals.isBalanced).toBe(true)
    })

    // ====================================================================
    // 6. isBalanced = false when they don't match
    // ====================================================================
    it('isBalanced is false when there is a meaningful difference', () => {
      // Increase assets by $1000 without offsetting
      const grouping = makeFullGrouping({ A: 51000 })
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(result.current.totals.isBalanced).toBe(false)
      expect(result.current.totals.balanceDifference).toBe(1000)
    })

    it('balanceDifference is negative when L&E exceeds assets', () => {
      // Decrease assets
      const grouping = makeFullGrouping({ A: 49000 })
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(result.current.totals.isBalanced).toBe(false)
      expect(result.current.totals.balanceDifference).toBe(-1000)
    })
  })

  // ========================================================================
  // 7. Cash flow with prior period data
  // ========================================================================
  describe('cash flow with prior period', () => {
    it('generates cash flow with operating/investing/financing sections', () => {
      const current = makeFullGrouping()
      const prior = makeFullGrouping({
        A: 40000,
        B: 25000,
        C: 18000,
        D: 8000,
        E: 35000,
        F: 12000,
        G: -22000,
        H: -8000,
        I: -28000,
        J: -4000,
        K: -80000, // lower equity in prior (will include retained earnings change)
      })

      const { result } = renderHook(() => useStatementBuilder(current, prior))
      const { cashFlow } = result.current

      expect(cashFlow.hasPriorPeriod).toBe(true)
    })

    it('includes working capital changes in operating activities', () => {
      const current = makeFullGrouping()
      const prior = makeFullGrouping({
        B: 25000, // AR increased by 5000
        C: 18000, // Inventory increased by 2000
        D: 8000,  // Prepaid increased by 2000
        G: -22000, // AP increased by 3000 (more negative = more AP)
        H: -8000,  // Other CL increased by 2000
      })

      const { result } = renderHook(() => useStatementBuilder(current, prior))
      const opItems = result.current.cashFlow.operating.items

      const arChange = opItems.find(i => i.label === 'Change in Accounts Receivable')
      // change('B') = 30000 - 25000 = 5000; displayed as -5000
      expect(arChange?.amount).toBe(-5000)

      const invChange = opItems.find(i => i.label === 'Change in Inventory')
      expect(invChange?.amount).toBe(-2000)

      const prepaidChange = opItems.find(i => i.label === 'Change in Prepaid Expenses')
      expect(prepaidChange?.amount).toBe(-2000)

      const apChange = opItems.find(i => i.label === 'Change in Accounts Payable')
      // change('G') = -25000 - (-22000) = -3000; displayed as -(-3000) = 3000
      expect(apChange?.amount).toBe(3000)

      const accruedChange = opItems.find(i => i.label === 'Change in Accrued Liabilities')
      expect(accruedChange?.amount).toBe(2000)
    })

    it('includes investing activities from PPE and intangibles changes', () => {
      const current = makeFullGrouping()
      const prior = makeFullGrouping({
        E: 35000, // PPE increased by 5000
        F: 12000, // Intangibles increased by 3000
      })

      const { result } = renderHook(() => useStatementBuilder(current, prior))
      const invItems = result.current.cashFlow.investing.items

      const capex = invItems.find(i => i.label === 'Capital Expenditures (PPE)')
      // change('E') = 40000 - 35000 = 5000; displayed as -5000
      expect(capex?.amount).toBe(-5000)

      const otherAssets = invItems.find(i => i.label === 'Change in Other Non-Current Assets')
      expect(otherAssets?.amount).toBe(-3000)
    })

    it('includes financing activities from debt and equity changes', () => {
      const current = makeFullGrouping()
      const prior = makeFullGrouping({
        I: -28000, // Long-term debt increased by 2000 (more negative)
        J: -4000,  // Other LT liabilities increased by 1000
        K: -80000, // Equity changed (from -80k to -95k)
      })

      const { result } = renderHook(() => useStatementBuilder(current, prior))
      const finItems = result.current.cashFlow.financing.items

      const debtChange = finItems.find(i => i.label === 'Change in Long-Term Debt')
      // change('I') = -30000 - (-28000) = -2000; displayed as -(-2000) = 2000
      expect(debtChange?.amount).toBe(2000)

      const otherLt = finItems.find(i => i.label === 'Change in Other Long-Term Liabilities')
      expect(otherLt?.amount).toBe(1000)
    })

    it('excludes retained earnings from equity financing change', () => {
      // The hook subtracts netIncome from the equity change to isolate
      // equity changes excluding retained earnings
      const current = makeFullGrouping()
      // Prior equity = -80000; current equity = -95000
      // deltaK = -95000 - (-80000) = -15000
      // equityChangeDisplayed = -deltaK = 15000
      // financingEquityChange = 15000 - netIncome(15000) = 0
      // So equity financing line should NOT appear (it's 0)
      const prior = makeFullGrouping({ K: -80000 })

      const { result } = renderHook(() => useStatementBuilder(current, prior))
      const finItems = result.current.cashFlow.financing.items

      const equityChange = finItems.find(i => i.label === 'Equity Changes (excl. Retained Earnings)')
      expect(equityChange).toBeUndefined()
    })

    it('shows equity financing change when there are non-retained-earnings equity changes', () => {
      const current = makeFullGrouping()
      // Prior equity = -70000; current equity = -95000
      // deltaK = -95000 - (-70000) = -25000
      // equityChangeDisplayed = -(-25000) = 25000
      // financingEquityChange = 25000 - 15000(netIncome) = 10000
      const prior = makeFullGrouping({ K: -70000 })

      const { result } = renderHook(() => useStatementBuilder(current, prior))
      const finItems = result.current.cashFlow.financing.items

      const equityChange = finItems.find(i => i.label === 'Equity Changes (excl. Retained Earnings)')
      expect(equityChange).toBeDefined()
      expect(equityChange?.amount).toBe(10000)
    })

    it('calculates netChange as sum of all section subtotals', () => {
      const current = makeFullGrouping()
      const prior = makeFullGrouping({
        A: 40000,
        B: 25000,
        E: 35000,
        G: -22000,
        I: -28000,
        K: -80000,
      })

      const { result } = renderHook(() => useStatementBuilder(current, prior))
      const { cashFlow } = result.current

      expect(cashFlow.netChange).toBe(
        cashFlow.operating.subtotal + cashFlow.investing.subtotal + cashFlow.financing.subtotal
      )
    })

    it('sets beginningCash and endingCash correctly', () => {
      const current = makeFullGrouping()
      const prior = makeFullGrouping({ A: 40000 })

      const { result } = renderHook(() => useStatementBuilder(current, prior))
      const { cashFlow } = result.current

      expect(cashFlow.endingCash).toBe(50000)
      expect(cashFlow.beginningCash).toBe(40000)
    })

    it('reconciles when beginning + netChange equals ending cash', () => {
      // Build a scenario where all changes are consistent:
      // Only cash and receivables changed, no other changes
      const current = makeFullGrouping()
      const prior = makeFullGrouping({
        A: 40000,  // Cash was 40k, now 50k
        B: 40000,  // AR was 40k, now 30k (collected 10k)
        // K stays same = -95000; net income = 15000
        // With same K, deltaK = 0, equityChangeDisplayed = 0
        // financingEquityChange = 0 - 15000 = -15000
      })

      const { result } = renderHook(() => useStatementBuilder(current, prior))
      const { cashFlow } = result.current

      // Operating: netIncome(15000) + AR change (-(30000-40000)) = 15000 + 10000 = 25000
      // Financing: equity change excl RE = -15000
      // Net change = 25000 + 0 + (-15000) = 10000
      // Beginning = 40000, Ending = 50000, difference = 10000
      expect(cashFlow.beginningCash + cashFlow.netChange).toBe(cashFlow.endingCash)
      expect(cashFlow.isReconciled).toBe(true)
      expect(cashFlow.reconciliationDifference).toBe(0)
    })

    it('always includes depreciation note', () => {
      const current = makeFullGrouping()
      const prior = makeFullGrouping()

      const { result } = renderHook(() => useStatementBuilder(current, prior))

      expect(result.current.cashFlow.notes).toContain(
        'Depreciation add-back available in PDF/Excel export only'
      )
    })
  })

  // ========================================================================
  // 8. Cash flow without prior period
  // ========================================================================
  describe('cash flow without prior period', () => {
    it('sets hasPriorPeriod to false when no prior grouping provided', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(result.current.cashFlow.hasPriorPeriod).toBe(false)
    })

    it('sets hasPriorPeriod to false when prior grouping is null', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping, null))

      expect(result.current.cashFlow.hasPriorPeriod).toBe(false)
    })

    it('includes "Prior period required" note', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(result.current.cashFlow.notes).toContain(
        'Prior period required for working capital changes'
      )
    })

    it('operating section only contains Net Income when no prior period', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      const opItems = result.current.cashFlow.operating.items
      expect(opItems).toHaveLength(1)
      expect(opItems[0]!.label).toBe('Net Income')
    })

    it('investing and financing sections are empty when no prior period', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(result.current.cashFlow.investing.items).toHaveLength(0)
      expect(result.current.cashFlow.financing.items).toHaveLength(0)
    })

    it('beginningCash is 0 when no prior period', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(result.current.cashFlow.beginningCash).toBe(0)
    })

    it('isReconciled is false when no prior period', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(result.current.cashFlow.isReconciled).toBe(false)
    })

    it('netChange equals net income when no prior period (only operating item)', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(result.current.cashFlow.netChange).toBe(result.current.totals.netIncome)
    })
  })

  // ========================================================================
  // 9. Mapping trace
  // ========================================================================
  describe('mapping trace', () => {
    it('has entries for all 15 lead sheet letters (A-O)', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      const refs = result.current.mappingTrace.map(e => e.leadSheetRef)
      const expected = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
      expect(refs).toEqual(expected)
    })

    it('maps each entry to the correct statement', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      const trace = result.current.mappingTrace

      const bsLetters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
      const isLetters = ['L', 'M', 'N', 'O']

      for (const entry of trace) {
        if (bsLetters.includes(entry.leadSheetRef)) {
          expect(entry.statement).toBe('Balance Sheet')
        } else if (isLetters.includes(entry.leadSheetRef)) {
          expect(entry.statement).toBe('Income Statement')
        }
      }
    })

    it('includes correct account count and account details', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      const traceA = result.current.mappingTrace.find(e => e.leadSheetRef === 'A')!
      expect(traceA.accountCount).toBe(1)
      expect(traceA.accounts).toHaveLength(1)
      expect(traceA.accounts[0]!.accountName).toBe('Cash')
    })

    it('populates statementAmount from balance sheet / income statement', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      const traceA = result.current.mappingTrace.find(e => e.leadSheetRef === 'A')!
      expect(traceA.statementAmount).toBe(50000)

      const traceL = result.current.mappingTrace.find(e => e.leadSheetRef === 'L')!
      expect(traceL.statementAmount).toBe(100000)
    })

    it('reports isTied when rawAggregate matches net_balance', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      for (const entry of result.current.mappingTrace) {
        expect(entry.isTied).toBe(true)
        expect(entry.tieDifference).toBeLessThan(0.01)
      }
    })

    it('detects untied entries when account debits/credits do not sum to net_balance', () => {
      const grouping = makeFullGrouping()
      // Manually tamper: create accounts whose debit-credit doesn't match net_balance
      const summaryA = grouping.summaries.find(s => s.lead_sheet === 'A')!
      summaryA.accounts = [
        makeAccount('Cash', 40000, 0, { lead_sheet: 'A', lead_sheet_name: 'Cash' }),
      ]
      // net_balance is still 50000 but rawSum = 40000, so tieDiff = 10000

      const { result } = renderHook(() => useStatementBuilder(grouping))
      const traceA = result.current.mappingTrace.find(e => e.leadSheetRef === 'A')!

      expect(traceA.isTied).toBe(false)
      expect(traceA.tieDifference).toBe(10000)
      expect(traceA.rawAggregate).toBe(40000)
    })

    it('handles missing lead sheet letters gracefully', () => {
      // Create grouping with only A and L
      const grouping: LeadSheetGrouping = {
        summaries: [
          makeSummary('A', 'Cash', 50000),
          makeSummary('L', 'Revenue', -100000, undefined, 'revenue'),
        ],
        unmapped_count: 0,
        total_accounts: 2,
      }

      const { result } = renderHook(() => useStatementBuilder(grouping))

      // Should still have 15 trace entries
      expect(result.current.mappingTrace).toHaveLength(15)

      // Missing entries should have 0 accounts and amount 0
      const traceB = result.current.mappingTrace.find(e => e.leadSheetRef === 'B')!
      expect(traceB.accountCount).toBe(0)
      expect(traceB.accounts).toHaveLength(0)
      expect(traceB.isTied).toBe(true)
    })
  })

  // ========================================================================
  // 10. Sign corrections
  // ========================================================================
  describe('sign corrections', () => {
    it('signCorrectionApplied is true for G, H, I, J, K, L, O', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      const correctedLetters = new Set(['G', 'H', 'I', 'J', 'K', 'L', 'O'])
      for (const entry of result.current.mappingTrace) {
        if (correctedLetters.has(entry.leadSheetRef)) {
          expect(entry.signCorrectionApplied).toBe(true)
        } else {
          expect(entry.signCorrectionApplied).toBe(false)
        }
      }
    })

    it('signCorrectionApplied is false for asset and expense letters (A-F, M, N)', () => {
      const grouping = makeFullGrouping()
      const { result } = renderHook(() => useStatementBuilder(grouping))

      const uncorrectedLetters = ['A', 'B', 'C', 'D', 'E', 'F', 'M', 'N']
      for (const letter of uncorrectedLetters) {
        const entry = result.current.mappingTrace.find(e => e.leadSheetRef === letter)!
        expect(entry.signCorrectionApplied).toBe(false)
      }
    })
  })

  // ========================================================================
  // Edge cases
  // ========================================================================
  describe('edge cases', () => {
    it('handles all-zero balances', () => {
      const zeros: Partial<Record<string, number>> = {}
      for (const letter of 'ABCDEFGHIJKLMNO'.split('')) {
        zeros[letter] = 0
      }
      const grouping = makeFullGrouping(zeros)
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(result.current.totals.totalAssets).toBe(0)
      // -bal(letter) where bal returns 0 yields -0 in JS; use toBeCloseTo for numeric equivalence
      expect(result.current.totals.totalLiabilities).toBeCloseTo(0)
      expect(result.current.totals.totalEquity).toBeCloseTo(0)
      expect(result.current.totals.netIncome).toBeCloseTo(0)
      expect(result.current.totals.isBalanced).toBe(true)
    })

    it('handles empty summaries array', () => {
      const grouping: LeadSheetGrouping = {
        summaries: [],
        unmapped_count: 0,
        total_accounts: 0,
      }
      const { result } = renderHook(() => useStatementBuilder(grouping))

      expect(result.current.totals.totalAssets).toBe(0)
      expect(result.current.totals.isBalanced).toBe(true)
      expect(result.current.mappingTrace).toHaveLength(15)
    })

    it('handles negative asset balances (unusual but possible)', () => {
      const grouping = makeFullGrouping({ A: -5000 })
      const { result } = renderHook(() => useStatementBuilder(grouping))

      const cashLine = result.current.balanceSheet.find(i => i.leadSheetRef === 'A')
      expect(cashLine?.amount).toBe(-5000)
    })

    it('handles multiple accounts per lead sheet letter', () => {
      const grouping = makeFullGrouping()
      const summaryA = grouping.summaries.find(s => s.lead_sheet === 'A')!
      summaryA.accounts = [
        makeAccount('Cash on Hand', 20000, 0, { lead_sheet: 'A', lead_sheet_name: 'Cash' }),
        makeAccount('Checking Account', 25000, 0, { lead_sheet: 'A', lead_sheet_name: 'Cash' }),
        makeAccount('Petty Cash', 5000, 0, { lead_sheet: 'A', lead_sheet_name: 'Cash' }),
      ]
      summaryA.account_count = 3

      const { result } = renderHook(() => useStatementBuilder(grouping))

      const traceA = result.current.mappingTrace.find(e => e.leadSheetRef === 'A')!
      expect(traceA.accountCount).toBe(3)
      expect(traceA.accounts).toHaveLength(3)
      expect(traceA.rawAggregate).toBe(50000)
      expect(traceA.isTied).toBe(true)
    })

    it('omits cash flow line items below CHANGE_THRESHOLD (0.005)', () => {
      const current = makeFullGrouping()
      const prior = makeFullGrouping({
        B: 30000.003, // delta = 30000 - 30000.003 = -0.003, abs < 0.005
      })

      const { result } = renderHook(() => useStatementBuilder(current, prior))
      const opItems = result.current.cashFlow.operating.items

      const arChange = opItems.find(i => i.label === 'Change in Accounts Receivable')
      expect(arChange).toBeUndefined()
    })

    it('confidence values pass through to mapping trace accounts', () => {
      const grouping = makeFullGrouping()
      const summaryA = grouping.summaries.find(s => s.lead_sheet === 'A')!
      summaryA.accounts = [
        makeAccount('Cash', 50000, 0, {
          lead_sheet: 'A',
          lead_sheet_name: 'Cash',
          confidence: 0.85,
        }),
      ]

      const { result } = renderHook(() => useStatementBuilder(grouping))
      const traceA = result.current.mappingTrace.find(e => e.leadSheetRef === 'A')!
      expect(traceA.accounts[0]!.confidence).toBe(0.85)
    })

    it('defaults confidence to 1 when not provided', () => {
      const grouping = makeFullGrouping()
      // Default accounts don't explicitly set confidence in their lead sheet account
      // but our makeAccount helper defaults to 1, and the hook reads acct.confidence ?? 1
      const { result } = renderHook(() => useStatementBuilder(grouping))
      const traceA = result.current.mappingTrace.find(e => e.leadSheetRef === 'A')!
      expect(traceA.accounts[0]!.confidence).toBe(1)
    })
  })
})
