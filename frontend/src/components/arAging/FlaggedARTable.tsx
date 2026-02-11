'use client'

import { FlaggedEntriesTable, type ColumnDef } from '@/components/shared/testing/FlaggedEntriesTable'
import type { ARTestResult } from '@/types/arAging'

interface FlaggedARTableProps {
  results: ARTestResult[]
}

const columns: ColumnDef[] = [
  {
    field: 'customer',
    label: 'Customer / Account',
    render: (fe) => (
      <span className="font-sans text-sm text-content-primary">
        {fe.entry.customer_name || fe.entry.account_name || '\u2014'}
      </span>
    ),
    sortValue: (fe) => fe.entry.customer_name || fe.entry.account_name || '',
  },
  {
    field: 'amount',
    label: 'Amount',
    render: (fe) => (
      <span className="font-mono text-sm text-content-primary text-right block">
        ${Math.abs(fe.entry.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
      </span>
    ),
    sortValue: (fe) => Math.abs(fe.entry.amount),
  },
  {
    field: 'aging',
    label: 'Days',
    render: (fe) => (
      <span className="font-mono text-xs text-content-secondary">
        {fe.entry.aging_days != null ? `${fe.entry.aging_days}d` : '\u2014'}
      </span>
    ),
    sortValue: (fe) => fe.entry.aging_days ?? 0,
  },
]

const SEARCH_FIELDS = ['customer_name', 'account_name', 'invoice_number', 'issue']

export function FlaggedARTable({ results }: FlaggedARTableProps) {
  return (
    <FlaggedEntriesTable
      results={results}
      columns={columns}
      searchFields={SEARCH_FIELDS}
      searchPlaceholder="Search customer, account, invoice..."
      emptyMessage="No flagged items found. All tests returned clean results."
      entityLabel="items"
      filterSkipped
    />
  )
}
