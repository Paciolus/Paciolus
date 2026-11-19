import type { BankRecResult } from '@/types/bankRec'

/**
 * Sprint 886 (review OUT-10): the run's reconciliation tests, composite score
 * and outstanding-item aging. The engine always produced them and the memo is
 * built around them, but the screen never showed them, so the memo and CSV
 * carried figures the reviewer could not compare. Same labels and one-decimal
 * score as the memo and CSV. A block the response did not carry says so.
 */

const AGING_LABELS: Record<string, string> = { bank_only: 'Bank only', ledger_only: 'Ledger only' }

function formatAmount(value: number): string {
  return `$${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function BankRecTestsPanel({ result }: { result: BankRecResult }) {
  const composite = result.composite_score ?? null
  const tests = result.rec_tests ?? null
  const aging = result.outstanding_aging ?? null

  return (
    <div className="theme-card p-4" data-testid="bank-rec-tests-panel">
      <h3 className="font-serif text-sm text-content-primary mb-3">Reconciliation tests</h3>

      <dl className="flex flex-wrap gap-x-6 gap-y-1 mb-3" data-testid="bank-rec-score">
        <div className="flex gap-2 items-baseline">
          <dt className="font-sans text-xs text-content-secondary">Composite diagnostic score</dt>
          <dd className="font-mono text-sm text-content-primary">
            {composite ? `${composite.score.toFixed(1)} / 100` : 'Not available'}
          </dd>
        </div>
        <div className="flex gap-2 items-baseline">
          <dt className="font-sans text-xs text-content-secondary">Diagnostic tier</dt>
          <dd className="font-mono text-sm text-content-primary">
            {composite ? composite.risk_tier.toUpperCase() : 'Not evaluated'}
          </dd>
        </div>
      </dl>

      {tests ? (
        <table className="w-full text-xs font-sans mb-3" data-testid="bank-rec-tests">
          <thead>
            <tr className="text-left text-content-secondary">
              <th className="font-medium py-1">Test</th>
              <th className="font-medium py-1 text-right">Items flagged</th>
              <th className="font-medium py-1 text-right">Severity</th>
            </tr>
          </thead>
          <tbody>
            {tests.map((t) => (
              <tr key={t.test_name} className="border-t border-theme">
                <td className="py-1 text-content-primary">{t.test_name}</td>
                <td className="py-1 text-right font-mono text-content-primary">{t.flagged_count}</td>
                <td className={`py-1 text-right font-mono ${t.flagged_count > 0 && t.severity === 'high' ? 'text-clay-600' : 'text-content-secondary'}`}>
                  {t.severity.toUpperCase()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="font-sans text-xs text-content-secondary mb-3">Reconciliation tests: Not available</p>
      )}

      <h4 className="font-serif text-xs text-content-primary mb-1">Outstanding items aging</h4>
      {aging ? (
        <table className="w-full text-xs font-sans" data-testid="bank-rec-aging">
          <thead>
            <tr className="text-left text-content-secondary">
              <th className="font-medium py-1">Category</th>
              <th className="font-medium py-1 text-right">Items</th>
              <th className="font-medium py-1 text-right">Over 10 days</th>
              <th className="font-medium py-1 text-right">Over 30 days</th>
              <th className="font-medium py-1 text-right">Oldest item</th>
            </tr>
          </thead>
          <tbody>
            {aging.map((a) => (
              <tr key={a.category} className="border-t border-theme">
                <td className="py-1 text-content-primary">{AGING_LABELS[a.category] ?? a.category}</td>
                <td className="py-1 text-right font-mono text-content-primary">{a.total_count}</td>
                <td className="py-1 text-right font-mono text-content-primary">{a.over_10_days}</td>
                <td className="py-1 text-right font-mono text-content-primary">{a.over_30_days}</td>
                <td className="py-1 text-right font-mono text-content-secondary">
                  {a.oldest_item_days !== null
                    ? `${a.oldest_item_days} days (${a.oldest_item_date ?? 'date not available'})${a.oldest_item_amount !== null ? `, ${formatAmount(a.oldest_item_amount)}` : ''}`
                    : 'Not available'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="font-sans text-xs text-content-secondary">Aging: Not available</p>
      )}
      <p className="font-sans text-xs text-content-tertiary mt-2">
        Ages are measured to the latest date in the bank statement.
      </p>
    </div>
  )
}
