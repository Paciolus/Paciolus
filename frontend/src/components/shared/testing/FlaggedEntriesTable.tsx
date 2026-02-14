'use client'

import { useState, useMemo, type ReactNode } from 'react'
import { motion } from 'framer-motion'
import type { TestingSeverity } from '@/types/testingShared'

const ITEMS_PER_PAGE = 25

const SEVERITY_ORDER: Record<TestingSeverity, number> = { high: 3, medium: 2, low: 1 }

// ─── Types ───────────────────────────────────────────────────────────────────

export type ColumnDef<TEntry extends Record<string, unknown> = Record<string, unknown>> = {
  field: string
  label: string
  render: (fe: FlatFlaggedEntry<TEntry>) => ReactNode
  sortValue?: (fe: FlatFlaggedEntry<TEntry>) => string | number
}

export type FlatFlaggedEntry<TEntry extends Record<string, unknown> = Record<string, unknown>> = {
  entry: TEntry
  severity: TestingSeverity
  test_name: string
  test_key: string
  issue: string
  confidence: number
}

/** Minimal result shape — compatible with all 7 domain TestResult types. */
export type FlaggedResultInput<TEntry extends Record<string, unknown> = Record<string, unknown>> = {
  test_key: string
  entries_flagged: number
  flagged_entries: Array<{
    entry: TEntry
    severity: TestingSeverity
    test_name: string
    test_key: string
    issue: string
    confidence: number
  }>
  skipped?: boolean
}

export type FlaggedEntriesTableProps<TEntry extends Record<string, unknown> = Record<string, unknown>> = {
  results: FlaggedResultInput<TEntry>[]
  columns: ColumnDef<TEntry>[]
  searchFields: string[]
  searchPlaceholder: string
  emptyMessage: string
  entityLabel: string
  filterSkipped?: boolean
}

// ─── Severity Badge ──────────────────────────────────────────────────────────

const SEVERITY_BADGE_COLORS: Record<TestingSeverity, string> = {
  high: 'bg-clay-50 text-clay-700 border-clay-200',
  medium: 'bg-oatmeal-100 text-oatmeal-700 border-oatmeal-300',
  low: 'bg-oatmeal-50 text-content-secondary border-oatmeal-200',
}

