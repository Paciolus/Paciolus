'use client'

import { FlaggedEntriesTable, type ColumnDef } from '@/components/shared/testing/FlaggedEntriesTable'
import type { APTestResult, APPaymentData } from '@/types/apTesting'

interface FlaggedPaymentTableProps {
  results: APTestResult[]
}

const columns: ColumnDef<APPaymentData>[] = [
  {
    field: 'vendor',
    label: 'Vendor',
    render: (fe) => (
      <>
        <span className="font-sans text-sm text-content-primary">
          {fe.entry.vendor_name || '\u2014'}
        </span>
        {fe.entry.invoice_number && (
          <span className="font-mono text-xs text-content-tertiary ml-2">#{fe.entry.invoice_number}</span>
        )}
      </>
    ),
    sortValue: (fe) => fe.entry.vendor_name || '',
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
        {fe.entry.payment_date || fe.entry.invoice_date || '\u2014'}
      </span>
    ),
    sortValue: (fe) => fe.entry.payment_date || fe.entry.invoice_date || '',
  },
]

const SEARCH_FIELDS = ['vendor_name', 'invoice_number', 'description', 'issue']

export function FlaggedPaymentTable({ results }: FlaggedPaymentTableProps) {
  return (
    <FlaggedEntriesTable
      results={results}
      columns={columns}
      searchFields={SEARCH_FIELDS}
      searchPlaceholder="Search vendor, invoice #, description..."
      emptyMessage="No flagged payments found. All tests returned clean results."
      entityLabel="payments"
    />
  )
}
