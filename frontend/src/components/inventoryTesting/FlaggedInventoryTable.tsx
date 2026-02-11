'use client'

import { FlaggedEntriesTable, type ColumnDef } from '@/components/shared/testing/FlaggedEntriesTable'
import type { InvTestResult } from '@/types/inventoryTesting'

interface FlaggedInventoryTableProps {
  results: InvTestResult[]
}

const columns: ColumnDef[] = [
  {
    field: 'item',
    label: 'Item',
    render: (fe) => (
      <span className="font-sans text-sm text-content-primary">
        {fe.entry.item_id || fe.entry.description || '\u2014'}
      </span>
    ),
    sortValue: (fe) => fe.entry.item_id || fe.entry.description || '',
  },
  {
    field: 'quantity',
    label: 'Qty',
    render: (fe) => (
      <span className="font-mono text-sm text-content-primary text-right block">
        {fe.entry.quantity.toLocaleString()}
      </span>
    ),
    sortValue: (fe) => fe.entry.quantity,
  },
  {
    field: 'value',
    label: 'Value',
    render: (fe) => (
      <span className="font-mono text-sm text-content-primary text-right block">
        ${fe.entry.extended_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
      </span>
    ),
    sortValue: (fe) => fe.entry.extended_value,
  },
  {
    field: 'category',
    label: 'Category',
    render: (fe) => (
      <span className="font-sans text-xs text-content-secondary">
        {fe.entry.category || '\u2014'}
      </span>
    ),
    sortValue: (fe) => fe.entry.category || '',
  },
]

const SEARCH_FIELDS = ['item_id', 'description', 'category', 'issue']

export function FlaggedInventoryTable({ results }: FlaggedInventoryTableProps) {
  return (
    <FlaggedEntriesTable
      results={results}
      columns={columns}
      searchFields={SEARCH_FIELDS}
      searchPlaceholder="Search item ID, description, issue..."
      emptyMessage="No flagged entries found. All tests returned clean results."
      entityLabel="entries"
    />
  )
}