function severityBadge(severity: TestingSeverity) {
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-sans font-medium border ${SEVERITY_BADGE_COLORS[severity]}`}>
      {severity.toUpperCase()}
    </span>
  )
}

// ─── Component ───────────────────────────────────────────────────────────────

export function FlaggedEntriesTable<TEntry extends Record<string, unknown>>({
  results,
  columns,
  searchFields,
  searchPlaceholder,
  emptyMessage,
  entityLabel,
  filterSkipped = false,
}: FlaggedEntriesTableProps<TEntry>) {
  const [searchQuery, setSearchQuery] = useState('')
  const [severityFilter, setSeverityFilter] = useState<TestingSeverity | 'all'>('all')
  const [testFilter, setTestFilter] = useState<string>('all')
  const [sortField, setSortField] = useState<string>('severity')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(0)
  const [expandedRow, setExpandedRow] = useState<number | null>(null)

  // Flatten all flagged entries
  const allFlagged = useMemo(() => {
    const entries: FlatFlaggedEntry<TEntry>[] = []
    for (const tr of results) {
      if (filterSkipped && tr.skipped) continue
      for (const fe of tr.flagged_entries) {
        entries.push(fe as FlatFlaggedEntry<TEntry>)
      }
    }
    return entries
  }, [results, filterSkipped])

  // Available test keys for filter
  const testKeys = useMemo(() => {
    const keys = new Set<string>()
    for (const tr of results) {
      if (filterSkipped && tr.skipped) continue
      if (tr.entries_flagged > 0) keys.add(tr.test_key)
    }
    return Array.from(keys).sort()
  }, [results, filterSkipped])

  // Filter + sort
  const filtered = useMemo(() => {
    let items = [...allFlagged]

    if (severityFilter !== 'all') {
      items = items.filter(fe => fe.severity === severityFilter)
    }
    if (testFilter !== 'all') {
      items = items.filter(fe => fe.test_key === testFilter)
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      items = items.filter(fe => {
        for (const field of searchFields) {
          if (field === 'issue') {
            if (fe.issue.toLowerCase().includes(q)) return true
          } else {
            const val = fe.entry[field]
            if (val != null && String(val).toLowerCase().includes(q)) return true
          }
        }
        return false
      })
    }

    // Build column lookup for sort
    const colMap = new Map<string, ColumnDef<TEntry>>()
    for (const col of columns) {
      colMap.set(col.field, col)
    }

    items.sort((a, b) => {
      let cmp = 0
      if (sortField === 'severity') {
        cmp = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
      } else if (sortField === 'test') {
        cmp = a.test_name.localeCompare(b.test_name)
      } else {
        const col = colMap.get(sortField)
        if (col?.sortValue) {
          const aVal = col.sortValue(a)
          const bVal = col.sortValue(b)
          if (typeof aVal === 'number' && typeof bVal === 'number') {
            cmp = aVal - bVal
          } else {
            cmp = String(aVal).localeCompare(String(bVal))
          }
        }
      }
      return sortDir === 'desc' ? -cmp : cmp
    })

    return items
  }, [allFlagged, severityFilter, testFilter, searchQuery, sortField, sortDir, searchFields, columns])

  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE)
  const paged = filtered.slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE)

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDir('desc')
    }
    setPage(0)
  }

  const sortIndicator = (field: string) =>
    sortField === field ? (sortDir === 'desc' ? ' \u25BC' : ' \u25B2') : ''

  if (allFlagged.length === 0) {
    return (
      <div className="bg-surface-card-secondary border border-theme rounded-xl p-8 text-center">
        <p className="font-sans text-content-secondary">{emptyMessage}</p>
      </div>
    )
  }

  // Build header columns: Test + domain columns + Severity + Issue
  const headerColumns = [
    { field: 'test', label: 'Test' },
    ...columns.map(c => ({ field: c.field, label: c.label })),
    { field: 'severity', label: 'Severity' },
  ]

  return (
    <div className="space-y-4">
      {/* Filter Bar */}
 <div className="flex flex-wrap items-center gap-3 theme-card p-4">
        <input
          type="text"
          placeholder={searchPlaceholder}
          value={searchQuery}
          onChange={e => { setSearchQuery(e.target.value); setPage(0) }}
          className="flex-1 min-w-[200px] bg-surface-input border border-theme rounded-lg px-3 py-2 text-sm font-sans text-content-primary placeholder-content-tertiary focus:outline-none focus:border-sage-500"
        />
        <select
          value={severityFilter}
          onChange={e => { setSeverityFilter(e.target.value as TestingSeverity | 'all'); setPage(0) }}
          className="bg-surface-input border border-theme rounded-lg px-3 py-2 text-sm font-sans text-content-primary focus:outline-none focus:border-sage-500"
        >
          <option value="all">All Severities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          value={testFilter}
          onChange={e => { setTestFilter(e.target.value); setPage(0) }}
          className="bg-surface-input border border-theme rounded-lg px-3 py-2 text-sm font-sans text-content-primary focus:outline-none focus:border-sage-500"
        >
          <option value="all">All Tests</option>
          {testKeys.map(key => (
            <option key={key} value={key}>{key.replace(/_/g, ' ')}</option>
          ))}
        </select>
        <span className="font-sans text-xs text-content-tertiary">
          {filtered.length} of {allFlagged.length} {entityLabel}
        </span>
      </div>

      {/* Table */}
 <div className="overflow-x-auto theme-card">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-theme">
              {headerColumns.map(col => (
                <th
                  key={col.field}
                  onClick={() => handleSort(col.field)}
                  className="px-4 py-3 font-serif text-xs text-content-secondary cursor-pointer hover:text-content-primary select-none"
                >
                  {col.label}{sortIndicator(col.field)}
                </th>
              ))}
              <th className="px-4 py-3 font-serif text-xs text-content-secondary">Issue</th>
            </tr>
          </thead>
          <tbody>
            {paged.map((fe, i) => {
              const globalIdx = page * ITEMS_PER_PAGE + i
              const isExpanded = expandedRow === globalIdx

              return (
                <motion.tr
                  key={`${fe.test_key}-${String(fe.entry['row_number'] ?? fe.entry['row_index'] ?? i)}-${i}`}
                  initial={false}
                  className={`border-b border-theme-divider cursor-pointer transition-colors
                    ${isExpanded ? 'bg-sage-50/30' : 'even:bg-oatmeal-50/50 hover:bg-sage-50/40'}`}
                  onClick={() => setExpandedRow(isExpanded ? null : globalIdx)}
                >
                  <td className="px-4 py-3">
                    <span className="font-sans text-xs text-content-secondary">
                      {fe.test_name}
                    </span>
                  </td>
                  {columns.map(col => (
                    <td key={col.field} className="px-4 py-3">
                      {col.render(fe)}
                    </td>
                  ))}
                  <td className="px-4 py-3">{severityBadge(fe.severity)}</td>
                  <td className="px-4 py-3">
                    <span className="font-sans text-xs text-content-secondary line-clamp-1">
                      {fe.issue}
                    </span>
                  </td>
                </motion.tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1.5 bg-surface-card border border-oatmeal-300 rounded-lg text-content-secondary font-sans text-sm disabled:opacity-30 hover:bg-surface-card-secondary transition-colors"
          >
            Previous
          </button>
          <span className="font-sans text-xs text-content-tertiary">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="px-3 py-1.5 bg-surface-card border border-oatmeal-300 rounded-lg text-content-secondary font-sans text-sm disabled:opacity-30 hover:bg-surface-card-secondary transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
