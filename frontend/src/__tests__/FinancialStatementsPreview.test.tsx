/**
 * Sprint 808 — finding D-7: the out-of-balance warning hedged about information
 * it was already holding.
 *
 * The component rendered *"Balance Sheet is out of balance by $X. This may
 * indicate unclassified accounts or mapping gaps."* while the payload it was
 * rendering carried `unclassified_count` and — on the lead sheet Z summary — the
 * account names. A diagnostic product telling the practitioner something *may*
 * be wrong while holding the exact answer is the whole of the finding.
 *
 * Two things the review did not catch, found while implementing it and covered
 * here:
 *
 * 1. The warning only fired when the balance sheet failed to foot. Unclassified
 *    accounts are excluded from **both** statements, so net income is wrong by
 *    their sum whether or not the balance sheet happens to balance — a dropped
 *    expense line and a dropped revenue line of equal size leave it footing
 *    perfectly. The list must appear independently of `isBalanced`.
 * 2. `frontend/src/types/leadSheet.ts` declared `unmapped_count`, which the API
 *    has never sent — the serializer emits `unclassified_count`. The one place
 *    the UI tried to surface the count guarded on `undefined > 0`, so it had
 *    never rendered for any upload. That is why the hedging warning was the
 *    only signal a practitioner ever got.
 */

import { fireEvent, render, screen } from '@testing-library/react'
import { FinancialStatementsPreview } from '@/components/financialStatements/FinancialStatementsPreview'
import type { LeadSheetAccount, LeadSheetGrouping, LeadSheetSummary } from '@/types/leadSheet'

// A proxy mock, so any `motion.<tag>` the subtree reaches for resolves. The
// first draft enumerated `div` and `svg` and fell over inside `ExportButton`,
// which uses another tag — an enumerated mock is the same
// list-that-stops-matching shape as finding D-4.
jest.mock('framer-motion', () => {
  const React = require('react')
  const MOTION_PROPS = new Set([
    'initial',
    'animate',
    'exit',
    'transition',
    'variants',
    'whileHover',
    'whileTap',
    'whileFocus',
    'whileInView',
    'viewport',
    'layout',
    'layoutId',
    'drag',
    'custom',
  ])
  const strip = (props: Record<string, unknown>) =>
    Object.fromEntries(Object.entries(props).filter(([key]) => !MOTION_PROPS.has(key)))

  return {
    motion: new Proxy(
      {},
      {
        get: (_target, tag: string) => {
          const Component = ({ children, ...rest }: any) =>
            React.createElement(tag, strip(rest), children)
          Component.displayName = `motion.${tag}`
          return Component
        },
      }
    ),
    AnimatePresence: ({ children }: any) => React.createElement(React.Fragment, null, children),
    useReducedMotion: () => true,
    useInView: () => true,
  }
})

jest.mock('@/utils/apiClient', () => ({
  apiDownload: jest.fn(),
  downloadBlob: jest.fn(),
}))

function account(name: string, debit: number, credit: number, letter: string): LeadSheetAccount {
  return {
    account: name,
    debit,
    credit,
    confidence: letter === 'Z' ? 0.5 : 0.95,
    lead_sheet: letter as LeadSheetAccount['lead_sheet'],
    lead_sheet_name: letter,
    match_reason: 'test',
  }
}

function summary(letter: string, netBalance: number, accounts: LeadSheetAccount[]): LeadSheetSummary {
  return {
    lead_sheet: letter as LeadSheetSummary['lead_sheet'],
    lead_sheet_name: letter,
    category: 'asset',
    accounts,
    total_debit: accounts.reduce((t, a) => t + a.debit, 0),
    total_credit: accounts.reduce((t, a) => t + a.credit, 0),
    net_balance: netBalance,
    account_count: accounts.length,
  }
}

/** A balanced grouping with `unclassifiedNames` sitting on lead sheet Z. */
function grouping(unclassifiedNames: string[], opts?: { balanced?: boolean }): LeadSheetGrouping {
  const balanced = opts?.balanced ?? true
  const summaries: LeadSheetSummary[] = [
    summary('A', 100_000, [account('Cash - Operating', 100_000, 0, 'A')]),
    summary('K', balanced ? -100_000 : -40_000, [
      account('Common Stock', 0, balanced ? 100_000 : 40_000, 'K'),
    ]),
  ]
  if (unclassifiedNames.length) {
    summaries.push(
      summary(
        'Z',
        0,
        unclassifiedNames.map(name => account(name, 0, 0, 'Z'))
      )
    )
  }
  return {
    summaries,
    unclassified_count: unclassifiedNames.length,
    unclassified_accounts: unclassifiedNames,
    total_accounts: summaries.reduce((t, s) => t + s.account_count, 0),
  }
}

