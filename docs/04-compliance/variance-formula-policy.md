# Variance Formula Policy

**Status:** Active — Sprint 765 (2026-04-30)
**Scope:** Every Paciolus endpoint that emits a percent variance, percent change, or budget variance percent.

---

## Formula

```
percent_variance = (current - prior) / abs(prior) * 100
```

The **denominator basis is `abs(prior)`** — the absolute value of the prior-period balance.  This is the canonical "absolute prior" basis.  It is consistent across:

- `multi_period_comparison.compare_trial_balances` (prior ↔ current account movements)
- `multi_period_comparison.compare_three_periods` (prior ↔ current ↔ budget; both the period and budget comparisons use this basis)
- `prior_period_comparison.calculate_variance` (current ↔ prior diagnostic summary)
- Lead-sheet summary aggregates within all of the above

## Why absolute prior

Two reasonable conventions exist for percent-change denominators:

1. **Signed prior** — `(current - prior) / prior * 100`.  Preserves the sign of the prior balance, but produces sign-flipped percentages on credit-normal accounts (liabilities, equity, revenue), which is counter-intuitive in audit workpapers.
2. **Absolute prior** — `(current - prior) / abs(prior) * 100`.  Yields a percent whose sign tracks the *direction of change in the absolute amount*, regardless of whether the underlying balance is debit-normal or credit-normal.

Paciolus uses **absolute prior** because it produces audit-intuitive output: a 10% positive percent variance on a liability and a 10% positive percent variance on an asset both mean "the absolute balance grew by 10%."  Display sign-flips (so a liability *increase* shows as positive) are handled separately at the response layer via `display_change_amount` / `display_change_percent` for credit-normal categories.

## Near-zero guard

When `abs(prior) <= NEAR_ZERO` (constant `0.005`), `percent_variance` is set to `null` rather than computed.  This avoids divide-by-near-zero amplification on dormant or newly-created accounts.  Consumers must treat `null` as "not meaningfully expressible as a percentage" and rely on `dollar_variance` / `change_amount` instead.

## Disclosure on the wire

Every variance-emitting response surfaces:

```json
{
  "variance_basis": "absolute_prior",
  "variance_formula": "(current - prior) / abs(prior) * 100"
}
```

Memos, PDFs, and downstream consumers should render the formula alongside any percent variance figure.  The contract test `backend/tests/test_variance_basis_contract.py` enforces that the declared basis matches the actual computation across all variance-emitting code paths.

## Migration / change policy

Changing the basis (e.g., to signed prior) is a breaking change that affects every memo, PDF, and historical comparison.  It would require:

1. A new policy document superseding this one.
2. Updates to all `to_dict()` paths emitting `variance_basis`.
3. Recomputation of any cached prior-period comparisons.
4. Stakeholder review (CEO + audit lead) — auditor judgments based on prior basis would be invalidated.

This is intentionally high-friction.  The basis should be considered stable.

## Related

- `backend/prior_period_comparison.py:VARIANCE_BASIS`, `VARIANCE_FORMULA`
- `backend/multi_period_comparison.py:VARIANCE_BASIS`, `VARIANCE_FORMULA`
- `backend/tests/test_variance_basis_contract.py`
- ASC 205-10 (comparative statements) — discloses comparative basis but does not prescribe a denominator convention; this policy makes the convention explicit.
