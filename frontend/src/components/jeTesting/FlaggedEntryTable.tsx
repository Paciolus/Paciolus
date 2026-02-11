'use client'

import { FlaggedEntriesTable, type ColumnDef } from '@/components/shared/testing/FlaggedEntriesTable'
import type { JETestResult } from '@/types/jeTesting'

interface FlaggedEntryTableProps {
  results: JETestResult[]
}

const columns: ColumnDef[] = [
  {
    field: 'account',
    label: 'Account',
    render: (fe) => (
      <>
        <span className="font-sans text-sm text-content-primary">
          {fe.entry.account || '\u2014'}
        </span>
        {fe.entry.entry_id && (
          <span className="font-mono text-xs text-content-tertiary ml-2">#{fe.entry.entry_id}</span>
        )}
      </>
    ),
    sortValue: (fe) => fe.entry.account || '',
  },
  {
    field: 'date',
    label: 'Date',
    render: (fe) => (
      <span className="font-mono text-xs text-content-tertiary">
        {fe.entry.posting_date || fe.entry.entry_date || '\u2014'}
      </span>
    ),
    sortValue: (fe) => fe.entry.posting_date || fe.entry.entry_date || '',
  },
  {
    field: 'amount',
    label: 'Amount',
    render: (fe) => {
      const amt = fe.entry.debit || fe.entry.credit || 0
      return (
        <span className="font-mono text-sm text-content-primary text-right block">
          ${Math.abs(amt).toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </span>
      )
    },
    sortValue: (fe) => Math.abs(fe.entry.debit || fe.entry.credit || 0),
  },
]

const SEARCH_FIELDS = ['account', 'description', 'entry_id', 'issue']

export function FlaggedEntryTable({ results }: FlaggedEntryTableProps) {
  return (
    <FlaggedEntriesTable
      results={results}
      columns={columns}
      searchFields={SEARCH_FIELDS}
      searchPlaceholder="Search account, description, entry ID..."
      emptyMessage="No flagged entries found. All tests returned clean results."
      entityLabel="entries"
    />
  )
}
