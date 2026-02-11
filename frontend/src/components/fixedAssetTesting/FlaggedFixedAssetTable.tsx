'use client'

import { FlaggedEntriesTable, type ColumnDef } from '@/components/shared/testing/FlaggedEntriesTable'
import type { FATestResult } from '@/types/fixedAssetTesting'

interface FlaggedFixedAssetTableProps {
  results: FATestResult[]
}

const columns: ColumnDef[] = [
  {
    field: 'asset',
    label: 'Asset',
    render: (fe) => (
      <span className="font-sans text-sm text-content-primary">
        {fe.entry.asset_id || fe.entry.description || '\u2014'}
      </span>
    ),
    sortValue: (fe) => fe.entry.asset_id || fe.entry.description || '',
  },
  {
    field: 'cost',
    label: 'Cost',
    render: (fe) => (
      <span className="font-mono text-sm text-content-primary text-right block">
        ${fe.entry.cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
      </span>
    ),
    sortValue: (fe) => fe.entry.cost,
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

const SEARCH_FIELDS = ['asset_id', 'description', 'category', 'issue']

export function FlaggedFixedAssetTable({ results }: FlaggedFixedAssetTableProps) {
  return (
    <FlaggedEntriesTable
      results={results}
      columns={columns}
      searchFields={SEARCH_FIELDS}
      searchPlaceholder="Search asset ID, description, issue..."
      emptyMessage="No flagged entries found. All tests returned clean results."
      entityLabel="entries"
    />
  )
}
