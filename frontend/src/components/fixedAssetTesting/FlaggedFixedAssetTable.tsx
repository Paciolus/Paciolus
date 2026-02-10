'use client'

import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import type { FATestResult, FlaggedFixedAssetEntry, FASeverity } from '@/types/fixedAssetTesting'

const ITEMS_PER_PAGE = 25

interface FlaggedFixedAssetTableProps {
  results: FATestResult[]
}

type SortField = 'asset' | 'cost' | 'category' | 'severity' | 'test'
type SortDir = 'asc' | 'desc'

const SEVERITY_ORDER: Record<FASeverity, number> = { high: 3, medium: 2, low: 1 }

function severityBadge(severity: FASeverity) {
  const colors: Record<FASeverity, string> = {
    high: 'bg-clay-50 text-clay-700 border-clay-200',
    medium: 'bg-oatmeal-100 text-oatmeal-700 border-oatmeal-300',
    low: 'bg-oatmeal-50 text-content-secondary border-oatmeal-200',
  }
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-sans font-medium border ${colors[severity]}`}>
      {severity.toUpperCase()}
    </span>
  )
}

export function FlaggedFixedAssetTable({ results }: FlaggedFixedAssetTableProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [severityFilter, setSeverityFilter] = useState<FASeverity | 'all'>('all')
  const [testFilter, setTestFilter] = useState<string>('all')
  const [sortField, setSortField] = useState<SortField>('severity')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [page, setPage] = useState(0)
  const [expandedRow, setExpandedRow] = useState<number | null>(null)

  const allFlagged = useMemo(() => {
    const entries: FlaggedFixedAssetEntry[] = []
    for (const tr of results) {
      for (const fe of tr.flagged_entries) {
        entries.push(fe)
      }
    }
    return entries
  }, [results])

  const testKeys = useMemo(() => {
    const keys = new Set<string>()
    for (const tr of results) {
      if (tr.entries_flagged > 0) keys.add(tr.test_key)
    }
    return Array.from(keys).sort()
  }, [results])

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
      items = items.filter(fe =>
        (fe.entry.asset_id || '').toLowerCase().includes(q) ||
        (fe.entry.description || '').toLowerCase().includes(q) ||
        (fe.entry.category || '').toLowerCase().includes(q) ||
        fe.issue.toLowerCase().includes(q)
      )
    }

    items.sort((a, b) => {
      let cmp = 0
      switch (sortField) {
        case 'severity':
          cmp = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
          break
        case 'cost':
          cmp = a.entry.cost - b.entry.cost
          break
        case 'test':
          cmp = a.test_name.localeCompare(b.test_name)
          break
        case 'asset':
          cmp = (a.entry.asset_id || a.entry.description || '').localeCompare(b.entry.asset_id || b.entry.description || '')
          break
        case 'category':
          cmp = (a.entry.category || '').localeCompare(b.entry.category || '')
          break
      }
      return sortDir === 'desc' ? -cmp : cmp
    })

    return items
  }, [allFlagged, severityFilter, testFilter, searchQuery, sortField, sortDir])

  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE)
  const paged = filtered.slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE)

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDir('desc')
    }
    setPage(0)
  }

  const sortIndicator = (field: SortField) =>
    sortField === field ? (sortDir === 'desc' ? ' \u25BC' : ' \u25B2') : ''

  if (allFlagged.length === 0) {
    return (
      <div className="bg-surface-card-secondary border border-theme rounded-xl p-8 text-center">
        <p className="font-sans text-content-secondary">No flagged entries found. All tests returned clean results.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-surface-card-secondary border border-theme rounded-xl p-4">
        <input
          type="text"
          placeholder="Search asset ID, description, issue..."
          value={searchQuery}
          onChange={e => { setSearchQuery(e.target.value); setPage(0) }}
          className="flex-1 min-w-[200px] bg-surface-input border border-theme rounded-lg px-3 py-2 text-sm font-sans text-content-primary placeholder-content-tertiary focus:outline-none focus:border-sage-500"
        />
        <select
          value={severityFilter}
          onChange={e => { setSeverityFilter(e.target.value as FASeverity | 'all'); setPage(0) }}
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
          {filtered.length} of {allFlagged.length} entries
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto bg-surface-card-secondary border border-theme rounded-xl">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-theme">
              {[
                { field: 'test' as SortField, label: 'Test' },
                { field: 'asset' as SortField, label: 'Asset' },
                { field: 'cost' as SortField, label: 'Cost' },
                { field: 'category' as SortField, label: 'Category' },
                { field: 'severity' as SortField, label: 'Severity' },
              ].map(col => (
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
                  key={`${fe.test_key}-${fe.entry.row_number}-${i}`}
                  initial={false}
                  className={`border-b border-theme-divider cursor-pointer transition-colors
                    ${isExpanded ? 'bg-surface-card-secondary' : 'hover:bg-surface-card-secondary'}`}
                  onClick={() => setExpandedRow(isExpanded ? null : globalIdx)}
                >
                  <td className="px-4 py-3">
                    <span className="font-sans text-xs text-content-secondary">
                      {fe.test_name}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-sans text-sm text-content-primary">
                      {fe.entry.asset_id || fe.entry.description || '\u2014'}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-sm text-content-primary text-right">
                    ${fe.entry.cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-3 font-sans text-xs text-content-secondary">
                    {fe.entry.category || '\u2014'}
                  </td>
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
