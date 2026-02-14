'use client'

import { FlaggedEntriesTable, type ColumnDef } from '@/components/shared/testing/FlaggedEntriesTable'
import type { RevenueTestResult, RevenueEntryData } from '@/types/revenueTesting'

interface FlaggedRevenueTableProps {
  results: RevenueTestResult[]
}

const columns: ColumnDef<RevenueEntryData>[] = [
  {
    field: 'account',
    label: 'Account',
    render: (fe) => (
      <span className="font-sans text-sm text-content-primary">
        {fe.entry.account_name || fe.entry.account_number || '\u2014'}
      </span>
    ),
    sortValue: (fe) => fe.entry.account_name || '',
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
    field: 'date',
    label: 'Date',
    render: (fe) => (
      <span className="font-mono text-xs text-content-secondary">
        {fe.entry.date || '\u2014'}
      </span>
    ),
    sortValue: (fe) => fe.entry.date || '',
  },
]

const SEARCH_FIELDS = ['account_name', 'account_number', 'description', 'issue']

export function FlaggedRevenueTable({ results }: FlaggedRevenueTableProps) {
  return (
    <FlaggedEntriesTable
      results={results}
      columns={columns}
      searchFields={SEARCH_FIELDS}
      searchPlaceholder="Search account, description, issue..."
      emptyMessage="No flagged entries found. All tests returned clean results."
      entityLabel="entries"
    />
  )
}
