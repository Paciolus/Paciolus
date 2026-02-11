'use client'

import { FlaggedEntriesTable, type ColumnDef } from '@/components/shared/testing/FlaggedEntriesTable'
import type { PayrollTestResult } from '@/types/payrollTesting'

interface FlaggedEmployeeTableProps {
  results: PayrollTestResult[]
}

const columns: ColumnDef[] = [
  {
    field: 'employee',
    label: 'Employee',
    render: (fe) => (
      <>
        <span className="font-sans text-sm text-content-primary">
          {fe.entry.employee_name || '\u2014'}
        </span>
        {fe.entry.department && (
          <span className="font-sans text-xs text-content-tertiary ml-2">{fe.entry.department}</span>
        )}
      </>
    ),
    sortValue: (fe) => fe.entry.employee_name || '',
  },
  {
    field: 'amount',
    label: 'Amount',
    render: (fe) => (
      <span className="font-mono text-sm text-content-primary text-right block">
        ${Math.abs(fe.entry.gross_pay).toLocaleString(undefined, { minimumFractionDigits: 2 })}
      </span>
    ),
    sortValue: (fe) => Math.abs(fe.entry.gross_pay),
  },
  {
    field: 'date',
    label: 'Pay Date',
    render: (fe) => (
      <span className="font-mono text-xs text-content-secondary">
        {fe.entry.pay_date || '\u2014'}
      </span>
    ),
    sortValue: (fe) => fe.entry.pay_date || '',
  },
]

const SEARCH_FIELDS = ['employee_name', 'employee_id', 'department', 'issue']

export function FlaggedEmployeeTable({ results }: FlaggedEmployeeTableProps) {
  return (
    <FlaggedEntriesTable
      results={results}
      columns={columns}
      searchFields={SEARCH_FIELDS}
      searchPlaceholder="Search employee, ID, department..."
      emptyMessage="No flagged employees found. All tests returned clean results."
      entityLabel="entries"
    />
  )
}
