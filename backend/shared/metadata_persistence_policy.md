# Metadata Persistence Policy

> **Engineering guidance.** The authoritative, customer-facing statement is
> [`docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md`](../../docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md).
> **Where the two differ, the compliance document wins** — it is the one
> customers and auditors are shown. This file exists to answer the narrower
> question an engineer has: *may I persist this?*
>
> **Rewritten 2026-10-22 (Sprint 801).** The Sprint 96.5 version of this file
> listed 8 tables under a heading that read as exhaustive, when the schema
> held 29, and stated flatly that there is *"no foreign key or reference to
> any specific account, amount, or transaction"* — which three shipped tables
> contradict, all of them disclosed correctly in the compliance document.
> That inverted the usual risk: the externally-audited document was right and
> the internal engineering guidance was wrong in the **permissive** direction,
> describing a stricter system than exists, so a reader could not tell which
> new persistence was a violation and which was precedent.
>
> The table inventory has been removed rather than corrected. A hand-copied
> list of 29 tables would be stale within a sprint; the rules below are what
> a reader actually needs, and `Base.metadata` is the inventory.

## Core principle

Paciolus persists **metadata and the practitioner's own conclusions**. The
uploaded file, and the line-level account/balance/transaction detail parsed
out of it, are processed in memory and never written to disk or database.

## The decision rule

Ask where the value came from.

| Origin | Persist? |
|--------|----------|
| Parsed out of an uploaded file | **No** — ephemeral, discarded after the response |
| Computed *aggregate* over an upload (totals, ratios, counts, scores) | Yes |
| An identifier the tool *flagged*, with no amount attached | Yes — see below |
| Typed by the practitioner as their own conclusion | Yes — see below |
| Authentication, billing, client/engagement workflow | Yes |

"Aggregate" means it does not reconstruct a row. `total_assets` is an
aggregate; a per-account balance is not, however few accounts there are.

## The three deliberate exceptions

These exist, are intentional, and are disclosed in the compliance document.
They are listed here because the previous version of this file denied them,
and a rule that the code visibly breaks gets ignored wholesale.

1. **`tool_runs.flagged_accounts`** — the account *names* a tool flagged,
   as a JSON list of strings. Identifiers only, **never balances**. This is
   structural chart-of-accounts metadata, the same class as a lead-sheet
   mapping. Produced only by the seven extractors in
   `shared/account_extractors.py`, each of which copies an account-name field
   and nothing else; `tests/test_account_extractors_zero_storage.py` enforces
   that no amount can reach the column.

2. **`uncorrected_misstatements`** — the ISA 450 summary of uncorrected
   misstatements. `accounts_affected_json` holds account names with DR/CR and
   amounts, and `fs_impact_net_income` / `fs_impact_net_assets` hold signed
   figures. This is the auditor's **own** decision record, typed by them, not
   data extracted from a client file.

3. **`analytical_expectations`** — the ISA 520 expectation, its precision
   threshold, and the single actual it is compared against. Again the
   practitioner's input plus one computed comparison, not a population.

The distinction that makes all three consistent with Zero-Storage: we never
retain *the client's data*; we do retain *the auditor's workpaper*.

## Prohibited in engagement, tool-run and follow-up tables

Per AccountingExpertAuditor Guardrail 2, outside the three exceptions above:

- `account_number`
- `account_name`
- `amount` / `debit` / `credit`
- `transaction_id` / `entry_id`
- `vendor_name` / `employee_name`
- Any personally identifiable information (PII)

`follow_up_items` in particular is narrative-only: *"Round amount entries
detected: 47 entries flagged"*, never *"Account 1000-Cash: $50,000 round
amount on entry JE-2024-0123"*.

## UI expectations for stale references

Financial detail is ephemeral, so the engagement workspace cannot re-display
a past tool run's results.

| Scenario | UI behaviour |
|----------|--------------|
| User views an engagement | Tool name, run date, composite score, status badge |
| User clicks "View Details" on a past run | "Re-run this tool to view detailed results. Original data was processed in-memory and is no longer available." |
| Follow-up item references a past run | Narrative description, severity, disposition. No drill-down. |
| User exports an engagement package | Anomaly summary (narratives), workpaper index, manifest. Not the uploaded files. |

## Adding a new persisted column

1. Apply the decision rule above.
2. If it is an amount or an identifier from an upload, it does not go in the
   database — pass it through the response instead.
3. If you believe you have a fourth exception, it needs the same treatment as
   the three above: a stated reason here **and** a row in
   `docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md`, because that is the
   document the customer is shown.
