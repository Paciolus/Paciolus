# Metadata Persistence Policy

> **Sprint 96.5** — Documents the boundary between persistent metadata and ephemeral financial data in Paciolus.

## Core Principle: Zero-Storage for Financial Data

Paciolus persists **metadata only**. All financial data (trial balances, journal entries, AP payments, payroll records, bank statements, receipts) is processed in-memory and **never written to disk or database**.

## What Persists (Database Tables)

| Table | Data Type | Purpose | Phase |
|-------|-----------|---------|-------|
| `users` | Credentials, settings, tier | Authentication & preferences | Phase I |
| `activity_logs` | Aggregate stats (row count, totals, anomaly counts) | Audit history dashboard | Phase I |
| `clients` | Name, industry, fiscal year end | Multi-tenant client identification | Phase I |
| `diagnostic_summaries` | Category totals, calculated ratios | Trend analysis & variance tracking | Phase II |
| `email_verification_tokens` | Token, expiry, usage status | Email verification flow | Phase V |
| `engagements` | client_id, period, status, materiality_threshold | Engagement workflow tracking | Phase X |
| `tool_runs` | tool_name, run_number, composite_score, timestamp | Tool execution metadata | Phase X |
| `follow_up_items` | description (text), severity, disposition, notes | Narrative-only anomaly tracker | Phase X |

## What Is Ephemeral (Never Persisted)

| Data Type | Source | Lifecycle |
|-----------|--------|-----------|
| Trial balance rows | CSV/Excel upload | In-memory during request; garbage collected after response |
| Journal entries | GL extract upload | In-memory during JE testing; discarded after response |
| AP payment records | AP file upload | In-memory during AP testing; discarded after response |
| Payroll records | Payroll file upload | In-memory during payroll testing; discarded after response |
| Bank statement rows | Bank file upload | In-memory during reconciliation; discarded after response |
| PO/Invoice/Receipt rows | Document uploads | In-memory during three-way match; discarded after response |
| Uploaded file bytes | Any file upload | Streamed, processed, never saved to filesystem |

## How Follow-Up Items Link to Ephemeral Data

Follow-up items are created when a tool run completes with `engagement_id`. They reference ephemeral data **by narrative description only**:

```
Good:  "Round amount entries detected: 47 entries flagged"
Bad:   "Account 1000-Cash: $50,000 round amount on entry JE-2024-0123"
```

The link is maintained through:
- `tool_run_id` — references the ToolRun metadata record (what tool, when, score)
- `description` — human-readable summary of the finding
- `tool_source` — enum identifying which tool generated it

There is **no foreign key or reference to any specific account, amount, or transaction**.

## UI Expectations for Stale References

Since financial data is ephemeral, the engagement workspace cannot re-display detailed tool results from past runs.

| Scenario | UI Behavior |
|----------|-------------|
| Tool run completed, user views engagement | Show: tool name, run date, composite score, status badge |
| User clicks "View Details" on a past tool run | Show: "Re-run this tool to view detailed results. Original data was processed in-memory and is no longer available." |
| Follow-up item references a past run | Show: narrative description + severity + disposition. No drill-down to original data. |
| User exports engagement package | Include: anomaly summary (narratives), workpaper index, manifest. Exclude: original uploaded files. |

## Prohibited Fields in Engagement Tables

Per AccountingExpertAuditor Guardrail 2, the following fields are **never stored** in engagement, tool_run, or follow_up_item tables:

- `account_number`
- `account_name`
- `amount` / `debit` / `credit`
- `transaction_id` / `entry_id`
- `vendor_name` / `employee_name`
- Any personally identifiable information (PII)

This constraint is enforced via pytest assertion in the test suite.