const baseProps = { filename: 'tb.xlsx', token: 'tok' }

/** Render with the section collapsed, as it first appears. */
function renderCollapsed(g: LeadSheetGrouping) {
  return render(<FinancialStatementsPreview leadSheetGrouping={g} {...baseProps} />)
}

/**
 * Render and expand.
 *
 * The statement body — and the unclassified warning with it — lives inside a
 * collapsed `AnimatePresence` block, so every assertion about the warning has
 * to open the section first. Asserting absence without expanding would pass for
 * the wrong reason: nothing is in the DOM yet.
 */
function renderExpanded(g: LeadSheetGrouping) {
  const result = renderCollapsed(g)
  fireEvent.click(screen.getByText('Financial Statements'))
  return result
}

describe('FinancialStatementsPreview — unclassified accounts (D-7)', () => {
  it('names every unclassified account instead of saying one "may" exist', () => {
    renderExpanded(grouping(['Salaries and Wages Expense', 'Owner’s Draw', 'Lease Liability']))

    expect(screen.getByText(/3 accounts could not be classified/i)).toBeInTheDocument()
    expect(screen.getByText('Salaries and Wages Expense')).toBeInTheDocument()
    expect(screen.getByText('Owner’s Draw')).toBeInTheDocument()
    expect(screen.getByText('Lease Liability')).toBeInTheDocument()
  })

  it('does not hedge with "may indicate"', () => {
    renderExpanded(grouping(['Salaries Expense']))

    expect(screen.queryByText(/may indicate/i)).not.toBeInTheDocument()
  })

  it('says what is wrong with the numbers, not merely that something is', () => {
    renderExpanded(grouping(['Salaries Expense']))

    // The measured consequence: net income is wrong by the dropped amount.
    expect(screen.getByText(/Net Income is wrong by/i)).toBeInTheDocument()
  })

  it('points at the Classification Validator, which is where the fix is', () => {
    renderExpanded(grouping(['Salaries Expense']))

    expect(screen.getByText(/Classification Validator/i)).toBeInTheDocument()
  })

  it('warns even when the balance sheet foots', () => {
    // The case the old warning could not reach. Two dropped accounts of equal
    // and opposite sign leave the balance sheet balanced and net income wrong.
    renderExpanded(grouping(['Salaries Expense', 'Consulting Income'], { balanced: true }))

    expect(screen.getByText(/2 accounts could not be classified/i)).toBeInTheDocument()
    expect(screen.queryByText(/out of balance/i)).not.toBeInTheDocument()
  })

  it('marks the statements PROVISIONAL on the collapsed header', () => {
    // Visible without expanding: the practitioner may never open the section.
    renderCollapsed(grouping(['Salaries Expense']))

    expect(screen.getByText('PROVISIONAL')).toBeInTheDocument()
  })

  it('uses singular wording for a single account', () => {
    renderExpanded(grouping(['Salaries Expense']))

    expect(screen.getByText(/1 account could not be classified/i)).toBeInTheDocument()
    expect(screen.queryByText(/1 accounts could not/i)).not.toBeInTheDocument()
  })

  describe('the zero state', () => {
    it('shows no unclassified warning and no provisional badge', () => {
      renderExpanded(grouping([]))
      // Sanity: the section really is open, so the absences below mean something.
      expect(screen.getByText('Balance Sheet')).toBeInTheDocument()

      expect(screen.queryByText(/could not be classified/i)).not.toBeInTheDocument()
      expect(screen.queryByText('PROVISIONAL')).not.toBeInTheDocument()
      expect(screen.queryByTestId('unclassified-account-list')).not.toBeInTheDocument()
    })

    it('an imbalance with nothing unclassified gets different words', () => {
      // A coverage gap and a mapping error are different problems, and telling
      // the practitioner to go resolve unclassified accounts when there are
      // none is the same failure as hedging.
      renderExpanded(grouping([], { balanced: false }))

      // "out of balance" appears twice — the header badge and the warning body.
      expect(screen.getByText('OUT OF BALANCE')).toBeInTheDocument()
      expect(screen.getByText(/mapping or sign issue rather than a coverage gap/i)).toBeInTheDocument()
    })
  })

  describe('the contract the API actually sends', () => {
    it('falls back to the lead sheet Z summary when the explicit list is absent', () => {
      // An older cached payload has no `unclassified_accounts`. Naming the
      // accounts from the Z summary is better than showing an empty list.
      const g = grouping(['Salaries Expense'])
      const legacy = {
        ...g,
        unclassified_accounts: [] as string[],
      } as LeadSheetGrouping

      renderExpanded(legacy)

      expect(screen.getByText('Salaries Expense')).toBeInTheDocument()
    })
  })
})
