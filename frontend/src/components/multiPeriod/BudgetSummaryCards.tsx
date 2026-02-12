import type { MovementSummaryResponse } from '@/hooks'

export function BudgetSummaryCards({ comparison }: { comparison: MovementSummaryResponse }) {
  if (!comparison.budget_label) return null
  return (
    <div className="theme-card p-4">
      <h3 className="font-serif text-sm text-content-secondary mb-3">
        Budget Variance: {comparison.current_label} vs {comparison.budget_label}
      </h3>
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className="text-xl font-mono font-bold text-sage-600">{comparison.accounts_over_budget || 0}</div>
          <div className="text-xs font-sans text-content-tertiary">Over Budget</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-mono font-bold text-clay-600">{comparison.accounts_under_budget || 0}</div>
          <div className="text-xs font-sans text-content-tertiary">Under Budget</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-mono font-bold text-content-secondary">{comparison.accounts_on_budget || 0}</div>
          <div className="text-xs font-sans text-content-tertiary">On Budget</div>
        </div>
      </div>
    </div>
  )
}
